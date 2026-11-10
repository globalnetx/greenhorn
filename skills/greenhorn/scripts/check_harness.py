#!/usr/bin/env python3
# Copyright 2026 GNX. Licensed under the Apache License, Version 2.0;
# see the LICENSE file in the Greenhorn repository,
# https://github.com/globalnetx/greenhorn.
"""
Check a company plugin folder before it is built.

Reads every skill under skills/, the command files under commands/ when
there are any, the organisation-instructions block in README.md, and the
optional harness.yaml settings file, and reports what
would break or mislead once the plugin is installed: frontmatter the upload
would reject, descriptions that cannot route, pointers that do not land,
names that must never appear, text written for one specific model. Output
is plain language with file and line. Exits non-zero on errors so a build
step or CI can gate on it.

Usage (from wherever this file sits; in the Greenhorn repository that is
skills/greenhorn/scripts/):
    python3 check_harness.py                 # check the current folder
    python3 check_harness.py path/to/folder  # check another folder
    python3 check_harness.py --strict        # warnings fail too
    python3 check_harness.py --quiet         # findings only, no summary
    python3 check_harness.py --json          # machine-readable output

Python 3.9 or newer, standard library only. The skill's references
schema.md and conventions.md explain every rule enforced here.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# --- The contract (references/schema.md) -----------------------------------------------

# A skill uploaded to claude.ai accepts exactly these top-level fields.
TOP_LEVEL_FIELDS = ("name", "description", "license", "compatibility", "metadata", "allowed-tools")
# Everything else a maintainer tracks lives one level down, under metadata.
METADATA_FIELDS = ("version", "audience", "tags", "language", "role", "deprecated", "replaced-by", "greenhorn-tool")
AUDIENCES = ("internal", "public", "restricted")
DEFAULT_AUDIENCE = "internal"
# conduct: owns the cross-cutting rules and the routing table.
# house-rules: owns the list of data that never goes into an AI.
# The organisation-instructions stamp covers one section of each.
ROLES = ("conduct", "house-rules")
# Greenhorn's own skill carries this marker; the build never copies a skill
# that has it into a company plugin.
GREENHORN_TOOL_KEY = "greenhorn-tool"

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MIN = 3
NAME_MAX = 64
DESCRIPTION_MIN = 40
DESCRIPTION_MAX = 1024  # the plugin sync drops longer descriptions with only a warning
COMPATIBILITY_MAX = 500
BODY_MAX_LINES = 500
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
# A language code: two letters, optionally a region (en, nl, en-GB, nl-BE).
LANGUAGE_RE = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RELATIVE_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ASSET_PATH_RE = re.compile(r"references/[A-Za-z0-9_./-]+")
KEBAB_TOKEN_RE = re.compile(r"(?<![\w/.-])([a-z0-9]+(?:-[a-z0-9]+)+)(?![\w/-])(?!\.\w)")
NAMED_SKILL_REF_RE = re.compile(r"\b([a-z0-9]+(?:-[a-z0-9]+)+)\s+skills?\b")
TRIGGER_RE = re.compile(r"\b[Uu]se this skill\b|\b[Tt]rigger\b|\b[Ww]hen\b")

# The dated source header every Markdown file under a skill's references/
# opens with (schema.md, "Reference files"): an HTML comment at the very
# top, or else the file's first paragraph, holding one line that names the
# source or title and one that carries a real date.
REFERENCE_HEADER_LINES = 15
REFERENCE_SOURCE_RE = re.compile(r"^\s*(?:<!--\s*)?(?:Source|Title)\s*:\s*\S", re.IGNORECASE)
REFERENCE_DATE_RE = re.compile(r"^\s*(?:<!--\s*)?Date\s*:\s*(\d{4}-\d{2}(?:-\d{2})?)\b", re.IGNORECASE)
EXCLUSION_RE = re.compile(r"\b(?:do not|don't|never) use\b", re.IGNORECASE)

# conventions.md, "Write for any model". Warnings, so a skill that is
# explicitly about one client can still pass without --strict.
PORTABILITY_PATTERNS = [
    (re.compile(r"\byou are claude\b", re.IGNORECASE),
     'addresses the model by name ("you are Claude"); write it for a competent colleague instead'),
    (re.compile(r"<thinking>", re.IGNORECASE),
     "uses a <thinking> tag, a prompt trick for one specific model; state the procedure directly"),
    (re.compile(r"\bthink step by step\b", re.IGNORECASE),
     'says "think step by step", a prompt trick for one specific model; state the procedure directly'),
    (re.compile(r"\b(?:anthropic|openai|chatgpt)\b", re.IGNORECASE),
     "names an AI provider; the content should outlive the provider"),
]

# The organisation-instructions block in README.md (schema.md, "Other
# contracts the checker enforces").
ORG_BLOCK_START = "<!-- ORG-INSTRUCTIONS:START -->"
ORG_BLOCK_END = "<!-- ORG-INSTRUCTIONS:END -->"
ORG_HASH_RE = re.compile(r"<!--\s*ORG-INSTRUCTIONS:CONDUCT-HASH=([0-9a-f]+)\s*-->")
ORG_BLOCK_FENCE_RE = re.compile(r"```text\s*\n(.*?)\n```", re.DOTALL)
ORG_BLOCK_MAX = 3000

SETTINGS_FILE = "harness.yaml"
DEFAULT_PLACEHOLDERS = ["Tulipware", "Nordlicht Optics"]


# --- Findings ----------------------------------------------------------------


@dataclass
class Finding:
    level: str  # "error" or "warning"
    path: str
    line: Optional[int]
    message: str


@dataclass
class Report:
    root: Path
    findings: list = field(default_factory=list)
    skills_checked: int = 0
    commands_checked: int = 0
    org_block_chars: Optional[int] = None
    org_block_cap: Optional[int] = None

    def _rel(self, path) -> str:
        p = Path(path)
        try:
            return str(p.resolve().relative_to(self.root.resolve()))
        except ValueError:
            return str(p)

    def error(self, path, message: str, line: Optional[int] = None) -> None:
        self.findings.append(Finding("error", self._rel(path), line, message))

    def warn(self, path, message: str, line: Optional[int] = None) -> None:
        self.findings.append(Finding("warning", self._rel(path), line, message))

    @property
    def errors(self) -> list:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list:
        return [f for f in self.findings if f.level == "warning"]


# --- A small YAML reader (standard library only) -----------------------------
#
# Frontmatter and the settings file use a narrow shape: `key: value` at the
# left margin, where value is a plain or quoted single-line string, a flow
# list ([a, b]) or a block list (one "- item" per line); plus one nested
# mapping under a key such as `metadata:`. Nothing deeper, no multi-line
# scalars, no anchors. A full YAML library would be more than the content
# needs, and would be one more thing to install on the admin's computer.

_QUOTED_SCALAR_RE = re.compile(r'^(?:"((?:\\.|[^"\\])*)"|\'((?:\'\'|[^\'])*)\')\s*(?:#.*)?$')
_FLOW_LIST_RE = re.compile(r"^\[(.*)\]\s*$")
_BLOCK_ITEM_RE = re.compile(r"^(\s+)-\s+(.*)$")
_FLUSH_ITEM_RE = re.compile(r"^-\s+(.*)$")
_ANY_ITEM_RE = re.compile(r"^\s*-\s+(.*)$")


def _parse_scalar(value: str) -> str:
    value = value.rstrip()
    if not value:
        return ""
    m = _QUOTED_SCALAR_RE.match(value)
    if m:
        if m.group(1) is not None:
            raw = m.group(1)
            return (
                raw.replace(r"\"", '"')
                   .replace(r"\\", "\\")
                   .replace(r"\n", "\n")
                   .replace(r"\t", "\t")
            )
        return m.group(2).replace("''", "'")
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def _parse_flow_list(value: str) -> list:
    inner = value.strip()[1:-1].strip()
    if not inner:
        return []
    items = []
    current = []
    in_dq = in_sq = False
    for ch in inner:
        if ch == '"' and not in_sq:
            in_dq = not in_dq
            current.append(ch)
        elif ch == "'" and not in_dq:
            in_sq = not in_sq
            current.append(ch)
        elif ch == "," and not in_dq and not in_sq:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        items.append("".join(current).strip())
    return [_parse_scalar(item) for item in items if item]


def _parse_value(rest: str):
    if _FLOW_LIST_RE.match(rest):
        return _parse_flow_list(rest)
    return _parse_scalar(rest)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#")


def parse_simple_yaml(text: str, first_line: int = 1):
    """Return (data, where, error).

    `data` maps keys to strings, lists, or (one level down) dicts of the
    same. `where` maps the same keys, and `parent.child` for nested keys,
    to file line numbers. `error` is None or (line, message).
    """
    lines = text.splitlines()
    data = {}
    where = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        lineno = first_line + i
        if _is_blank_or_comment(line):
            i += 1
            continue
        if _indent(line) > 0:
            return None, None, (lineno, "unexpected indentation; only `key: value` lines at the left margin are allowed here, plus one indented level under metadata")
        stripped = line.strip()
        if ":" not in stripped:
            return None, None, (lineno, "this line is not `key: value`")
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if not key:
            return None, None, (lineno, "empty key before the colon")
        if key in data:
            return None, None, (lineno, f"`{key}` appears twice; keep one")
        if rest.startswith("#"):
            rest = ""
        if rest:
            data[key] = _parse_value(rest)
            where[key] = lineno
            i += 1
            continue

        # Empty value: a block list or a nested mapping follows (or nothing).
        # List items may sit at the left margin (`- item`), the way most
        # people type YAML, or indented.
        block = []
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            if _is_blank_or_comment(nxt):
                j += 1
                continue
            if _indent(nxt) == 0 and not _FLUSH_ITEM_RE.match(nxt):
                break
            block.append((first_line + j, nxt))
            j += 1

        where[key] = lineno
        if not block:
            data[key] = ""
        elif all(_ANY_ITEM_RE.match(l) for _, l in block):
            data[key] = [_parse_scalar(_ANY_ITEM_RE.match(l).group(1)) for _, l in block]
        else:
            nested, err = _parse_nested(block, key, where)
            if err:
                return None, None, err
            data[key] = nested
        i = j
    return data, where, None


def _parse_nested(block, parent: str, where: dict):
    """Parse one indented mapping level. Values are scalars, flow lists, or
    a block list indented deeper than the mapping's own keys."""
    nested = {}
    base = _indent(block[0][1])
    k = 0
    while k < len(block):
        lineno, line = block[k]
        ind = _indent(line)
        if ind != base:
            return None, (lineno, f"nesting deeper than one level under `{parent}` is not allowed; keep `{parent}` to simple `key: value` pairs")
        stripped = line.strip()
        if _BLOCK_ITEM_RE.match(line):
            return None, (lineno, f"a list item where a `key: value` pair was expected under `{parent}`")
        if ":" not in stripped:
            return None, (lineno, f"this line under `{parent}` is not `key: value`")
        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        if not key:
            return None, (lineno, f"empty key before the colon under `{parent}`")
        if key in nested:
            return None, (lineno, f"`{parent}.{key}` appears twice; keep one")
        if rest.startswith("#"):
            rest = ""
        where[f"{parent}.{key}"] = lineno
        if rest:
            nested[key] = _parse_value(rest)
            k += 1
            continue
        items = []
        k += 1
        while k < len(block):
            sub_lineno, sub = block[k]
            m = _BLOCK_ITEM_RE.match(sub)
            if not m or _indent(sub) <= base:
                break
            items.append(_parse_scalar(m.group(2)))
            k += 1
        if not items and k < len(block) and _indent(block[k][1]) > base:
            return None, (block[k][0], f"nesting deeper than one level under `{parent}` is not allowed; keep `{parent}` to simple `key: value` pairs")
        nested[key] = items if items else ""
    return nested, None


