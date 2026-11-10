#!/usr/bin/env python3
# Copyright 2026 GNX. Licensed under the Apache License, Version 2.0;
# see the LICENSE file in the Greenhorn repository,
# https://github.com/globalnetx/greenhorn.
"""
Build a company plugin from a company folder.

Runs the checker (strict) and the secret scanner first and refuses to
build on any finding that would ship. Then assembles the plugin by
allowlist: the company's own skills (`skills/<prefix>-*/`, each with its
SKILL.md and references/) and a manifest written here. Nothing else is
read into the plugin: not the interview profile, the source documents,
the brand sources, the house rules, the README, the settings, earlier
builds, hidden files, or any skill marked as Greenhorn's own
(`metadata.greenhorn-tool: true`). The result is checked against the
upload limits and zipped to dist/<name>-vX.Y.Z.zip, with the version
raised from the last build recorded in harness.yaml.

Usage (from wherever this file sits; in the Greenhorn repository that is
skills/greenhorn/scripts/):
    python3 build_plugin.py                   # build the current folder into dist/
    python3 build_plugin.py path/to/folder    # build another folder
    python3 build_plugin.py --dry-run         # say what would go in and stay out; write nothing
    python3 build_plugin.py --bump minor      # raise the minor number (patch is the default)
    python3 build_plugin.py --set-version 1.0.0
    python3 build_plugin.py --json            # machine-readable output
    python3 build_plugin.py --self-test       # prove the refusals on a throwaway folder

Settings read from harness.yaml (the skill's schema reference, "The
settings file"): `plugin-author` (required), `plugin-name` (default: the
skills' shared prefix), `plugin-description` (default: the README's first
paragraph), `plugin-license` (optional), and `build-state`, which this
script writes after every build.

Exit codes: 0 built (or dry run clean), 1 refused with reasons printed,
2 the folder or the arguments are unusable.

Python 3.9 or newer, standard library only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_harness as ch  # noqa: E402  (path set up just above)
import scan_secrets as ss  # noqa: E402

# --- The upload constraints, from the documentation --------------------------
#
# Each constant names where it was read and when, so a reader can re-check it.
# The skill's references/upload-facts.md carries the same facts with their
# wording; keep the two in step.

# claude.com/docs/plugins/platform-support, "Marketplace and plugin limits",
# read 2026-11-09: "Each plugin can contain up to 5,000 files and 200 MB".
MAX_FILES = 5000
MAX_BYTES = 200 * 1024 * 1024
# claude.com/docs/plugins/org-sync, read 2026-11-09: claude.ai rejects a
# plugin with a top-level bin/ directory, uploaded or synced.
FORBIDDEN_TOP_LEVEL = ("bin",)
# code.claude.com/docs/en/plugins-reference, read 2026-11-09: reserved
# plugin names.
RESERVED_PLUGIN_NAMES = ("claude", "anthropic", "anthropics", "claude-code", "claude-mods")
RESERVED_PLUGIN_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
# code.claude.com/docs/en/skills, read 2026-11-09: a skill folder must not
# be called "synced" in any capitalisation; "anthropic-skills" is reserved.
RESERVED_SKILL_NAMES = ("synced", "anthropic-skills")
# The manifest lives at .claude-plugin/plugin.json at the zip root or
# inside a single top-level folder (claude.com/docs/plugins/build, read
# 2026-11-09). This script uses one top-level folder named after the
# plugin, so the zip unpacks into one folder, like Greenhorn's own.
MANIFEST_DIR = ".claude-plugin"
MANIFEST_NAME = "plugin.json"

# Where the always-on block goes. support.claude.com, "Set organization
# instructions" (article 14546867), last updated 2026-08-31, read
# 2026-11-09.
ORG_INSTRUCTIONS_WHERE = "Organization settings > Organization and access > Organization instructions"
ORG_INSTRUCTIONS_WHO = "an Owner or Primary Owner (Team or Enterprise plan)"
ORG_INSTRUCTIONS_CAP = 3000
ORG_INSTRUCTIONS_SOURCE = 'support.claude.com, "Set organization instructions", read 2026-11-09'

FIRST_VERSION = "0.1.0"
STATE_KEY = "build-state"
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
STATE_COMMENT = "# Written by Greenhorn's build script after every build; leave it alone."

# What never travels, with the plain reason shown to the admin. Only the
# entries that exist in the folder are listed.
NEVER_SHIPS = [
    ("harness-profile.md", "the interview as answered; never leaves this computer"),
    ("sources/", "the documents handed over during setup; never leave this computer"),
    ("brand-sources/", "logo files and screenshots as handed over; never leave this computer"),
    ("HOUSE-RULES.md", "how to work in the folder; the plugin does not need it"),
    ("harness.yaml", "settings for the checks and this build"),
    ("README.md", "the skill index and the always-on block; the block is pasted, not uploaded"),
    ("dist/", "earlier builds"),
    ("local/", "local notes"),
]


# --- Result ------------------------------------------------------------------


@dataclass
class Build:
    root: Path
    dry_run: bool
    ok: bool = True
    refusals: list = field(default_factory=list)   # (path or None, message)
    warnings: list = field(default_factory=list)   # (path or None, message)
    checker_findings: list = field(default_factory=list)
    scanner_findings: list = field(default_factory=list)
    went_in: list = field(default_factory=list)    # (skill name, [relative files])
    left_out: list = field(default_factory=list)   # (path, reason)
    manifest: dict = field(default_factory=dict)
    previous_version: Optional[str] = None
    version: Optional[str] = None
    file_count: int = 0
    byte_count: int = 0
    zip_path: Optional[Path] = None
    block_text: Optional[str] = None
    block_chars: Optional[int] = None
    block_cap: int = ORG_INSTRUCTIONS_CAP
    block_stamp: Optional[str] = None
    block_changed: Optional[bool] = None

    def refuse(self, path, message: str) -> None:
        self.ok = False
        self.refusals.append((self._rel(path), message))

    def warn(self, path, message: str) -> None:
        self.warnings.append((self._rel(path), message))

    def _rel(self, path) -> Optional[str]:
        if path is None:
            return None
        try:
            return str(Path(path).resolve().relative_to(self.root.resolve()))
        except ValueError:
            return str(path)


# --- Settings ----------------------------------------------------------------


def _read_settings(root: Path, build: Build) -> dict:
    """The plugin-* keys and build-state from harness.yaml, read with the
    checker's own parser so the two never disagree on the file's shape."""
    out = {"author": None, "name": None, "description": None, "license": None, "state": {}}
    path = root / ch.SETTINGS_FILE
    if not path.is_file():
        build.refuse(path, f"there is no {ch.SETTINGS_FILE}; the build needs one with at least `plugin-author: \"<the company's name>\"` in it")
        return out
    data, _, err = ch.parse_simple_yaml(path.read_text(encoding="utf-8-sig"), first_line=1)
    if err:
        build.refuse(path, f"line {err[0]}: {err[1]}")
        return out
    for key, target in (("plugin-author", "author"), ("plugin-name", "name"), ("plugin-description", "description"), ("plugin-license", "license")):
        value = data.get(key)
        if value in (None, ""):
            continue
        if not isinstance(value, str):
            build.refuse(path, f"`{key}` must be one line of text")
            continue
        out[target] = value.strip()
    if out["author"] is None:
        build.refuse(path, "no `plugin-author` set. The manifest names who made the plugin, and that is not something to guess: add `plugin-author: \"<the company's name>\"` to harness.yaml and build again")
    state = data.get(STATE_KEY)
    if isinstance(state, dict):
        out["state"] = {k: v for k, v in state.items() if isinstance(v, str)}
    elif state not in (None, ""):
        build.refuse(path, f"`{STATE_KEY}` must be an indented block of `key: value` pairs, as the build writes it")
    return out


def _write_build_state(path: Path, state: dict) -> None:
    """Replace or append the build-state block in harness.yaml, touching
    nothing else in the file (comments and order stay as the admin left
    them)."""
    text = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    lines = text.splitlines()
    block = [f"{STATE_KEY}:"] + [f"  {k}: {v}" for k, v in state.items()]
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^{re.escape(STATE_KEY)}\s*:\s*(#.*)?$", line):
            start = i
            break
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([STATE_COMMENT] + block)
    else:
        end = start + 1
        while end < len(lines) and (not lines[end].strip() or lines[end].startswith((" ", "\t")) or lines[end].lstrip().startswith("#") and lines[end].startswith(" ")):
            end += 1
        # Keep a trailing blank line out of the replaced region.
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        lines[start:end] = block
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- Version -----------------------------------------------------------------


def _parse_version(value: str) -> Optional[tuple]:
    m = VERSION_RE.match(value.strip()) if isinstance(value, str) else None
    return tuple(int(g) for g in m.groups()) if m else None


def _next_version(previous: Optional[str], bump: str, explicit: Optional[str], build: Build, settings_path: Path) -> Optional[str]:
    prev = _parse_version(previous) if previous else None
    if previous and prev is None:
        build.refuse(settings_path, f"`{STATE_KEY}.version` is '{previous}', not a version like 1.2.3; fix it or remove the build-state block")
        return None
    if explicit is not None:
        new = _parse_version(explicit)
        if new is None:
            build.refuse(None, f"--set-version '{explicit}' is not a version like 1.2.3")
            return None
        if prev is not None and new <= prev:
            build.refuse(settings_path, f"--set-version {explicit} is not higher than the last build, {previous}; an organisation only notices an update when the version rises")
            return None
        return explicit
    if prev is None:
        return FIRST_VERSION
    major, minor, patch = prev
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


# --- The checks ----------------------------------------------------------------


def _run_checks(root: Path, build: Build) -> None:
    report = ch.check_folder(root)
    for f in report.findings:
        build.checker_findings.append(f)
    if report.errors or report.warnings:
        build.ok = False
    scan = ss.scan([p for p in ss._walk(root) if "dist" not in p.relative_to(root).parts[:1]])
    for f in scan.findings:
        rel = Path(f.path)
        try:
            rel = Path(f.path).resolve().relative_to(root.resolve())
        except (ValueError, OSError):
            pass
        ships = rel.parts[:1] == ("skills",) or rel.as_posix() == "README.md"
        build.scanner_findings.append((rel.as_posix(), f.line, f.rule, f.snippet, ships))
        if ships:
            build.ok = False
        else:
            build.warn(root / rel, f"line {f.line}: looks like a credential ({f.rule}). It does not ship, but the folder is backed up, so remove it, and change it if it is real")


# --- The allowlist -------------------------------------------------------------


def _is_hidden_or_cache(path: Path) -> bool:
    return any(part.startswith(".") or part == "__pycache__" for part in path.parts)


def _shared_prefix(names: list) -> Optional[str]:
    """`acme` when every skill folder is `acme-something`; None otherwise."""
    firsts = set()
    for n in names:
        if "-" not in n:
            return None
        firsts.add(n.split("-", 1)[0])
    return firsts.pop() if len(firsts) == 1 else None


def _collect_skills(root: Path, build: Build, skills: list, plugin_name_setting: Optional[str]) -> Optional[str]:
    """Decide which skills go in and which files of each. Returns the
    prefix (also the default plugin name)."""
    skills_root = root / "skills"
    if not skills_root.is_dir():
        build.refuse(root, "there is no skills/ folder, so there is nothing to build; giddy-up writes the first skills")
        return None
    if (skills_root / "greenhorn").is_dir():
        build.refuse(skills_root / "greenhorn", "this folder holds Greenhorn's own skill; it is not a company folder, and nothing of Greenhorn goes into a company plugin")
        return None

    # A symbolic link anywhere under skills/ could point at the profile, at
    # sources/, or outside the folder, and every copy would follow it. None
    # are allowed; the plugin carries only files that really sit in skills/.
    links = [p for p in [skills_root] + sorted(skills_root.rglob("*")) if p.is_symlink()]
    for link in links:
        build.refuse(link, "this is a symbolic link; the build copies only real files under skills/, because a link can point at the profile, the sources, or anything outside the folder. Replace it with a copy of the file, or remove it")
    if links:
        return None

    for s in skills:
        marker = s.metadata.get(ch.GREENHORN_TOOL_KEY)
        if marker not in (None, "", "false"):
            build.refuse(s.path, f"this skill carries `metadata.{ch.GREENHORN_TOOL_KEY}: {marker}`, which marks Greenhorn's own skill. It never goes into a company plugin; remove the folder from skills/")

    folders = [p for p in sorted(skills_root.iterdir()) if p.is_dir() and not p.name.startswith(".")]
    if not folders:
        build.refuse(skills_root, "the skills folder is empty; there is nothing to build yet")
        return None
    names = [p.name for p in folders]
    prefix = _shared_prefix(names)
    if prefix is None:
        if plugin_name_setting:
            prefix = plugin_name_setting
        else:
            build.refuse(skills_root, "the skill folders do not share one prefix (" + ", ".join(names) + "). Every company skill is named `<prefix>-<topic>`, like acme-voice; rename the odd one out, or move it out of skills/")
            return None
    for p in folders:
        if not p.name.startswith(prefix + "-"):
            build.refuse(p, f"'{p.name}' does not start with the company prefix '{prefix}-', so it is not one of the company's skills; rename it or move it out of skills/")
        if p.name.lower() in RESERVED_SKILL_NAMES or p.name.lower().startswith("anthropic-skills:"):
            build.refuse(p, f"'{p.name}' is a reserved skill folder name; pick another")

    by_folder = {s.folder.resolve(): s for s in skills}
    for p in folders:
        if not p.name.startswith(prefix + "-") or (p.resolve() in by_folder and by_folder[p.resolve()].is_greenhorn_tool):
            continue
        files = []
        skill_md = p / "SKILL.md"
        if skill_md.is_file():
            files.append("SKILL.md")
        refs = p / "references"
        if refs.is_dir():
            for f in sorted(refs.rglob("*")):
                rel = f.relative_to(p)
                if not f.is_file() or _is_hidden_or_cache(rel):
                    continue
                if f.name.lower() == "skill.md":
                    build.refuse(f, "a SKILL.md under references/ is a stray copy of a skill, not a reference file; move it to its own folder under skills/ or remove it")
                    continue
                files.append(rel.as_posix())
        for entry in sorted(p.iterdir()):
            if entry.name in ("SKILL.md", "references") or entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            build.left_out.append((f"skills/{p.name}/{entry.name}" + ("/" if entry.is_dir() else ""),
                                   "only SKILL.md and references/ travel; move it under references/ and name it in SKILL.md, or remove it"))
        build.went_in.append((p.name, files))
    return prefix


DESCRIPTION_LONG = 300


def _first_paragraph(readme: Path) -> Optional[str]:
    """The README's first paragraph that is prose: not a heading, not an
    HTML comment, not an image, badge, table, list, quote, or fenced
    block, and never anything from inside the always-on block."""
    if not readme.is_file():
        return None
    text = readme.read_text(encoding="utf-8-sig")
    if ch.ORG_BLOCK_START in text and ch.ORG_BLOCK_END in text:
        head, rest = text.split(ch.ORG_BLOCK_START, 1)
        text = head + rest.split(ch.ORG_BLOCK_END, 1)[1]
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    for para in re.split(r"\n\s*\n", text):
        p = para.strip()
        if not p or p.startswith(("#", "<", "!", "[", "|", "`", "- ", "* ", ">", "---")):
            continue
        return re.sub(r"\s+", " ", p)
    return None


def _versions_in_dist(root: Path, name: str) -> list:
    """Versions of earlier zips for this plugin found in dist/, so a lost
    build-state cannot make the version fall back."""
    found = []
    for z in (root / "dist").glob(f"{name}-v*.zip"):
        v = _parse_version(z.name[len(name) + 2:-4])
        if v is not None:
            found.append(v)
    return found


def _check_plugin_name(name: str, build: Build, settings_path: Path) -> None:
    if not ch.NAME_PATTERN.match(name) or not (ch.NAME_MIN <= len(name) <= ch.NAME_MAX):
        build.refuse(settings_path, f"the plugin name '{name}' must be lowercase letters, digits and hyphens, {ch.NAME_MIN} to {ch.NAME_MAX} characters; set `plugin-name` in harness.yaml")
    if name in RESERVED_PLUGIN_NAMES or name.startswith(RESERVED_PLUGIN_PREFIXES):
        build.refuse(settings_path, f"the plugin name '{name}' is reserved; set `plugin-name` in harness.yaml to something else")


# --- The block -----------------------------------------------------------------


def _read_block(root: Path, build: Build, cap: int, previous_stamp: Optional[str]) -> None:
    readme = root / "README.md"
    build.block_cap = cap
    if not readme.is_file():
        build.warn(readme, "there is no README.md, so there is no always-on block to paste; reins writes it")
        return
    text = readme.read_text(encoding="utf-8-sig")
    if ch.ORG_BLOCK_START not in text or ch.ORG_BLOCK_END not in text:
        build.warn(readme, "README.md has no always-on block between the markers; reins writes it")
        return
    region = text.split(ch.ORG_BLOCK_START, 1)[1].split(ch.ORG_BLOCK_END, 1)[0]
    fence = ch.ORG_BLOCK_FENCE_RE.search(region)
    if not fence:
        return
    build.block_text = fence.group(1)
    build.block_chars = len(fence.group(1))
    stamp = ch.ORG_HASH_RE.search(region)
    build.block_stamp = stamp.group(1) if stamp else None
    build.block_changed = previous_stamp is None or build.block_stamp != previous_stamp


# --- Assembling ----------------------------------------------------------------


def _stage(root: Path, build: Build, staging: Path, name: str) -> None:
    top = staging / name
    (top / MANIFEST_DIR).mkdir(parents=True)
    (top / MANIFEST_DIR / MANIFEST_NAME).write_text(json.dumps(build.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for skill_name, files in build.went_in:
        for rel in files:
            src = root / "skills" / skill_name / rel
            dst = top / "skills" / skill_name / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    count = 0
    size = 0
    manifests = 0
    for f in sorted(top.rglob("*")):
        if f.is_file():
            count += 1
            size += f.stat().st_size
            if f.name == MANIFEST_NAME and f.parent.name == MANIFEST_DIR:
                manifests += 1
    build.file_count = count
    build.byte_count = size
    if count > MAX_FILES:
        build.refuse(root, f"the plugin would hold {count:,} files; the upload accepts at most {MAX_FILES:,}")
    if size > MAX_BYTES:
        build.refuse(root, f"the plugin would be {size / (1024 * 1024):,.0f} MB unpacked; the upload accepts at most 200 MB")
    if manifests != 1:
        build.refuse(root, f"the plugin would hold {manifests} manifests; it must hold exactly one at {MANIFEST_DIR}/{MANIFEST_NAME}")
    for folder in FORBIDDEN_TOP_LEVEL:
        if (top / folder).exists():
            build.refuse(root, f"the plugin would hold a top-level {folder}/ folder, which the upload refuses")


def _zip(staging: Path, name: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".zip.part")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in sorted((staging / name).rglob("*")):
            if f.is_file():
                zf.write(f, arcname=f.relative_to(staging).as_posix())
    os.replace(tmp, target)


# --- The build -----------------------------------------------------------------


def build_folder(root: Path, dry_run: bool = False, bump: str = "patch", set_version: Optional[str] = None) -> Build:
    build = Build(root=root, dry_run=dry_run)
    settings_path = root / ch.SETTINGS_FILE

    if (root / FORBIDDEN_TOP_LEVEL[0]).is_dir():
        build.refuse(root / "bin", "a top-level bin/ folder makes the upload refuse the whole plugin; move its files elsewhere")

    _run_checks(root, build)
    settings = _read_settings(root, build)
    skills = ch.load_skills(root)
    prefix = _collect_skills(root, build, skills, settings["name"])
    checker_settings = ch.load_settings(root, None)

    name = settings["name"] or prefix
    if name:
        _check_plugin_name(name, build, settings_path)

    build.previous_version = settings["state"].get("version") or None
    build.version = _next_version(build.previous_version, bump, set_version, build, settings_path)
    if name and build.version:
        newest = max(_versions_in_dist(root, name), default=None)
        if newest is not None and _parse_version(build.version) <= newest:
            shown = ".".join(str(n) for n in newest)
            build.refuse(root / "dist", f"dist/ already holds {name}-v{shown}.zip, and the next version would be {build.version}, which is not higher. The build state in harness.yaml seems to have been lost; build again with `--set-version` above {shown}")

    description = settings["description"] or _first_paragraph(root / "README.md")
    if not description:
        build.refuse(root / "README.md", "no description for the plugin: README.md has no opening paragraph to take it from. Set `plugin-description` in harness.yaml, or let reins write the README")
    elif len(description) > DESCRIPTION_LONG:
        build.warn(settings_path if settings["description"] else root / "README.md", f"the plugin's description is {len(description):,} characters; the organisation's plugin list shows it as a blurb, so a line or two reads better. Set `plugin-description` in harness.yaml to shorten it")

    _read_block(root, build, checker_settings["org_block_max"], settings["state"].get("org-block-stamp") or None)
    if build.block_chars is not None and build.block_chars > build.block_cap:
        build.refuse(root / "README.md", f"the always-on block is {build.block_chars:,} characters; the field holds {build.block_cap:,}")

    for entry, reason in NEVER_SHIPS:
        if (root / entry.rstrip("/")).exists():
            build.left_out.append((entry, reason))
    known = {entry.rstrip("/") for entry, _ in NEVER_SHIPS} | {"skills"}
    for entry in sorted(root.iterdir()):
        if entry.name in known or entry.name.startswith(".") or entry.name == "__pycache__":
            continue
        build.left_out.append((entry.name + ("/" if entry.is_dir() else ""), "not part of a company plugin; only skills/ travels"))

    if not build.ok or not name or not build.version:
        build.ok = False
        return build

    build.manifest = {
        "name": name,
        "version": build.version,
        "description": description,
        "author": {"name": settings["author"]},
    }
    if settings["license"]:
        build.manifest["license"] = settings["license"]

    zip_name = f"{name}-v{build.version}.zip"
    build.zip_path = root / "dist" / zip_name
    with tempfile.TemporaryDirectory(prefix="greenhorn-build-") as tmp:
        staging = Path(tmp)
        _stage(root, build, staging, name)
        if not build.ok:
            return build
        if not dry_run:
            if build.zip_path.exists():
                build.warn(build.zip_path, "a zip with this version already existed and was replaced")
            _zip(staging, name, build.zip_path)
            _write_build_state(settings_path, {
                "version": build.version,
                "built": datetime.date.today().isoformat(),
                "org-block-stamp": build.block_stamp or "none",
            })
    return build


# --- Output ----------------------------------------------------------------------


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} bytes"
    if n < 1024 * 1024:
        return f"{n / 1024:,.0f} KB"
    return f"{n / (1024 * 1024):,.1f} MB"


def render_text(build: Build) -> None:
    out = sys.stdout
    err = sys.stderr
    for f in build.checker_findings:
        label = "ERROR" if f.level == "error" else "WARN "
        where = f"{f.path}:{f.line}" if f.line else f.path
        print(f"{label}  {where}: {f.message}", file=err)
    for path, line, rule, snippet, ships in build.scanner_findings:
        if ships:
            print(f"SECRET  {path}:{line}: {rule}: {snippet}", file=err)
    for path, message in build.refusals:
        print(f"REFUSED  {path + ': ' if path else ''}{message}", file=err)
    for path, message in build.warnings:
        print(f"NOTE  {path + ': ' if path else ''}{message}", file=out)

    if not build.ok:
        print(file=err)
        print("Nothing was built. Fix the items above and build again; the checks are the same ones round-up runs.", file=err)
        return

    verb = "Would go in" if build.dry_run else "Went in"
    print(f"{verb} ({len(build.went_in)} skills):")
    for skill_name, files in build.went_in:
        extra = [f for f in files if f != "SKILL.md"]
        print(f"  skills/{skill_name}/  SKILL.md" + (f" and {len(extra)} file{'s' if len(extra) != 1 else ''} under references/" if extra else ""))
    m = build.manifest
    print(f"  {MANIFEST_DIR}/{MANIFEST_NAME}  name {m['name']}, version {m['version']}, by {m['author']['name']}")
    if build.left_out:
        print()
        print("Left out, on purpose:")
        width = max(len(p) for p, _ in build.left_out)
        for path, reason in build.left_out:
            print(f"  {path.ljust(width)}  {reason}")
    print()
    if build.dry_run:
        print(f"Dry run: would write {build.zip_path} ({build.file_count} files, {_fmt_size(build.byte_count)} unpacked). Nothing was written.")
    else:
        print(f"Zip: {build.zip_path} ({build.file_count} files, {_fmt_size(build.byte_count)} unpacked)")
    if build.previous_version:
        print(f"Version: {build.previous_version} -> {build.version}" + ("" if build.dry_run else f", recorded in {ch.SETTINGS_FILE}"))
    else:
        print(f"Version: {build.version} (first build)" + ("" if build.dry_run else f", recorded in {ch.SETTINGS_FILE}"))

    print()
    if build.block_text is None:
        print("No always-on block to paste yet: README.md has none. Reins writes it.")
        return
    if build.block_changed:
        why = "first build recorded" if build.previous_version is None else "its stamp changed since the last build"
        print(f"The always-on block CHANGED ({why}): paste it again.")
    else:
        print("The always-on block is unchanged since the last build; nothing to paste unless it was never pasted.")
    print(f"  Where: {ORG_INSTRUCTIONS_WHERE}")
    print(f"  Who:   {ORG_INSTRUCTIONS_WHO}")
    print(f"  Size:  {build.block_chars:,} of {build.block_cap:,} characters")
    print(f"  Per {ORG_INSTRUCTIONS_SOURCE}.")
    print("```text")
    print(build.block_text)
    print("```")


def render_json(build: Build) -> None:
    print(json.dumps({
        "ok": build.ok,
        "dry_run": build.dry_run,
        "refusals": [{"path": p, "message": m} for p, m in build.refusals],
        "notes": [{"path": p, "message": m} for p, m in build.warnings],
        "checker": [f.__dict__ for f in build.checker_findings],
        "secrets": [{"path": p, "line": l, "rule": r, "snippet": s, "ships": ships} for p, l, r, s, ships in build.scanner_findings],
        "went_in": [{"skill": n, "files": f} for n, f in build.went_in],
        "left_out": [{"path": p, "reason": r} for p, r in build.left_out],
        "manifest": build.manifest,
        "previous_version": build.previous_version,
        "version": build.version,
        "file_count": build.file_count,
        "byte_count": build.byte_count,
        "zip": str(build.zip_path) if build.zip_path else None,
        "block": None if build.block_text is None else {
            "text": build.block_text,
            "chars": build.block_chars,
            "cap": build.block_cap,
            "stamp": build.block_stamp,
            "changed": build.block_changed,
            "where": ORG_INSTRUCTIONS_WHERE,
            "who": ORG_INSTRUCTIONS_WHO,
            "source": ORG_INSTRUCTIONS_SOURCE,
        },
    }, indent=2, ensure_ascii=False))


# --- Self-test -------------------------------------------------------------------
#
# A throwaway company folder, built and then broken in each of the ways the
# allowlist exists to catch. Standard library only; run by CI.

_CONDUCT = """---
name: {p}-conduct
description: "Use this skill first, before any work on a {P} order, customer, or ticket: its checklist is the pre-flight and its table says which skill to open. Do NOT use for the AI house rules in full ({p}-house-rules)."
metadata:
  version: 0.1.0
  role: conduct