def parse_frontmatter(content: str):
    """Return (data, where, body, body_first_line, error)."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return None, None, "", 1, (1, "missing or malformed frontmatter; the file must start with `---` on line 1, the fields, and a closing `---`")
    data, where, err = parse_simple_yaml(match.group(1), first_line=2)
    if err:
        return None, None, "", 1, err
    body = content[len(match.group(0)):]
    body_first_line = match.group(0).count("\n") + 1
    return data, where, body, body_first_line, None


# --- Skills -------------------------------------------------------------------


@dataclass
class Skill:
    name: str
    folder: Path
    path: Path
    data: dict
    where: dict
    body: str
    body_first_line: int

    @property
    def metadata(self) -> dict:
        md = self.data.get("metadata")
        return md if isinstance(md, dict) else {}

    @property
    def audience(self) -> str:
        value = self.metadata.get("audience")
        return value if isinstance(value, str) and value else DEFAULT_AUDIENCE

    @property
    def role(self) -> str:
        value = self.metadata.get("role")
        return value if isinstance(value, str) else ""

    @property
    def is_greenhorn_tool(self) -> bool:
        return self.metadata.get(GREENHORN_TOOL_KEY) == "true"

    @property
    def description(self) -> str:
        value = self.data.get("description")
        return value if isinstance(value, str) else ""

    def line_of(self, key: str) -> Optional[int]:
        return self.where.get(key)


def _plural(n: int, word: str) -> str:
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def check_top_level(skill_md: Path, data: dict, where: dict, report: Report) -> None:
    for key in data:
        if key in TOP_LEVEL_FIELDS:
            continue
        if key in METADATA_FIELDS:
            report.error(skill_md, f"`{key}` is not allowed at the top level; the plugin upload rejects it. Move it under `metadata:` (indented one level).", where.get(key))
        else:
            report.error(skill_md, f"`{key}` is not one of the {len(TOP_LEVEL_FIELDS)} fields the plugin upload accepts ({', '.join(TOP_LEVEL_FIELDS)}). Remove it, or put it under `metadata:`.", where.get(key))


def check_name(skill: Skill, report: Report) -> None:
    name = skill.data.get("name")
    line = skill.line_of("name")
    if name is None:
        report.error(skill.path, "`name` is missing; it must equal the folder name", 2)
        return
    if not isinstance(name, str) or not name.strip():
        report.error(skill.path, "`name` must be a non-empty string", line)
        return
    if not NAME_PATTERN.match(name):
        report.error(skill.path, f"`name` '{name}' must be lowercase letters, digits and hyphens only, like `acme-voice`", line)
    if not (NAME_MIN <= len(name) <= NAME_MAX):
        report.error(skill.path, f"`name` is {_plural(len(name), 'character')}; it must be between {NAME_MIN} and {NAME_MAX}", line)
    if name != skill.folder.name:
        report.error(skill.path, f"`name` '{name}' does not match the folder name '{skill.folder.name}'; they must be identical", line)


def check_description(skill: Skill, report: Report) -> None:
    desc = skill.data.get("description")
    line = skill.line_of("description")
    if desc is None:
        report.error(skill.path, "`description` is missing; it is the line the assistant reads to decide whether to open this skill", 2)
        return
    if not isinstance(desc, str) or not desc.strip():
        report.error(skill.path, "`description` must be a non-empty string on one line", line)
        return
    n = len(desc)
    if n < DESCRIPTION_MIN:
        report.error(skill.path, f"`description` is {_plural(n, 'character')}; it needs at least {DESCRIPTION_MIN} to say when to use the skill", line)
    if n > DESCRIPTION_MAX:
        report.error(skill.path, f"`description` is {n:,} characters; the limit is {DESCRIPTION_MAX:,}, beyond which the plugin sync silently drops the skill. Trim it.", line)
    if not TRIGGER_RE.search(desc):
        report.warn(skill.path, "`description` does not say when to use the skill; start with \"Use this skill when ...\" or \"Trigger when ...\"", line)


def check_optional_top_level(skill: Skill, report: Report) -> None:
    compat = skill.data.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            report.error(skill.path, "`compatibility` must be a short string", skill.line_of("compatibility"))
        elif len(compat) > COMPATIBILITY_MAX:
            report.error(skill.path, f"`compatibility` is {len(compat):,} characters; the limit is {COMPATIBILITY_MAX}", skill.line_of("compatibility"))
    lic = skill.data.get("license")
    if lic is not None and not isinstance(lic, str):
        report.error(skill.path, "`license` must be a string", skill.line_of("license"))
    tools = skill.data.get("allowed-tools")
    if tools is not None and not isinstance(tools, str):
        report.error(skill.path, "`allowed-tools` must be one string of tool names separated by spaces", skill.line_of("allowed-tools"))


def check_metadata(skill: Skill, report: Report) -> None:
    md = skill.data.get("metadata")
    if md is None:
        report.warn(skill.path, "no `metadata:` block; add one with at least `version: 0.1.0` so changes can be tracked", skill.line_of("name"))
        return
    if not isinstance(md, dict):
        report.error(skill.path, "`metadata` must be an indented block of `key: value` pairs", skill.line_of("metadata"))
        return
    for key, value in md.items():
        if isinstance(value, dict):
            report.error(skill.path, f"`metadata.{key}` nests another level; keep metadata to simple `key: value` pairs", skill.line_of(f"metadata.{key}"))
        elif isinstance(value, list):
            report.warn(skill.path, f"`metadata.{key}` is a list; write it as one string with commas, which the upload is documented to accept", skill.line_of(f"metadata.{key}"))

    version = md.get("version")
    if version is None or version == "":
        report.warn(skill.path, "`metadata.version` is missing; add `version: 0.1.0` and bump it when the content changes", skill.line_of("metadata"))
    elif not isinstance(version, str) or not VERSION_RE.match(version):
        report.warn(skill.path, f"`metadata.version` '{version}' is not in the shape major.minor.patch, like 0.1.0", skill.line_of("metadata.version"))

    audience = md.get("audience")
    if audience is not None and audience != "" and audience not in AUDIENCES:
        report.error(skill.path, f"`metadata.audience` '{audience}' is not one of {', '.join(AUDIENCES)}", skill.line_of("metadata.audience"))

    role = md.get("role")
    if role is not None and role != "" and role not in ROLES:
        report.error(skill.path, f"`metadata.role` '{role}' is not a known role; the known roles are {', '.join('`' + r + '`' for r in ROLES)}", skill.line_of("metadata.role"))

    tool = md.get(GREENHORN_TOOL_KEY)
    if tool is not None and tool not in ("true", "false"):
        report.warn(skill.path, f"`metadata.{GREENHORN_TOOL_KEY}` is '{tool}'; write `true` (only on Greenhorn's own skill) or leave it out", skill.line_of(f"metadata.{GREENHORN_TOOL_KEY}"))

    deprecated = md.get("deprecated")
    replaced_by = md.get("replaced-by")
    if deprecated is not None and (not isinstance(deprecated, str) or not deprecated.strip()):
        report.error(skill.path, "`metadata.deprecated` must be a non-empty reason", skill.line_of("metadata.deprecated"))
    if replaced_by is not None:
        if not isinstance(replaced_by, str) or not replaced_by.strip():
            report.error(skill.path, "`metadata.replaced-by` must name the successor skill", skill.line_of("metadata.replaced-by"))
        elif deprecated is None:
            report.warn(skill.path, "`metadata.replaced-by` is set but `metadata.deprecated` gives no reason; add one", skill.line_of("metadata.replaced-by"))


def _body_line(skill: Skill, offset_in_body: int) -> int:
    return skill.body_first_line + skill.body[:offset_in_body].count("\n")


def check_body(skill: Skill, report: Report) -> None:
    body = skill.body
    if not body.strip():
        report.warn(skill.path, "the body is empty; frontmatter alone teaches nothing", skill.body_first_line)
        return
    n_lines = body.count("\n") + 1
    if n_lines > BODY_MAX_LINES:
        report.warn(skill.path, f"the body is {n_lines:,} lines; keep SKILL.md under about {BODY_MAX_LINES} and move detail into files under references/", skill.body_first_line)

    for pattern, message in PORTABILITY_PATTERNS:
        for m in pattern.finditer(body):
            report.warn(skill.path, message, _body_line(skill, m.start()))

    # Relative links must resolve and stay inside the plugin: this skill's
    # folder, or a sibling skill under the same skills/ folder.
    link_spans = []
    skills_root = skill.folder.parent.resolve()
    for m in RELATIVE_LINK_RE.finditer(body):
        link_spans.append((m.start(), m.end()))
        target = m.group(1).strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0].split("?", 1)[0]
        if not target_path:
            continue
        resolved = (skill.folder / target_path).resolve()
        line = _body_line(skill, m.start())
        try:
            resolved.relative_to(skills_root)
        except ValueError:
            report.error(skill.path, f"the link '{target}' points outside the skills folder; a plugin carries only what is under skills/", line)
            continue
        if not resolved.exists():
            report.error(skill.path, f"the link '{target}' points at a file that does not exist", line)

    # Supporting files: every non-markdown file under references/ is named in
    # the body (or it is unreachable weight), and every references/ path the
    # body names exists.
    refs_dir = skill.folder / "references"
    if refs_dir.is_dir():
        for asset in sorted(refs_dir.rglob("*")):
            if not asset.is_file() or asset.suffix.lower() == ".md":
                continue
            rel = asset.relative_to(skill.folder).as_posix()
            if rel not in body and asset.name not in body:
                report.error(skill.path, f"'{rel}' sits under references/ but the body never names it, so the assistant cannot find it; name it by path or filename, or remove it")
    for m in ASSET_PATH_RE.finditer(body):
        if any(a <= m.start() < b for a, b in link_spans):
            continue  # already checked as a link above
        token = m.group(0).rstrip(".")
        if token.endswith("/"):
            continue
        if not (skill.folder / token).exists():
            report.error(skill.path, f"the body names '{token}', which does not exist in this skill's folder", _body_line(skill, m.start()))

    check_reference_headers(skill, report)


def check_reference_headers(skill: Skill, report: Report) -> None:
    """Every Markdown file under references/ opens with a dated source
    header, so a reader can tell where it came from and how old it is."""
    refs_dir = skill.folder / "references"
    if not refs_dir.is_dir():
        return
    for ref in sorted(refs_dir.rglob("*")):
        if not ref.is_file() or ref.suffix.lower() != ".md":
            continue
        try:
            head = _reference_header(ref.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, OSError) as e:
            report.error(ref, f"could not read this reference file: {e}")
            continue
        has_source = any(REFERENCE_SOURCE_RE.match(line) for line in head)
        dates = [m.group(1) for m in (REFERENCE_DATE_RE.match(line) for line in head) if m]
        if has_source and dates:
            bad = [d for d in dates if not _is_real_date(d)]
            if bad:
                report.error(ref, f"the header's date '{bad[0]}' is not a real date; write it as YYYY-MM-DD, or YYYY-MM when only the month is known", 1)
            continue
        missing = " and ".join(part for part, ok in (("a `Source:` or `Title:` line", has_source), ("a `Date: YYYY-MM-DD` line", bool(dates))) if not ok)
        report.error(ref, f"this reference file has no dated source header; open the file with {missing}, in an HTML comment at the top or as its first paragraph, so its age can be seen (Greenhorn's schema reference, \"Reference files\")", 1)


def _reference_header(text: str) -> list:
    """The header region: an HTML comment at the very top, or else the
    first paragraph. Leading blank lines are skipped."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    lines = lines[i:i + REFERENCE_HEADER_LINES]
    if lines and lines[0].lstrip().startswith("<!--"):
        region = []
        for line in lines:
            region.append(line)
            if "-->" in line:
                break
        return region
    region = []
    for line in lines:
        if not line.strip():
            break
        region.append(line)
    return region


def _is_real_date(value: str) -> bool:
    try:
        datetime.date.fromisoformat(value if len(value) == 10 else value + "-01")
        return True
    except ValueError:
        return False


def load_skill(folder: Path, report: Optional[Report]) -> Optional[Skill]:
    """Read and check one skill folder. Returns the Skill when its frontmatter
    parsed, even if checks found problems, so cross-checks can still run."""
    skill_md = folder / "SKILL.md"
    if not skill_md.is_file():
        if report:
            report.error(folder, "this folder has no SKILL.md; every folder under skills/ is a skill and needs one")
        return None
    try:
        content = skill_md.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as e:
        if report:
            report.error(skill_md, f"the file is not valid UTF-8 text: {e}")
        return None
    data, where, body, body_first_line, err = parse_frontmatter(content)
    if err:
        if report:
            report.error(skill_md, err[1], err[0])
        return None
    name = data.get("name") if isinstance(data.get("name"), str) else folder.name
    skill = Skill(name=name, folder=folder, path=skill_md, data=data, where=where, body=body, body_first_line=body_first_line)
    if report:
        check_top_level(skill_md, data, where, report)
        check_name(skill, report)
        check_description(skill, report)
        check_optional_top_level(skill, report)
        check_metadata(skill, report)
        check_body(skill, report)
        report.skills_checked += 1
    return skill