---

# {P} conduct

## TL;DR checklist

1. Plain words.
2. Confirm before anything that sends.
{extra}
---

## Reach for a specialised skill

| When the work is about | Open |
| --- | --- |
| What staff may do with AI | {p}-house-rules |
"""

_HOUSE_RULES = """---
name: {p}-house-rules
description: "Use this skill when someone asks what staff may or may not do with AI at {P}, or wants to paste something that might not belong in an AI. Do NOT use for the everyday checklist ({p}-conduct)."
metadata:
  version: 0.1.0
  role: house-rules
---

# {P} AI house rules

## Data that never goes into an AI

- Payroll.
- Customer personal data.

## Sanctioned routes

- The connector {P} provides.
- The systems' own screens, with the person driving.

## Example

Input: "paste the payroll file". Expected: decline and offer the version without salaries.
"""

_TOOL_SKILL = """---
name: {p}-helper
description: "Use this skill when testing that a tool-marked skill is refused by the build; it exists only for that test and routes nowhere else ({p}-conduct)."
metadata:
  version: 0.1.0
  greenhorn-tool: true
---

# Helper

Body.
"""


def _make_folder(root: Path, prefix: str = "acme", company: str = "Acme", author: bool = True) -> None:
    skills = root / "skills"
    (skills / f"{prefix}-conduct").mkdir(parents=True)
    (skills / f"{prefix}-house-rules" / "references").mkdir(parents=True)
    (skills / f"{prefix}-conduct" / "SKILL.md").write_text(_CONDUCT.format(p=prefix, P=company, extra=""), encoding="utf-8")
    (skills / f"{prefix}-house-rules" / "SKILL.md").write_text(_HOUSE_RULES.format(p=prefix, P=company), encoding="utf-8")
    (skills / f"{prefix}-house-rules" / "references" / "policy.md").write_text("<!--\nSource: Acme AI policy\nDate: 2026-01-01\n-->\n\nThe policy.\n", encoding="utf-8")
    lines = ["instruction-language: en", 'placeholders: "Tulipware, Nordlicht Optics"']
    if author:
        lines.append(f'plugin-author: "{company} Ltd"')
    (root / "harness.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_readme(root, prefix, company)


def _write_readme(root: Path, prefix: str, company: str) -> None:
    skills = ch.load_skills(root)
    stamp, problem = ch.org_block_fingerprint(skills)
    assert problem is None, problem
    (root / "README.md").write_text(
        f"# {company}: the assistant's knowledge\n\n"
        f"{company} sells kitchenware to shops across Europe. This folder is what its assistant knows.\n\n"
        "## The always-on block\n\n"
        f"{ch.ORG_BLOCK_START}\n<!-- ORG-INSTRUCTIONS:CONDUCT-HASH={stamp} -->\n"
        f"```text\n{company} conduct. (A) House rules: {prefix}-house-rules. (B) Plain words; confirm before sending; payroll never goes in.\n```\n"
        f"{ch.ORG_BLOCK_END}\n", encoding="utf-8")


def _zip_names(path: Path) -> list:
    with zipfile.ZipFile(path) as zf:
        return sorted(zf.namelist())


def self_test() -> int:
    passed = []

    def case(name: str, condition: bool, detail: str = "") -> None:
        if not condition:
            raise AssertionError(f"{name}: {detail}")
        passed.append(name)

    with tempfile.TemporaryDirectory(prefix="greenhorn-selftest-") as tmp:
        base = Path(tmp)

        # 1. A clean folder builds, with exactly the allowlist inside.
        root = base / "clean"
        _make_folder(root)
        b = build_folder(root)
        case("clean build succeeds", b.ok, "; ".join(m for _, m in b.refusals))
        case("first version", b.version == FIRST_VERSION and b.previous_version is None, str(b.version))
        names = _zip_names(b.zip_path)
        case("zip holds exactly the allowlist", names == [
            "acme/.claude-plugin/plugin.json",
            "acme/skills/acme-conduct/SKILL.md",
            "acme/skills/acme-house-rules/SKILL.md",
            "acme/skills/acme-house-rules/references/policy.md",
        ], str(names))
        manifest = json.loads(zipfile.ZipFile(b.zip_path).read("acme/.claude-plugin/plugin.json"))
        case("manifest fields", manifest["name"] == "acme" and manifest["version"] == FIRST_VERSION and manifest["author"]["name"] == "Acme Ltd" and manifest["description"].startswith("Acme sells kitchenware"), str(manifest))
        case("first build flags the block", b.block_changed is True and b.block_text is not None)
        state_text = (root / "harness.yaml").read_text(encoding="utf-8-sig")
        case("build state recorded", f"version: {FIRST_VERSION}" in state_text and "org-block-stamp:" in state_text, state_text)
        case("settings kept", 'plugin-author: "Acme Ltd"' in state_text and "instruction-language: en" in state_text, state_text)

        # 2. The second build bumps the patch number and sees no block change.
        b2 = build_folder(root)
        case("second build bumps patch", b2.ok and b2.previous_version == FIRST_VERSION and b2.version == "0.1.1", f"{b2.previous_version} -> {b2.version}")
        case("block unchanged on second build", b2.block_changed is False)
        case("second build state replaces the first", (root / "harness.yaml").read_text(encoding="utf-8-sig").count("version:") == 1)
        b3 = build_folder(root, bump="minor")
        case("minor bump", b3.ok and b3.version == "0.2.0", str(b3.version))
        b4 = build_folder(root, set_version="0.1.5")
        case("lower explicit version refused", not b4.ok and any("not higher" in m for _, m in b4.refusals), str(b4.refusals))
        b5 = build_folder(root, set_version="1.0.0")
        case("explicit higher version accepted", b5.ok and b5.version == "1.0.0")

        # 3. A dry run writes nothing.
        dry = base / "dry"
        _make_folder(dry)
        before = (dry / "harness.yaml").read_text(encoding="utf-8-sig")
        b = build_folder(dry, dry_run=True)
        case("dry run reports", b.ok and b.went_in and b.zip_path is not None)
        case("dry run writes nothing", not (dry / "dist").exists() and (dry / "harness.yaml").read_text(encoding="utf-8-sig") == before)

        # 4. A tool-marked skill is refused.
        tool = base / "tool"
        _make_folder(tool)
        (tool / "skills" / "acme-helper").mkdir()
        (tool / "skills" / "acme-helper" / "SKILL.md").write_text(_TOOL_SKILL.format(p="acme"), encoding="utf-8")
        b = build_folder(tool)
        case("greenhorn-tool skill refused", not b.ok and any(ch.GREENHORN_TOOL_KEY in m for _, m in b.refusals), str(b.refusals))
        case("greenhorn-tool skill not staged", all(n != "acme-helper" for n, _ in b.went_in))

        # 5. Greenhorn's own folder is refused.
        own = base / "own"
        _make_folder(own)
        (own / "skills" / "greenhorn").mkdir()
        (own / "skills" / "greenhorn" / "SKILL.md").write_text("---\nname: greenhorn\ndescription: x\n---\n", encoding="utf-8")
        b = build_folder(own)
        case("Greenhorn's own folder refused", not b.ok and any("Greenhorn's own skill" in m for _, m in b.refusals), str(b.refusals))

        # 6. A top-level bin/ is refused.
        binf = base / "bin"
        _make_folder(binf)
        (binf / "bin").mkdir()
        (binf / "bin" / "tool.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        b = build_folder(binf)
        case("top-level bin refused", not b.ok and any("bin/" in m for _, m in b.refusals), str(b.refusals))

        # 7. The profile, sources, brand sources, house rules, README, and a
        #    stray file in a skill folder are present and stay out.
        sens = base / "sensitive"
        _make_folder(sens)
        (sens / "harness-profile.md").write_text("# Profile\n\n- Real Person said something. [you said]\n", encoding="utf-8")
        (sens / "sources").mkdir()
        (sens / "sources" / "handbook.md").write_text("Internal handbook.\n", encoding="utf-8")
        (sens / "brand-sources").mkdir()
        (sens / "brand-sources" / "letterhead.txt").write_text("photo\n", encoding="utf-8")
        (sens / "HOUSE-RULES.md").write_text("# House rules\n", encoding="utf-8")
        (sens / "skills" / "acme-conduct" / "notes.txt").write_text("scratch\n", encoding="utf-8")
        (sens / "skills" / "acme-conduct" / ".DS_Store").write_bytes(b"\x00")
        b = build_folder(sens)
        case("sensitive folder still builds", b.ok, "; ".join(m for _, m in b.refusals))
        names = _zip_names(b.zip_path)
        case("nothing sensitive in the zip", not any(x in n for n in names for x in ("harness-profile", "sources", "HOUSE-RULES", "README", "harness.yaml", "notes.txt", ".DS_Store")), str(names))
        left = {p for p, _ in b.left_out}
        case("left-out list names them", {"harness-profile.md", "sources/", "brand-sources/", "HOUSE-RULES.md", "README.md", "harness.yaml", "skills/acme-conduct/notes.txt"} <= left, str(left))

        # 8. A changed checklist with a stale stamp is refused; re-stamped, it
        #    builds and flags the block.
        stale = base / "stale"
        _make_folder(stale)
        build_folder(stale)
        conduct = stale / "skills" / "acme-conduct" / "SKILL.md"
        conduct.write_text(_CONDUCT.format(p="acme", P="Acme", extra="3. Never state a figure from memory.\n"), encoding="utf-8")
        b = build_folder(stale)
        case("stale stamp refused", not b.ok and any("CONDUCT-HASH" in f.message or "last reviewed" in f.message for f in b.checker_findings), str([f.message for f in b.checker_findings]))
        _write_readme(stale, "acme", "Acme")
        b = build_folder(stale)
        case("re-stamped folder builds", b.ok, "; ".join(m for _, m in b.refusals))
        case("changed stamp flags the block", b.block_changed is True)

        # 9. A changed routes section also trips the stamp.
        routes = base / "routes"
        _make_folder(routes)
        hr = routes / "skills" / "acme-house-rules" / "SKILL.md"
        hr.write_text(hr.read_text(encoding="utf-8-sig").replace("- The connector", "- Scripts with your own login.\n- The connector"), encoding="utf-8")
        b = build_folder(routes)
        case("changed routes refused until re-stamped", not b.ok)

        # 10. A skill outside the prefix is refused.
        odd = base / "odd"
        _make_folder(odd)
        (odd / "skills" / "other-thing").mkdir()
        (odd / "skills" / "other-thing" / "SKILL.md").write_text("---\nname: other-thing\ndescription: \"Use this skill when nothing applies; it exists to be refused and routes to acme-conduct.\"\nmetadata:\n  version: 0.1.0\n---\n\nBody.\n", encoding="utf-8")
        b = build_folder(odd)
        case("skill outside the prefix refused", not b.ok and any("prefix" in m for _, m in b.refusals), str(b.refusals))

        # 11. No author: refused with the fix named.
        noauthor = base / "noauthor"
        _make_folder(noauthor, author=False)
        b = build_folder(noauthor)
        case("missing author refused", not b.ok and any("plugin-author" in m for _, m in b.refusals), str(b.refusals))

        # 12. A reserved plugin name is refused.
        reserved = base / "reserved"
        _make_folder(reserved)
        with (reserved / "harness.yaml").open("a", encoding="utf-8") as fh:
            fh.write("plugin-name: claude-acme\n")
        b = build_folder(reserved)
        case("reserved plugin name refused", not b.ok and any("reserved" in m for _, m in b.refusals), str(b.refusals))

        # 13. A secret in a skill refuses; one in sources/ is a note.
        secret = base / "secret"
        _make_folder(secret)
        (secret / "sources").mkdir()
        # Built from two halves so the repository's own secret scan does not trip
        # over this file.
        fake_key = "AKIA" + "IOSFODNN7REALKEY1"[:16]
        (secret / "sources" / "old.env").write_text(f"aws_access_key_id = {fake_key}\n", encoding="utf-8")
        b = build_folder(secret)
        case("secret outside the plugin is a note, not a refusal", b.ok and any("credential" in m for _, m in b.warnings), str((b.refusals, b.warnings)))
        (secret / "skills" / "acme-conduct" / "references").mkdir(exist_ok=True)
        (secret / "skills" / "acme-conduct" / "references" / "setup.md").write_text(f"<!--\nTitle: Setup\nDate: 2026-01-01\n-->\n\naws_access_key_id = {fake_key}\n", encoding="utf-8")
        b = build_folder(secret)
        case("secret inside a skill refuses", not b.ok and any(ships for *_, ships in b.scanner_findings), str(b.scanner_findings))

        # 14. Symbolic links under skills/ are refused: a file link, a
        #     references/ folder that is a link, and a skill folder that is one.
        link = base / "links"
        _make_folder(link)
        (link / "harness-profile.md").write_text("# Profile\n\nSecret things.\n", encoding="utf-8")
        (link / "sources").mkdir()
        (link / "sources" / "handbook.md").write_text("Internal.\n", encoding="utf-8")
        os.symlink(link / "harness-profile.md", link / "skills" / "acme-house-rules" / "references" / "profile.md")
        b = build_folder(link)
        case("file symlink refused", not b.ok and any("symbolic link" in m for _, m in b.refusals), str(b.refusals))
        os.remove(link / "skills" / "acme-house-rules" / "references" / "profile.md")
        os.symlink(link / "sources", link / "skills" / "acme-conduct" / "references")
        b = build_folder(link)
        case("references symlink refused", not b.ok and any("symbolic link" in m for _, m in b.refusals), str(b.refusals))
        os.remove(link / "skills" / "acme-conduct" / "references")
        outside = base / "outside-skill"
        outside.mkdir()
        (outside / "SKILL.md").write_text("---\nname: acme-outside\ndescription: \"Use this skill when testing a linked skill folder; it routes to acme-conduct.\"\nmetadata:\n  version: 0.1.0\n---\n\nBody.\n", encoding="utf-8")
        os.symlink(outside, link / "skills" / "acme-outside")
        b = build_folder(link)
        case("skill folder symlink refused", not b.ok and any("symbolic link" in m for _, m in b.refusals), str(b.refusals))
        os.remove(link / "skills" / "acme-outside")
        b = build_folder(link)
        case("folder builds once the links are gone", b.ok, "; ".join(m for _, m in b.refusals))

        # 15. A lost build state cannot make the version fall back below dist/.
        lost = base / "lost"
        _make_folder(lost)
        build_folder(lost)
        build_folder(lost)
        text = (lost / "harness.yaml").read_text(encoding="utf-8-sig")
        (lost / "harness.yaml").write_text(text.split(STATE_COMMENT)[0], encoding="utf-8")
        b = build_folder(lost)
        case("version regression refused", not b.ok and any("not higher" in m for _, m in b.refusals), str(b.refusals))
        b = build_folder(lost, set_version="0.2.0")
        case("explicit version above dist accepted", b.ok and b.version == "0.2.0", str(b.refusals))

        # 16. A SKILL.md under references/, a second fence in the block, and a
        #     marker written as "yes" are each refused.
        nested = base / "nested"
        _make_folder(nested)
        (nested / "skills" / "acme-house-rules" / "references" / "old").mkdir()
        (nested / "skills" / "acme-house-rules" / "references" / "old" / "SKILL.md").write_text("---\nname: old\ndescription: stray\n---\n", encoding="utf-8")
        b = build_folder(nested)
        case("SKILL.md under references refused", not b.ok and any("stray copy" in m for _, m in b.refusals), str(b.refusals))
        fences = base / "fences"
        _make_folder(fences)
        readme = fences / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8-sig").replace(ch.ORG_BLOCK_START + "\n", ch.ORG_BLOCK_START + "\n```text\ndraft\n```\n", 1), encoding="utf-8")
        b = build_folder(fences)
        case("two fences in the block refused", not b.ok and any("```text blocks" in f.message for f in b.checker_findings), str([f.message for f in b.checker_findings]))
        yes = base / "yes"
        _make_folder(yes)
        (yes / "skills" / "acme-helper").mkdir()
        (yes / "skills" / "acme-helper" / "SKILL.md").write_text(_TOOL_SKILL.format(p="acme").replace("greenhorn-tool: true", "greenhorn-tool: yes"), encoding="utf-8")
        b = build_folder(yes)
        case("marker spelled yes still refused as the marker", not b.ok and any(ch.GREENHORN_TOOL_KEY in m for _, m in b.refusals), str(b.refusals))

        # 17. The description never comes from inside the always-on block.
        blurb = base / "blurb"
        _make_folder(blurb)
        readme = blurb / "README.md"
        text = readme.read_text(encoding="utf-8-sig")
        text = text.replace("Acme sells kitchenware to shops across Europe. This folder is what its assistant knows.\n\n", "")
        readme.write_text(text, encoding="utf-8")
        b = build_folder(blurb, dry_run=True)
        case("no prose paragraph means no description, never the block", not b.ok and any("no description" in m for _, m in b.refusals), str((b.refusals, b.manifest)))

        # 18. The JSON rendering round-trips.
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            render_json(build_folder(base / "clean", dry_run=True))
        data = json.loads(buf.getvalue())
        case("json output parses", data["ok"] is True and data["block"]["where"] == ORG_INSTRUCTIONS_WHERE)

    print(f"Self-test: {len(passed)} cases passed.")
    return 0


# --- Driver ----------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build a company plugin from a company folder.")
    parser.add_argument("root", nargs="?", default=".", help="the company folder (default: the current folder)")
    parser.add_argument("--dry-run", action="store_true", help="say what would go in and stay out, and write nothing")
    parser.add_argument("--bump", choices=("patch", "minor", "major"), default="patch", help="which part of the version to raise (default: patch)")
    parser.add_argument("--set-version", metavar="X.Y.Z", help="use this version instead of bumping; it must be higher than the last build")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--self-test", action="store_true", help="prove the refusals on a throwaway folder and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        try:
            return self_test()
        except AssertionError as e:
            print(f"Self-test FAILED: {e}", file=sys.stderr)
            return 1

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR  {args.root}: not a folder", file=sys.stderr)
        return 2

    build = build_folder(root, dry_run=args.dry_run, bump=args.bump, set_version=args.set_version)
    if args.json:
        render_json(build)
    else:
        render_text(build)
    return 0 if build.ok else 1


def _utf8_output() -> None:
    """Windows consoles default to a legacy code page; a character outside
    it would otherwise end the run with a traceback."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _run() -> int:
    _utf8_output()
    try:
        return main()
    except UnicodeDecodeError:
        print("ERROR  a file in this folder is not saved as UTF-8 text, so it could not be read. "
              "Re-save README.md, harness.yaml, and the skill files as UTF-8 and run this again.", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"ERROR  could not read or write a file: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(_run())