def load_skills(root: Path, report: Optional[Report] = None) -> list:
    """Read every skill under root/skills. With a report, run the per-skill
    checks as well. Without one, read silently (the stamper uses this)."""
    skills_root = root / "skills"
    skills = []
    if not skills_root.is_dir():
        return skills
    for entry in sorted(skills_root.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_file():
            if report and entry.name != ".gitkeep":
                report.error(entry, "files do not belong directly under skills/; each skill is a folder with a SKILL.md inside")
            continue
        skill = load_skill(entry, report)
        if skill:
            skills.append(skill)
    return skills


# --- Cross-skill checks -------------------------------------------------------


def _skill_prefixes(names) -> set:
    """The name families in use: `acme-` when two or more skills start with
    `acme-`. A token in a description with such a prefix is meant to be a
    skill, so it must resolve. A prefix used by one skill only is not a
    family; `ai-house-rules` must not make `ai-generated` look like a route."""
    counts = {}
    for n in names:
        if "-" in n:
            p = n.split("-", 1)[0] + "-"
            counts[p] = counts.get(p, 0) + 1
    return {p for p, c in counts.items() if c >= 2}


def _referenced_skill_names(description: str, names: set, prefixes: set) -> set:
    def looks_like_skill(token: str) -> bool:
        return token in names or any(token.startswith(p) for p in prefixes)

    refs = set()
    for token in KEBAB_TOKEN_RE.findall(description):
        if looks_like_skill(token):
            refs.add(token)
    for token in NAMED_SKILL_REF_RE.findall(description):
        if looks_like_skill(token):
            refs.add(token)
    return refs


def _unlabelled(description: str, ref: str, label: str) -> bool:
    """True when any mention of ref lacks the label shortly before it."""
    pattern = re.compile(r"(?<![\w-])" + re.escape(ref) + r"(?![\w-])")
    for m in pattern.finditer(description):
        window = description[max(0, m.start() - 160):m.start()].lower()
        if label not in window:
            return True
    return False


def check_cross_skill(skills: list, report: Report) -> None:
    by_name = {}
    for s in skills:
        if s.name in by_name:
            report.error(s.path, f"another skill is already called '{s.name}' (in {report._rel(by_name[s.name].folder)}); names must be unique", s.line_of("name"))
        else:
            by_name[s.name] = s
    names = set(by_name)
    prefixes = _skill_prefixes(names)

    for s in skills:
        desc_line = s.line_of("description")
        desc = s.description
        if not desc:
            continue
        refs = _referenced_skill_names(desc, names, prefixes)
        others = {r for r in refs if r != s.name}
        for ref in sorted(others):
            if ref not in names:
                report.warn(s.path, f"`description` routes to '{ref}', which is not a skill in this folder; fix the name or drop the route", desc_line)
        if len(names) > 1 and EXCLUSION_RE.search(desc) and not any(r in names for r in others):
            report.warn(s.path, "`description` has a \"do not use for\" exclusion that names no other skill as the destination; say where that work lives instead", desc_line)

        # Audience direction: a route must not dead-end for a reader who
        # cannot see the target.
        for ref in sorted(others):
            target = by_name.get(ref)
            if not target:
                continue
            if target.audience == "restricted" and s.audience != "restricted":
                if _unlabelled(desc, ref, "restricted"):
                    report.warn(s.path, f"`description` routes to '{ref}', a restricted skill, without saying so; label the route \"restricted\" or drop it", desc_line)
            elif target.audience == "internal" and s.audience == "public":
                if _unlabelled(desc, ref, "internal-only"):
                    report.warn(s.path, f"`description` of a public skill routes to '{ref}', an internal skill, without a label; write \"internal-only\" before it so a customer-facing reader is not sent somewhere they cannot go", desc_line)

        replaced_by = s.metadata.get("replaced-by")
        if isinstance(replaced_by, str) and replaced_by.strip() and replaced_by not in names:
            report.error(s.path, f"`metadata.replaced-by` names '{replaced_by}', which is not a skill in this folder", s.line_of("metadata.replaced-by"))

    for role, what in (("conduct", "the rules and the routing table"), ("house-rules", "the list of data that never goes into an AI")):
        holders = [s for s in skills if s.role == role]
        if len(holders) > 1:
            for s in holders:
                report.error(s.path, f"{len(holders)} skills carry `metadata.role: {role}`; only one skill may own {what}", s.line_of("metadata.role"))

    if not any(s.role == "house-rules" for s in skills):
        for s in skills:
            if s.name == "house-rules" or s.name.endswith("-house-rules"):
                report.warn(s.path, "this looks like the house-rules skill but has no `metadata.role: house-rules`; mark it, so the organisation-instructions stamp covers its data list", s.line_of("metadata") or s.line_of("name"))

    tools = [s for s in skills if s.is_greenhorn_tool]
    if tools and len(tools) < len(skills):
        for s in tools:
            report.warn(s.path, f"this is Greenhorn's own skill (`metadata.{GREENHORN_TOOL_KEY}: true`) sitting beside company skills; the build never copies it into a company plugin, so keep it out of the company folder", s.line_of(f"metadata.{GREENHORN_TOOL_KEY}"))

    restricted = [s for s in skills if s.audience == "restricted"]
    if restricted and len(restricted) < len(skills):
        for s in restricted:
            report.warn(s.path, "this restricted skill shares a folder with skills for everyone; a restricted skill ships in its own plugin from its own folder, or every colleague can read it", s.line_of("metadata.audience"))


# --- Settings and the never-name list ----------------------------------------


def _as_list(value) -> list:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def load_settings(root: Path, report: Optional[Report]) -> dict:
    settings = {"placeholders": list(DEFAULT_PLACEHOLDERS), "never_name": [], "org_block_max": ORG_BLOCK_MAX, "instruction_language": None}
    path = root / SETTINGS_FILE
    if not path.is_file():
        return settings
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (UnicodeDecodeError, OSError) as e:
        if report:
            report.error(path, f"could not read the settings file: {e}")
        return settings
    data, where, err = parse_simple_yaml(text, first_line=1)
    if err:
        if report:
            report.error(path, err[1] + "; until this is fixed the never-name list is not applied", err[0])
        return settings
    if "placeholders" in data and _as_list(data["placeholders"]):
        settings["placeholders"] = _as_list(data["placeholders"])
    settings["never_name"] = _as_list(data.get("never-name"))
    cap = data.get("org-block-max")
    if cap not in (None, ""):
        if isinstance(cap, str) and cap.isdigit():
            settings["org_block_max"] = int(cap)
        elif report:
            report.error(path, "`org-block-max` must be a whole number of characters", where.get("org-block-max"))
    language = data.get("instruction-language")
    if language not in (None, ""):
        if isinstance(language, str) and LANGUAGE_RE.match(language.strip()):
            settings["instruction_language"] = language.strip()
        elif report:
            report.error(path, f"`instruction-language` '{language}' is not a language code; use two letters, like `en` or `nl`, optionally with a region, like `en-GB`", where.get("instruction-language"))
    # The plugin-* keys and build-state belong to build_plugin.py, which
    # sits beside this checker and reads them itself.
    known = ("instruction-language", "placeholders", "never-name", "org-block-max",
             "plugin-author", "plugin-name", "plugin-description", "plugin-license", "build-state")
    for key in data:
        if key not in known and report:
            report.warn(path, f"`{key}` is not a setting the checker knows ({', '.join(known)})", where.get(key))
    return settings


def _base_language(code: str) -> str:
    return code.split("-", 1)[0].lower()


def check_languages(skills: list, settings: dict, report: Report) -> None:
    """One plugin, one language for the instructions (conventions.md,
    Language). The first code in metadata.language is the language the
    skill's instructions are written in; later codes are languages its
    content uses, which may legitimately differ."""
    primary = {}
    for s in skills:
        raw = s.metadata.get("language")
        if raw in (None, ""):
            continue
        codes = _as_list(raw)
        line = s.line_of("metadata.language")
        bad = [c for c in codes if not LANGUAGE_RE.match(c)]
        for c in bad:
            report.warn(s.path, f"`metadata.language` has '{c}', which is not a language code; use two letters, like `en` or `nl`, optionally with a region, like `en-GB`", line)
        if codes and not bad:
            primary[s.name] = (s, _base_language(codes[0]), line)

    plugin_language = settings.get("instruction_language")
    if plugin_language:
        expected = _base_language(plugin_language)
        for s, lang, line in primary.values():
            if lang != expected:
                report.warn(s.path, f"this skill's instructions are in '{lang}', but the plugin's instruction language is '{expected}' (harness.yaml). Write the instructions of every skill in one language; examples and documents may stay in another, listed after the first code.", line)
        return

    counts = {}
    for _, lang, _ in primary.values():
        counts[lang] = counts.get(lang, 0) + 1
    if len(counts) < 2:
        return
    majority = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    for s, lang, line in primary.values():
        if lang != majority:
            report.warn(s.path, f"this skill's instructions are in '{lang}', while most skills here have theirs in '{majority}'. Write the instructions of every skill in one language, and set `instruction-language:` in harness.yaml to say which.", line)


NEVER_NAME_SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".ico", ".ttf", ".otf", ".woff", ".woff2"}


def check_never_name(root: Path, settings: dict, report: Report) -> None:
    """Every text file under skills/, whether or not its skill parsed: a
    name that must not appear is a problem wherever it sits."""
    names = settings["never_name"]
    skills_root = root / "skills"
    if not names or not skills_root.is_dir():
        return
    patterns = [(n, re.compile(r"(?<!\w)" + re.escape(n) + r"(?!\w)", re.IGNORECASE)) for n in names]
    suggestion = ", ".join(settings["placeholders"]) or "a placeholder name"
    for f in sorted(skills_root.rglob("*")):
        if not f.is_file() or f.suffix.lower() in NEVER_NAME_SKIP_SUFFIXES:
            continue
        try:
            text = f.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for n, pattern in patterns:
                if pattern.search(line):
                    report.error(f, f"names '{n}', which is on the never-name list; use a placeholder instead ({suggestion})", lineno)


# --- The organisation-instructions block -------------------------------------


def locate_conduct_skill(skills: list) -> Optional[Skill]:
    """The skill that owns the rules: `metadata.role: conduct`, or failing
    that, the one skill whose name is `conduct` or ends in `-conduct`."""
    by_role = [s for s in skills if s.role == "conduct"]
    if len(by_role) == 1:
        return by_role[0]
    if by_role:
        return None
    by_name = [s for s in skills if s.name == "conduct" or s.name.endswith("-conduct")]
    return by_name[0] if len(by_name) == 1 else None


def extract_checklist(body: str) -> Optional[str]:
    """The conduct skill's checklist: from the first `##` heading whose text
    contains "checklist" or "tl;dr" to the next `##` heading or rule."""
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("##") and ("checklist" in line.lower() or "tl;dr" in line.lower()):
            start = i + 1
            break
    if start is None:
        return None
    collected = []
    for line in lines[start:]:
        if line.strip() == "---" or line.startswith("## "):
            break
        collected.append(line)
    text = "\n".join(collected).strip()
    return text or None


def fingerprint(checklist_text: str) -> str:
    """Whitespace-collapsed hash: stable across reflow, changed by any edit."""
    normalized = re.sub(r"\s+", " ", checklist_text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


DATA_HEADING_RE = re.compile(r"\bdata\b", re.IGNORECASE)
ROUTES_HEADING_RE = re.compile(r"\broutes?\b", re.IGNORECASE)
ORG_MARKER_NEAR_MISS_RE = re.compile(r"<!--\s*org[\s_-]*instructions\s*:", re.IGNORECASE)


def locate_house_rules_skill(skills: list) -> Optional[Skill]:
    """The skill that owns the data list: `metadata.role: house-rules`."""
    holders = [s for s in skills if s.role == "house-rules"]
    return holders[0] if len(holders) == 1 else None


def _extract_section(body: str, heading_re) -> Optional[str]:
    """The text under the first `## ` heading matching heading_re, up to
    the next `##` heading or horizontal rule."""
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and heading_re.search(line):
            start = i + 1
            break
    if start is None:
        return None
    collected = []
    for line in lines[start:]:
        if line.strip() == "---" or line.startswith("## "):
            break
        collected.append(line)
    text = "\n".join(collected).strip()
    return text or None


def extract_data_list(body: str) -> Optional[str]:
    """The house-rules skill's data list: from the first `##` heading that
    has the word "data" in it (a whole word, so "metadata" does not count)
    to the next `##` heading or rule."""
    return _extract_section(body, DATA_HEADING_RE)


def extract_routes_section(body: str) -> Optional[str]:
    """The house-rules skill's routes section: from the first `##` heading
    with the word "route" or "routes" in it to the next `##` heading or
    rule. Optional: a company with no connected systems may have none."""
    return _extract_section(body, ROUTES_HEADING_RE)


def org_block_fingerprint(skills: list):
    """Return (fingerprint, None) or (None, (path, message)).

    The stamp covers what Layer B of the block restates: the conduct
    skill's checklist and, when a skill carries `metadata.role:
    house-rules`, its data list and its routes section (when it has one).
    Without a house-rules skill the stamp is the checklist's fingerprint
    alone, as before the list was added."""
    conduct = locate_conduct_skill(skills)
    if conduct is None:
        return None, (None, "no single conduct skill found (mark one with `metadata.role: conduct`)")
    checklist = extract_checklist(conduct.body)
    if checklist is None:
        return None, (conduct.path, "the conduct skill has no checklist section to fingerprint; add a `##` heading containing \"checklist\" or \"TL;DR\" with the rules under it")
    house_rules = locate_house_rules_skill(skills)
    if house_rules is None:
        return fingerprint(checklist), None
    data_list = extract_data_list(house_rules.body)
    if data_list is None:
        return None, (house_rules.path, "the house-rules skill has no data list to fingerprint; put the data that never goes into an AI under a `##` heading with the word \"data\" in it")
    parts = [checklist, data_list]
    routes = extract_routes_section(house_rules.body)
    if routes is not None:
        parts.append(routes)
    return fingerprint("\n\n".join(parts)), None


def stamper_command() -> str:
    """How to run the stamper that sits beside this checker, as a path a
    person can paste: relative to the current folder when it is inside it."""
    stamper = Path(__file__).resolve().with_name("stamp_org_instructions.py")
    try:
        shown = stamper.relative_to(Path.cwd().resolve())
    except ValueError:
        shown = stamper
    text = str(shown)
    return f'python3 "{text}"' if " " in text else f"python3 {text}"


def _line_of_substring(text: str, needle: str) -> Optional[int]:
    idx = text.find(needle)
    return None if idx < 0 else text[:idx].count("\n") + 1


def check_org_block(root: Path, skills: list, settings: dict, report: Report) -> None:
    readme = root / "README.md"
    has_conduct = locate_conduct_skill(skills) is not None
    if not readme.is_file():
        if has_conduct:
            report.warn(root, "there is a conduct skill but no README.md, so the organisation-instructions block cannot be checked; the routing step writes it")
        return
    text = readme.read_text(encoding="utf-8-sig")
    if ORG_BLOCK_START not in text and ORG_BLOCK_END not in text:
        near = ORG_MARKER_NEAR_MISS_RE.search(text)
        if near:
            report.error(readme, f"this looks like an organisation-instructions marker but is not spelled exactly; the markers are `{ORG_BLOCK_START}` and `{ORG_BLOCK_END}`, and until they match, the block's length and stamp go unchecked", _line_of_substring(text, near.group(0)))
        elif has_conduct:
            report.warn(readme, f"there is a conduct skill but README.md has no organisation-instructions block between `{ORG_BLOCK_START}` and `{ORG_BLOCK_END}`, so its length and stamp go unchecked; the routing step writes it")
        return
    start_line = _line_of_substring(text, ORG_BLOCK_START)
    if ORG_BLOCK_START not in text or ORG_BLOCK_END not in text:
        report.error(readme, f"the organisation-instructions block needs both markers, `{ORG_BLOCK_START}` and `{ORG_BLOCK_END}`", start_line or _line_of_substring(text, ORG_BLOCK_END))
        return
    region = text.split(ORG_BLOCK_START, 1)[1].split(ORG_BLOCK_END, 1)[0]
    fences = ORG_BLOCK_FENCE_RE.findall(region)
    if not fences:
        report.error(readme, "the organisation-instructions markers are present but there is no ```text block between them", start_line)
        return
    if len(fences) > 1:
        report.error(readme, f"there are {len(fences)} ```text blocks between the organisation-instructions markers; keep exactly one, the text to paste, so the right one is measured and printed", start_line)
        return
    fence = ORG_BLOCK_FENCE_RE.search(region)
    block_len = len(fence.group(1))
    cap = settings["org_block_max"]
    report.org_block_chars = block_len
    report.org_block_cap = cap
    if block_len > cap:
        report.error(readme, f"the organisation-instructions block is {block_len:,} characters; the field holds at most {cap:,}. Trim it.", start_line)

    expected, problem = org_block_fingerprint(skills)
    if problem:
        path, message = problem
        if path is None:
            report.error(readme, f"cannot verify the organisation-instructions block: {message}", start_line)
        else:
            report.error(path, message)
        return
    stamp = ORG_HASH_RE.search(region)
    if stamp is None:
        report.error(readme, f"the organisation-instructions block has no CONDUCT-HASH stamp; review the block against the conduct checklist and the house-rules data list and routes, then run `{stamper_command()}` (expected {expected})", start_line)
    elif stamp.group(1) != expected:
        report.error(readme, f"the conduct checklist, the house-rules data list, or the house-rules routes changed since the organisation-instructions block was last reviewed (stamp {stamp.group(1)}, now {expected}). Check whether the block needs the new or changed rule, then run `{stamper_command()}`.", start_line)


# --- Driver -------------------------------------------------------------------


def check_folder_shape(root: Path, report: Report) -> None:
    if (root / "bin").is_dir():
        report.error(root / "bin", "a top-level bin/ folder makes claude.ai and Cowork refuse the whole plugin; move its files into another folder, such as scripts/")


def check_commands(root: Path, report: Report) -> None:
    """Command files under commands/: frontmatter with a description, kept to
    the six fields a skill upload accepts. Company folders usually have none;
    Greenhorn's own repository has one per mode."""
    commands_root = root / "commands"
    if not commands_root.is_dir():
        return
    for cmd in sorted(commands_root.rglob("*")):
        if cmd.is_dir() or cmd.name.startswith("."):
            continue
        if cmd.suffix.lower() != ".md":
            report.warn(cmd, "only Markdown files belong under commands/; each `name.md` becomes a command")
            continue
        report.commands_checked += 1
        try:
            content = cmd.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError) as e:
            report.error(cmd, f"could not read this command file: {e}")
            continue
        data, where, body, _, err = parse_frontmatter(content)
        if err:
            report.error(cmd, err[1], err[0])
            continue
        for key in data:
            if key not in TOP_LEVEL_FIELDS:
                report.warn(cmd, f"`{key}` is not one of the six fields a skill upload accepts ({', '.join(TOP_LEVEL_FIELDS)}); keep command files to the same set, so the plugin uploads anywhere skills do", where.get(key))
        desc = data.get("description")
        if not isinstance(desc, str) or not desc.strip():
            report.error(cmd, "`description` is missing; it is the line shown next to the command in the slash menu", 2)
        if not body.strip():
            report.error(cmd, "the command has no body; say what the assistant should do when it runs")


def check_folder(root: Path) -> Report:
    report = Report(root=root)
    check_folder_shape(root, report)
    check_commands(root, report)
    settings = load_settings(root, report)
    skills = load_skills(root, report)
    check_cross_skill(skills, report)
    check_languages(skills, settings, report)
    check_never_name(root, settings, report)
    check_org_block(root, skills, settings, report)
    return report


def render_text(report: Report, root: Path, quiet: bool, strict: bool) -> None:
    for f in report.findings:
        label = "ERROR" if f.level == "error" else "WARN "
        where = f"{f.path}:{f.line}" if f.line else f.path
        print(f"{label}  {where}: {f.message}", file=sys.stderr if f.level == "error" else sys.stdout)
    if quiet:
        return
    if report.findings:
        print()
    if not (root / "skills").is_dir():
        print(f"No skills folder yet in {root}; nothing to check there.")
    elif report.skills_checked == 0:
        print(f"The skills folder in {root} is empty; nothing to check yet.")
    print(f"Skills checked: {report.skills_checked}")
    if report.commands_checked:
        print(f"Commands:       {report.commands_checked}")
    if report.org_block_chars is not None:
        print(f"Org block:      {report.org_block_chars:,} of {report.org_block_cap:,} characters")
    print(f"Errors:         {len(report.errors)}")
    print(f"Warnings:       {len(report.warnings)}" + ("  (counted as errors with --strict)" if strict and report.warnings else ""))
    if report.errors or (strict and report.warnings):
        print("Fix the items above before building the plugin.")
    else:
        print("All clear.")


def render_json(report: Report) -> None:
    print(json.dumps({
        "skills_checked": report.skills_checked,
        "commands_checked": report.commands_checked,
        "org_block_chars": report.org_block_chars,
        "org_block_cap": report.org_block_cap,
        "errors": [f.__dict__ for f in report.errors],
        "warnings": [f.__dict__ for f in report.warnings],
    }, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check a company plugin folder before it is built.")
    parser.add_argument("root", nargs="?", default=".", help="the folder to check (default: the current folder)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--quiet", action="store_true", help="print findings only, no summary")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR  {args.root}: not a folder", file=sys.stderr)
        return 2

    report = check_folder(root)
    if args.json:
        render_json(report)
    else:
        render_text(report, root, args.quiet, args.strict)
    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    return 1 if failed else 0


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
