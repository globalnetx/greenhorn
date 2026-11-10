#!/usr/bin/env python3
# Copyright 2026 GNX. Licensed under the Apache License, Version 2.0;
# see the LICENSE file in the Greenhorn repository,
# https://github.com/globalnetx/greenhorn.
"""
Put a company folder under version control, safely.

Run from the company folder (or point it at one). It writes the files a
repository needs and nothing else: a `.gitignore` that keeps the
sensitive files out (the interview profile, the source documents, the
brand sources, built zips, local notes), a LICENSE note that defaults to
"proprietary, internal use only", a NOTICE crediting Greenhorn's
Apache-licensed templates, copies of Greenhorn's checker and secret
scanner under `tools/`, and a GitHub Actions workflow that runs both on
every push and pull request and stops, before either, when the
repository is public. Then it runs `git init` on a branch called
`main` and makes one first commit of everything the ignore list allows.

It refuses, writing nothing, when the folder is not a Greenhorn folder
(no harness-profile.md and no skills/), when it holds Greenhorn's own
source, when it is already a repository or sits inside one (unless
--force), when git is not installed, and when git has no name and email
to commit under.

Usage (from wherever this file sits; in the Greenhorn repository that is
skills/greenhorn/scripts/):
    python3 init_repo.py                    # the current folder
    python3 init_repo.py path/to/folder     # another folder
    python3 init_repo.py --dry-run          # say what would be written and committed; write nothing
    python3 init_repo.py --owner "Acme Kitchenware"   # the name in the licence note (default: plugin-author from harness.yaml)
    python3 init_repo.py --include harness-profile.md # commit a sensitive file anyway, after a scrub (repeatable)
    python3 init_repo.py --force            # inside an existing repository: refresh tools/ and the workflow, merge the ignore list
    python3 init_repo.py --replace-licence  # write the default LICENSE and NOTICE again (never done otherwise)
    python3 init_repo.py --self-test        # prove the refusals and the ignore list on throwaway folders

Both routes to a remote continue from here: GitHub Desktop (add the
folder, publish it private) or the command line. Nothing here talks to
GitHub. Exit codes: 0 done (or dry run), 1 refused with reasons printed,
2 unusable arguments.

Python 3.9 or newer, standard library only.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
GREENHORN_URL = "https://github.com/globalnetx/greenhorn"

# What never goes into the repository unless the admin decides otherwise
# (the skill's conventions reference, "What never leaves the computer").
SENSITIVE = [
    ("harness-profile.md", "the interview as answered: real names, real figures, the writing samples"),
    ("sources/", "the documents handed over during intake"),
    ("brand-sources/", "logo files, screenshots, brand PDFs as handed over"),
]
# Built output, local notes, and machine files: always ignored.
ALWAYS_IGNORED = [
    ("dist/", "built plugin zips"),
    ("*.zip", "any zip, including a build copied elsewhere"),
    ("local/", "local notes"),
    ("*.local.md", "local notes"),
    (".claude/settings.local.json", "one person's own tool settings"),
    ("__pycache__/", "Python's cache"),
    (".DS_Store", "the Mac's folder metadata"),
    ("Thumbs.db", "Windows' folder metadata"),
]
INCLUDABLE = [name for name, _ in SENSITIVE]

TOOLS_DIR = "tools"
TOOL_SCRIPTS = ("check_harness.py", "scan_secrets.py")
WORKFLOW_PATH = Path(".github") / "workflows" / "checks.yml"
# The same pinned actions Greenhorn's own workflow uses.
ACTION_CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"
ACTION_SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0"
MARKER = "written by Greenhorn's homestead mode"


@dataclass
class Plan:
    root: Path
    dry_run: bool
    ok: bool = True
    refusals: list = field(default_factory=list)   # (path or None, message)
    notes: list = field(default_factory=list)      # (path or None, message)
    writes: list = field(default_factory=list)     # (relative path, what)
    kept: list = field(default_factory=list)       # (relative path, why it was left alone)
    ignored: list = field(default_factory=list)    # (pattern, reason, present in folder?)
    committed: list = field(default_factory=list)  # relative paths in the first commit
    left_out: list = field(default_factory=list)   # relative paths present but not committed
    branch: str = "main"
    version: str = "unknown"
    written: list = field(default_factory=list)    # relative paths this run wrote
    backups: dict = field(default_factory=dict)    # relative path -> text before this run, or None if new
    created_repo: bool = False
    rolled_back: bool = False

    def refuse(self, path, message: str) -> None:
        self.ok = False
        self.refusals.append((self._rel(path), message))

    def note(self, path, message: str) -> None:
        self.notes.append((self._rel(path), message))

    def _rel(self, path) -> Optional[str]:
        if path is None:
            return None
        # Not resolved first: a link would resolve to wherever it points.
        for candidate, base in ((Path(path), self.root), (Path(path).resolve(), self.root.resolve())):
            try:
                return candidate.relative_to(base).as_posix()
            except ValueError:
                continue
        return str(path)


# --- Looking before writing --------------------------------------------------


def greenhorn_version() -> str:
    """The version in the skill's SKILL.md beside this scripts folder, or
    the plugin manifest two folders up; 'unknown' when neither is there."""
    skill_md = HERE.parent / "SKILL.md"
    if skill_md.is_file():
        try:
            text = skill_md.read_text(encoding="utf-8-sig")
        except OSError:
            text = ""
        m = re.search(r"^\s+version:\s*[\"']?([0-9][0-9A-Za-z.\-]*)[\"']?\s*$", text, re.MULTILINE)
        if m:
            return m.group(1)
    manifest = HERE.parent.parent.parent / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        try:
            import json
            return str(json.loads(manifest.read_text(encoding="utf-8-sig")).get("version", "unknown"))
        except (OSError, ValueError):
            pass
    return "unknown"


def _run_git(args: list, cwd: Path, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, env=env)


def _git_identity_known(root: Path) -> bool:
    env_keys = ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")
    if all(os.environ.get(k) for k in env_keys):
        return True
    for key in ("user.name", "user.email"):
        r = _run_git(["config", "--get", key], root)
        if r.returncode != 0 or not r.stdout.strip():
            return False
    return True


def _inside_repository(root: Path) -> Optional[Path]:
    """The repository root this folder sits in, when it does; None otherwise."""
    r = _run_git(["rev-parse", "--show-toplevel"], root)
    if r.returncode == 0 and r.stdout.strip():
        return Path(r.stdout.strip())
    return None


def _owner_from_settings(root: Path) -> Optional[str]:
    settings = root / "harness.yaml"
    if not settings.is_file():
        return None
    try:
        text = settings.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    m = re.search(r"^plugin-author:\s*(.+?)\s*$", text, re.MULTILINE)
    if not m:
        return None
    value = m.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value or None


def _owner_from_skills(root: Path) -> Optional[str]:
    skills = root / "skills"
    if not skills.is_dir():
        return None
    prefixes = {p.name.split("-", 1)[0] for p in skills.iterdir() if p.is_dir() and "-" in p.name}
    if len(prefixes) == 1:
        return prefixes.pop().capitalize()
    return None


def _remotes(root: Path) -> list:
    """Every distinct remote address of the repository `root` is in (fetch
    and push), without any sign-in details in it."""
    found: list = []
    for line in _run_git(["remote", "-v"], root).stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        address = re.sub(r"//[^/]*@", "//", parts[1])
        if address not in found:
            found.append(address)
    return found


def _remote_words(remotes: list) -> str:
    """One sentence about the remotes, or '' when there are none."""
    if not remotes:
        return ""
    return (" It already has a remote (" + ", ".join(remotes) + "): before anything is pushed there, read that repository's visibility, "
            "and stop if it is public (the homestead reference, \"Private, and nothing else\").")


def _tracked_under(root: Path) -> int:
    """How many files under `root` the enclosing repository already tracks."""
    r = _run_git(["ls-files", "--", "."], root)
    return len([line for line in r.stdout.splitlines() if line.strip()]) if r.returncode == 0 else 0


def look(root: Path, plan: Plan, force: bool) -> None:
    """Every refusal, before anything is written."""
    if not root.is_dir():
        plan.refuse(root, "not a folder")
        return
    has_profile = (root / "harness-profile.md").is_file()
    has_skills = (root / "skills").is_dir()
    if (root / "skills" / "greenhorn").is_dir():
        plan.refuse(root / "skills" / "greenhorn", "this folder holds Greenhorn's own skill; it is not a company folder. Run this from the company's AI folder")
        return
    if not has_profile and not has_skills:
        plan.refuse(root, "this is not a Greenhorn folder: it has neither harness-profile.md nor a skills/ folder. Run giddy-up here first, or point this at the company's AI folder")
        return
    if shutil.which("git") is None:
        plan.refuse(None, "git is not installed, or not on the path this session can see. On a Mac, open Terminal, type `git --version`, and accept the offer to install the command line tools. On Windows, install Git from https://git-scm.com/downloads. GitHub Desktop brings its own copy of Git for its own use, which is enough for the walkthrough afterwards, but this script needs one it can call. Then run this again")
        return
    if (root / ".git").exists():
        if force:
            plan.note(root / ".git", "already a repository; carrying on because of --force. The files are written or refreshed, and the first commit is skipped if there is history already")
            if _remotes(root):
                plan.note(root / ".git", "this repository is not new." + _remote_words(_remotes(root)))
        else:
            plan.refuse(root / ".git", "this folder is already a repository." + _remote_words(_remotes(root)) + " Nothing was changed. Run with --force to refresh the ignore list, the copies under tools/, and the workflow inside it; LICENSE and NOTICE stay as they are unless --replace-licence is given too")
            return
    else:
        parent = _inside_repository(root)
        if parent is not None:
            tracked = _tracked_under(root)
            outer = _remote_words(_remotes(root)).replace("It already has", "That repository has")
            if tracked:
                outer += f" {tracked} of this folder's files are already tracked in it, so they are wherever it has been pushed; if that place is public, treat them as seen."
            if force:
                plan.note(root, f"this folder sits inside the repository at {parent}; carrying on because of --force, as its own nested repository.{outer}")
            else:
                plan.refuse(root, f"this folder sits inside a repository already, the one at {parent}.{outer} A repository inside a repository is rarely what you want; move the folder out, or run with --force to make it its own")
                return
    if not _git_identity_known(root):
        plan.refuse(None, "git does not know your name and email yet, so it cannot make the first commit. Sign in to GitHub Desktop once, which sets them, or run `git config --global user.name \"Your Name\"` and `git config --global user.email \"you@example.com\"`. Then run this again")
        return
    for script in TOOL_SCRIPTS:
        if not (HERE / script).is_file():
            plan.refuse(HERE / script, f"Greenhorn's {script} is missing beside this script, so it cannot be copied into tools/. Reinstall Greenhorn, or run this from a complete copy of the skill")
    for rel in (Path(".gitignore"), WORKFLOW_PATH, Path("harness.yaml")):
        target = root / rel
        if target.is_file():
            try:
                target.read_text(encoding="utf-8-sig")
            except (OSError, ValueError):
                plan.refuse(target, "could not read this file as text; it has to be plain UTF-8 before the script can merge or read it")
    # A link is committed as a link: not its contents, and it reveals where
    # it points. A linked sources/ would also slip past the ignore list,
    # which matches folders, not links.
    for link in _symlinks(root):
        rel = link.relative_to(root)
        if _is_ignored_path(root, rel, includes_hint=None) == ".git":
            continue
        if rel.as_posix().rstrip("/") in [n.rstrip("/") for n, _ in SENSITIVE]:
            plan.refuse(link, "this is a link to another folder, and git would commit the link itself, not ignore it. Move or copy the real folder in, or leave it out")
        else:
            plan.refuse(link, "this is a link; git would commit the link, not what it points at, and the link shows where it points. Replace it with the real file or folder, or remove it")


# --- The files ---------------------------------------------------------------


def gitignore_text(includes: list) -> str:
    lines = [
        f"# {MARKER}. Keep what never leaves this computer out of the repository.",
        "# Lines you remove here are a decision; record it in harness-profile.md.",
        "",
        "# The sensitive files: real names, real figures, documents as handed over.",
    ]
    # A comment shares no line with a pattern: git reads "pattern  # note"
    # as a pattern that ends in "# note", and ignores nothing.
    for name, reason in SENSITIVE:
        if name in includes:
            lines.append(f"# {name}  committed on purpose, after a scrub: {reason}")
        else:
            lines.append(f"# {reason}")
            lines.append(name)
    lines += ["", "# Built output, local notes, machine files."]
    for name, reason in ALWAYS_IGNORED:
        lines.append(f"# {reason}")
        lines.append(name)
    return "\n".join(lines) + "\n"


def merge_gitignore(existing: str, wanted: str) -> str:
    """Keep the admin's lines; add ours that are missing."""
    have = {line.strip() for line in existing.splitlines() if line.strip() and not line.lstrip().startswith("#")}
    additions = []
    comment = None
    for line in wanted.splitlines():
        if line.startswith("#"):
            comment = line if not line.startswith("# written by") and not line.startswith("# Lines you") and not line.startswith("# The sensitive") and not line.startswith("# Built output") else None
            continue
        if not line.strip():
            comment = None
            continue
        if line.strip() not in have:
            if comment:
                additions.append(comment)
            additions.append(line)
        comment = None
    if not additions:
        return existing
    sep = "" if existing.endswith("\n") or not existing else "\n"
    return existing + sep + "\n# Added by Greenhorn's homestead mode.\n" + "\n".join(additions) + "\n"


def license_text(owner: str, year: int) -> str:
    return (
        f"Copyright {year} {owner}. All rights reserved.\n"
        "\n"
        f"This folder is {owner}'s own AI knowledge in source form: the skills,\n"
        "the house rules, the always-on instruction block, and everything\n"
        "written from the interview. It is proprietary and for internal use\n"
        f"only. Do not copy, publish, or share it outside {owner} without\n"
        f"{owner}'s permission.\n"
        "\n"
        "The scripts under tools/ and the layout of this folder come from\n"
        "Greenhorn and are under the Apache License, Version 2.0; see NOTICE.\n"
        "\n"
        "To put this folder under another licence, replace this file; nothing\n"
        "else refers to it.\n"
    )


def notice_text(owner: str, version: str, date: str) -> str:
    return (
        f"This folder was set up with Greenhorn {version} ({GREENHORN_URL}) on {date}.\n"
        "Greenhorn is licensed under the Apache License, Version 2.0.\n"
        "\n"
        "The scripts under tools/ are copies of Greenhorn's check_harness.py and\n"
        "scan_secrets.py and keep that licence; Greenhorn's homestead mode\n"
        "refreshes them. The layout of this folder, the shape of its skills, and\n"
        "the wording of its ignore list follow Greenhorn's templates.\n"
        "\n"
        f"Everything else here, the skills above all, belongs to {owner} and is\n"
        "covered by the LICENSE file beside this one.\n"
    )


def tool_header(script: str, version: str, date: str) -> str:
    return (
        "#!/usr/bin/env python3\n"
        f"# {script}: a copy of Greenhorn's {script}, Greenhorn version {version},\n"
        f"# placed here by Greenhorn's homestead mode on {date} so the checks can\n"
        "# run on every change to this folder (see .github/workflows/checks.yml).\n"
        "# Greenhorn refreshes this copy; do not edit it here. Apache License 2.0,\n"
        f"# see NOTICE. Source: {GREENHORN_URL}\n"
    )


def tool_text(script: str, version: str, date: str) -> str:
    original = (HERE / script).read_text(encoding="utf-8-sig")
    body = original
    if body.startswith("#!"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    return tool_header(script, version, date) + body


def workflow_text() -> str:
    return f"""# Checks for this folder: {MARKER}.
# Runs Greenhorn's checker (strict, so warnings fail too) and its secret
# scanner on every push and pull request, from the copies under tools/.
# A red cross on a commit means one of them found something; open the
# run under the Actions tab to read it in plain words, with file and line.
#
# The first step fails when this repository is public. The skills
# describe how the company works, so it must not be; this is the backstop
# for a repository published the wrong way by accident. It runs on a push
# or a pull request, not by itself.

name: Checks

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  checks:
    name: Check the skills and scan for secrets
    runs-on: ubuntu-latest
    steps:
      - name: Stop if this repository is public
        env:
          GH_TOKEN: ${{{{ github.token }}}}
          WAS_PRIVATE: ${{{{ github.event.repository.private }}}}
        run: |
          # Ask GitHub what the visibility is now. If that gets no clear
          # answer, go by what it was when this run was triggered.
          visibility="$(gh api "repos/$GITHUB_REPOSITORY" --jq .visibility 2>/dev/null || true)"
          case "$visibility" in
            public|private|internal) ;;
            *) if [ "$WAS_PRIVATE" = "true" ]; then visibility="private"; else visibility="public"; fi ;;
          esac
          if [ "$visibility" = "public" ]; then
            echo "::error::This repository is public. It holds how the company works, so it must not be. Make it private now: Settings, General, Danger Zone, Change repository visibility. Then re-run this check."
            exit 1
          fi
          echo "Visibility: $visibility."
      - uses: {ACTION_CHECKOUT}
      - uses: {ACTION_SETUP_PYTHON}
        with:
          python-version: "3.11"
      - name: Check the folder (strict)
        run: python3 tools/check_harness.py --strict
      - name: Scan for anything that looks like a secret
        run: python3 tools/scan_secrets.py
"""


# --- Doing it -----------------------------------------------------------------


def _git_env() -> dict:
    env = dict(os.environ)
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    return env


def _is_ignored_path(root: Path, rel: Path, includes: Optional[list] = None, includes_hint: Optional[list] = None) -> Optional[str]:
    """The ignore pattern a path in the folder falls under, for the dry run."""
    includes = includes if includes is not None else (includes_hint or [])
    parts = rel.parts
    if parts and parts[0] == ".git":
        return ".git"
    for name, _ in SENSITIVE + ALWAYS_IGNORED:
        if name in includes:
            continue
        if name.endswith("/") and name[:-1] in parts[:-1]:
            return name
        if name.startswith("*.") and rel.name.endswith(name[1:]):
            return name
        if "/" in name.rstrip("/"):
            if rel.as_posix() == name:
                return name
        elif not name.endswith("/") and rel.name == name:
            return name
    return None


def _walk(root: Path) -> list:
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        d = Path(dirpath)
        if d.name == ".git" and d.parent == root:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(dn for dn in dirnames if dn != ".git" or d != root)
        for fn in sorted(filenames):
            out.append((d / fn).relative_to(root))
    return sorted(out)


def _symlinks(root: Path) -> list:
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        d = Path(dirpath)
        if d == root:
            dirnames[:] = [dn for dn in dirnames if dn != ".git"]
        for name in list(dirnames) + filenames:
            if (d / name).is_symlink():
                out.append(d / name)
    return sorted(out)


def prepare(root: Path, plan: Plan, owner: Optional[str], includes: list, force: bool, replace_licence: bool = False) -> dict:
    """Decide every file's text. Returns {relative path: text}."""
    today = datetime.date.today().isoformat()
    year = datetime.date.today().year
    plan.version = greenhorn_version()
    owner = owner or _owner_from_settings(root) or _owner_from_skills(root) or "the company"
    files = {}

    gi = root / ".gitignore"
    wanted = gitignore_text(includes)
    if gi.is_file():
        existing = gi.read_text(encoding="utf-8-sig")
        merged = merge_gitignore(existing, wanted)
        if merged == existing:
            plan.kept.append((".gitignore", "already has every line it needs"))
        else:
            files[".gitignore"] = merged
            plan.writes.append((".gitignore", "kept your lines, added the ones that were missing"))
    else:
        files[".gitignore"] = wanted
        plan.writes.append((".gitignore", "what stays out of the repository"))

    for name, text, what in (
        ("LICENSE", license_text(owner, year), f"proprietary, internal use only, in {owner}'s name"),
        ("NOTICE", notice_text(owner, plan.version, today), "credits Greenhorn's Apache-licensed templates and tools"),
    ):
        target = root / name
        if target.exists() and not replace_licence:
            plan.kept.append((name, "already there; left as it is, --force included (--replace-licence writes the default again)"))
        else:
            files[name] = text
            plan.writes.append((name, what))

    for script in TOOL_SCRIPTS:
        rel = f"{TOOLS_DIR}/{script}"
        files[rel] = tool_text(script, plan.version, today)
        plan.writes.append((rel, f"copy of Greenhorn's {script}, version {plan.version}; refreshed each time homestead runs"))

    wf = root / WORKFLOW_PATH
    wf_rel = WORKFLOW_PATH.as_posix()
    if wf.is_file() and MARKER not in wf.read_text(encoding="utf-8", errors="replace") and not force:
        plan.kept.append((wf_rel, "a workflow that is not ours; left as it is (--force replaces it). Until then nothing on GitHub checks the skills, or that the repository is not public"))
    else:
        files[wf_rel] = workflow_text()
        plan.writes.append((wf_rel, "runs the checker and the secret scanner on every push and pull request"))

    # What the ignore list keeps out, and whether any of it is present.
    present = _walk(root)
    for name, reason in SENSITIVE + ALWAYS_IGNORED:
        if name in includes:
            continue
        hit = any(_is_ignored_path(root, rel, includes) == name for rel in present)
        plan.ignored.append((name, reason, hit))
    for name in includes:
        plan.note(root / name, "committed on purpose, as you decided; the ignore list says so in a comment")

    # The first commit, predicted: everything present or about to be
    # written that no pattern catches.
    all_rel = {rel.as_posix() for rel in present} | set(files)
    for rel in sorted(all_rel):
        pattern = _is_ignored_path(root, Path(rel), includes)
        if pattern is None:
            plan.committed.append(rel)
        elif pattern != ".git":
            plan.left_out.append(rel)
    return files


def write_files(root: Path, files: dict, plan: Plan) -> None:
    for rel, text in files.items():
        target = root / rel
        plan.backups[rel] = target.read_text(encoding="utf-8-sig") if target.is_file() else None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        plan.written.append(rel)


def roll_back(root: Path, plan: Plan) -> None:
    """Undo this run's writes and the repository it created, so a refusal
    after writing still leaves the folder as it was."""
    for rel in reversed(plan.written):
        target = root / rel
        before = plan.backups.get(rel)
        if before is None:
            if target.exists():
                target.unlink()
            for parent in (target.parent, target.parent.parent):
                if parent != root and parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()
        else:
            target.write_text(before, encoding="utf-8")
    if plan.created_repo and (root / ".git").is_dir():
        shutil.rmtree(root / ".git")
    plan.written = []
    plan.rolled_back = True


def init_and_commit(root: Path, plan: Plan, includes: list) -> None:
    env = _git_env()
    if not (root / ".git").exists():
        plan.created_repo = True
        r = _run_git(["init", "-b", plan.branch], root, env)
        if r.returncode != 0:
            # Older git has no -b; init, then point HEAD at main.
            r = _run_git(["init"], root, env)
            if r.returncode != 0:
                plan.refuse(root, f"git init failed: {r.stderr.strip() or r.stdout.strip()}")
                roll_back(root, plan)
                return
            _run_git(["symbolic-ref", "HEAD", f"refs/heads/{plan.branch}"], root, env)
    has_history = _run_git(["rev-parse", "--verify", "HEAD"], root, env).returncode == 0
    if has_history:
        plan.note(root, "the repository has commits already, so no first commit was made; commit the refreshed files the usual way")
        return
    r = _run_git(["add", "-A"], root, env)
    if r.returncode != 0:
        plan.refuse(root, f"git add failed: {r.stderr.strip()}")
        roll_back(root, plan)
        return
    staged = [line for line in _run_git(["diff", "--cached", "--name-only"], root, env).stdout.splitlines() if line.strip()]
    # The one check that matters: nothing sensitive is staged.
    leaked = [s for s in staged if _is_ignored_path(root, Path(s), includes) not in (None, ".git")]
    if leaked:
        _run_git(["reset"], root, env)
        plan.refuse(root, "these files were about to be committed although the ignore list should keep them out: " + ", ".join(leaked) + ". Usually a line in .gitignore un-ignores one of them (a line starting with `!`). Nothing was committed, and the folder was put back as it was; fix .gitignore and run again")
        roll_back(root, plan)
        return
    message = "Put the folder under version control\n\nIgnore list, licence note, Greenhorn's checks under tools/, and the\nworkflow that runs them on every change."
    r = _run_git(["commit", "-q", "-m", message], root, env)
    if r.returncode != 0:
        plan.refuse(root, f"the first commit failed: {r.stderr.strip() or r.stdout.strip()}. The folder was put back as it was")
        roll_back(root, plan)
        return
    plan.committed = sorted(staged)
    present = _walk(root)
    plan.left_out = sorted(rel.as_posix() for rel in present if _is_ignored_path(root, rel, includes) not in (None, ".git"))


def run(root: Path, dry_run: bool = False, force: bool = False, owner: Optional[str] = None, includes: Optional[list] = None, replace_licence: bool = False) -> Plan:
    includes = list(includes or [])
    plan = Plan(root=root, dry_run=dry_run)
    bad = [i for i in includes if i not in INCLUDABLE]
    if bad:
        plan.refuse(None, "--include only takes " + ", ".join(INCLUDABLE) + "; not " + ", ".join(bad))
        return plan
    look(root, plan, force)
    if not plan.ok:
        return plan
    files = prepare(root, plan, owner, includes, force, replace_licence)
    if dry_run:
        return plan
    write_files(root, files, plan)
    init_and_commit(root, plan, includes)
    return plan


# --- Saying it ---------------------------------------------------------------------


def render(plan: Plan) -> None:
    out, err = sys.stdout, sys.stderr
    for path, message in plan.refusals:
        print(f"REFUSED  {path + ': ' if path else ''}{message}", file=err)
    for path, message in plan.notes:
        print(f"NOTE  {path + ': ' if path else ''}{message}", file=out)
    if not plan.ok:
        print(file=err)
        if plan.rolled_back:
            print("The files were written and then taken back, and the repository removed: the folder is as it was.", file=err)
        else:
            print("Nothing was written.", file=err)
        return

    verb = "Would write" if plan.dry_run else "Wrote"
    print(f"{verb} ({len(plan.writes)} files):")
    width = max((len(p) for p, _ in plan.writes), default=0)
    for path, what in plan.writes:
        print(f"  {path.ljust(width)}  {what}")
    if plan.kept:
        print()
        print("Left alone:")
        width = max(len(p) for p, _ in plan.kept)
        for path, why in plan.kept:
            print(f"  {path.ljust(width)}  {why}")
    print()
    print("Stays out of the repository (.gitignore):")
    width = max(len(n) for n, _, _ in plan.ignored)
    for name, reason, hit in plan.ignored:
        tag = "present" if hit else "not here yet"
        print(f"  {name.ljust(width)}  {reason} ({tag})")
    print()
    if plan.dry_run:
        print(f"Dry run: would run git init on `{plan.branch}` and commit {len(plan.committed)} files. Nothing was written.")
    else:
        print(f"Repository: branch `{plan.branch}`, first commit with {len(plan.committed)} files.")
    if plan.left_out:
        print(f"Kept out of the commit ({len(plan.left_out)} files): " + ", ".join(plan.left_out[:8]) + (" ..." if len(plan.left_out) > 8 else ""))
    print()
    print("Next: GitHub Desktop (File, Add Local Repository, then Publish repository with \"Keep this code private\" ticked), or the command line. Private, always: the homestead reference walks through both routes and reads the visibility back before anyone is invited.")


# --- Self-test ----------------------------------------------------------------------


def _make_folder(root: Path, with_profile: bool = True, with_skills: bool = True) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if with_profile:
        (root / "harness-profile.md").write_text("# Harness profile: Acme\n\n- Maintainer: A. Person [you said]\n", encoding="utf-8")
    if with_skills:
        skill = root / "skills" / "acme-compass"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: acme-compass\ndescription: \"Use this skill when the conversation involves Acme as a company, its services, or its customers.\"\nmetadata:\n  version: 0.1.0\n---\n\n# Acme compass\n\nAcme sells kitchenware to shops across Europe.\n",
            encoding="utf-8")
    (root / "README.md").write_text("# Acme: the assistant's knowledge\n\nAcme sells kitchenware.\n", encoding="utf-8")
    (root / "harness.yaml").write_text("instruction-language: en\nplugin-author: \"Acme Kitchenware\"\n", encoding="utf-8")
    (root / "HOUSE-RULES.md").write_text("# House rules\n", encoding="utf-8")
    (root / "sources").mkdir()
    (root / "sources" / "handbook.pdf").write_bytes(b"%PDF-1.4 not really")
    (root / "brand-sources").mkdir()
    (root / "brand-sources" / "logo.png").write_bytes(b"\x89PNG not really")
    (root / "dist").mkdir()
    (root / "dist" / "acme-v0.1.0.zip").write_bytes(b"PK not really")
    (root / "local").mkdir()
    (root / "local" / "notes.md").write_text("private\n", encoding="utf-8")
    (root / "ideas.local.md").write_text("private\n", encoding="utf-8")
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (root / ".claude" / "settings.local.json").write_text("{}\n", encoding="utf-8")
    (root / ".DS_Store").write_bytes(b"\x00")


def _tracked(root: Path) -> list:
    return sorted(line for line in _run_git(["ls-files"], root).stdout.splitlines() if line.strip())


def self_test() -> int:
    passed = []

    def case(name: str, condition: bool, detail: str = "") -> None:
        if not condition:
            raise AssertionError(f"{name}: {detail}")
        passed.append(name)

    if shutil.which("git") is None:
        print("Self-test needs git on the path.", file=sys.stderr)
        return 1

    # A clean identity for the test commits, whatever this machine has.
    saved = {k: os.environ.get(k) for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "HOME", "XDG_CONFIG_HOME", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "PATH")}
    try:
        with tempfile.TemporaryDirectory(prefix="greenhorn-initrepo-") as tmp:
            base = Path(tmp)
            os.environ["GIT_CONFIG_GLOBAL"] = str(base / "no-global-gitconfig")
            os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
            os.environ["GIT_AUTHOR_NAME"] = os.environ["GIT_COMMITTER_NAME"] = "Self Test"
            os.environ["GIT_AUTHOR_EMAIL"] = os.environ["GIT_COMMITTER_EMAIL"] = "self-test@example.invalid"

            # 1. Not a Greenhorn folder.
            empty = base / "empty"
            empty.mkdir()
            p = run(empty)
            case("empty folder refused", not p.ok and any("not a Greenhorn folder" in m for _, m in p.refusals), str(p.refusals))
            case("refusal writes nothing", not (empty / ".gitignore").exists() and not (empty / ".git").exists())

            # 2. Greenhorn's own source.
            own = base / "own"
            (own / "skills" / "greenhorn").mkdir(parents=True)
            p = run(own)
            case("greenhorn source refused", not p.ok and any("Greenhorn's own skill" in m for _, m in p.refusals), str(p.refusals))

            # 3. A dry run writes nothing and predicts the commit.
            dry = base / "dry"
            _make_folder(dry)
            before = sorted(x.relative_to(dry).as_posix() for x in dry.rglob("*"))
            p = run(dry, dry_run=True)
            case("dry run ok", p.ok, str(p.refusals))
            after = sorted(x.relative_to(dry).as_posix() for x in dry.rglob("*"))
            case("dry run writes nothing", before == after and not (dry / ".git").exists(), str(set(after) - set(before)))
            case("dry run names the writes", {w for w, _ in p.writes} == {".gitignore", "LICENSE", "NOTICE", "tools/check_harness.py", "tools/scan_secrets.py", ".github/workflows/checks.yml"}, str(p.writes))
            case("dry run predicts the commit", "skills/acme-compass/SKILL.md" in p.committed and "README.md" in p.committed and "harness-profile.md" not in p.committed and "sources/handbook.pdf" not in p.committed, str(p.committed))
            case("dry run shows what is present", any(n == "harness-profile.md" and hit for n, _, hit in p.ignored) and any(n == "Thumbs.db" and not hit for n, _, hit in p.ignored), str(p.ignored))

            # 4. The real thing: files, init on main, first commit without the sensitive files.
            real = base / "real"
            _make_folder(real)
            p = run(real)
            case("init succeeds", p.ok, str(p.refusals))
            case("on main", _run_git(["symbolic-ref", "--short", "HEAD"], real).stdout.strip() == "main")
            tracked = _tracked(real)
            for must in ("skills/acme-compass/SKILL.md", "README.md", "HOUSE-RULES.md", "harness.yaml", ".gitignore", "LICENSE", "NOTICE", "tools/check_harness.py", "tools/scan_secrets.py", ".github/workflows/checks.yml", ".claude/settings.json"):
                case(f"commit holds {must}", must in tracked, str(tracked))
            for never in ("harness-profile.md", "sources/handbook.pdf", "brand-sources/logo.png", "dist/acme-v0.1.0.zip", "local/notes.md", "ideas.local.md", ".claude/settings.local.json", ".DS_Store"):
                case(f"commit keeps out {never}", never not in tracked, str(tracked))
            case("sensitive files still on disk", (real / "harness-profile.md").is_file() and (real / "sources" / "handbook.pdf").is_file())
            ignore = (real / ".gitignore").read_text(encoding="utf-8-sig")
            for pattern in ("harness-profile.md", "sources/", "brand-sources/", "dist/", "*.zip", "local/", "*.local.md", ".claude/settings.local.json", "__pycache__/", ".DS_Store"):
                case(f"ignore list has {pattern}", re.search(r"^" + re.escape(pattern) + r"$", ignore, re.MULTILINE) is not None, ignore)
            lic = (real / "LICENSE").read_text(encoding="utf-8-sig")
            case("licence is proprietary in the owner's name", "Acme Kitchenware" in lic and "internal use" in lic and "Apache" in lic, lic)
            notice = (real / "NOTICE").read_text(encoding="utf-8-sig")
            case("notice credits Greenhorn", "Greenhorn" in notice and "Apache License" in notice and GREENHORN_URL in notice, notice)
            tool = (real / "tools" / "check_harness.py").read_text(encoding="utf-8-sig")
            case("tool copy carries the header", tool.startswith("#!/usr/bin/env python3\n# check_harness.py: a copy of Greenhorn's check_harness.py, Greenhorn version") and "homestead" in tool.splitlines()[2], tool[:300])
            case("tool copy is runnable", subprocess.run([sys.executable, "-I", str(real / "tools" / "check_harness.py"), "--strict", str(real)], capture_output=True, text=True).returncode == 0, "checker failed on the test folder")
            case("scanner copy is runnable", subprocess.run([sys.executable, "-I", str(real / "tools" / "scan_secrets.py")], cwd=str(real), capture_output=True, text=True).returncode == 0, "scanner failed on the test folder")
            wf = (real / WORKFLOW_PATH).read_text(encoding="utf-8-sig")
            case("workflow runs both checks strictly", "tools/check_harness.py --strict" in wf and "tools/scan_secrets.py" in wf and "pull_request:" in wf and "push:" in wf, wf)
            gate, checkout = wf.find("WAS_PRIVATE: ${{ github.event.repository.private }}"), wf.find("actions/checkout@")
            case("workflow stops first when the repository is public", 0 < gate < checkout and 'gh api "repos/$GITHUB_REPOSITORY" --jq .visibility' in wf and "GH_TOKEN: ${{ github.token }}" in wf and 'if [ "$visibility" = "public" ]; then' in wf and "exit 1" in wf, wf)
            log = _run_git(["log", "--oneline"], real).stdout.strip().splitlines()
            case("exactly one commit", len(log) == 1, str(log))
            case("working tree clean", _run_git(["status", "--porcelain"], real).stdout.strip() == "")

            # 5. Already a repository: refused, then refreshed with --force,
            # which leaves a re-licensed LICENSE alone.
            p = run(real)
            case("existing repository refused", not p.ok and any("already a repository" in m for _, m in p.refusals), str(p.refusals))
            (real / "tools" / "check_harness.py").write_text("# stale\n", encoding="utf-8")
            (real / "LICENSE").write_text("MIT, as the company decided\n", encoding="utf-8")
            p = run(real, force=True)
            case("force refreshes the tools", p.ok and "Greenhorn version" in (real / "tools" / "check_harness.py").read_text(encoding="utf-8-sig"), str(p.refusals))
            case("force keeps the company's licence", (real / "LICENSE").read_text(encoding="utf-8-sig") == "MIT, as the company decided\n" and any(k == "LICENSE" for k, _ in p.kept), str(p.kept))
            p = run(real, force=True, replace_licence=True)
            case("replace-licence writes the default again", p.ok and "All rights reserved" in (real / "LICENSE").read_text(encoding="utf-8-sig"), str(p.refusals))
            case("force makes no second first commit", len(_run_git(["log", "--oneline"], real).stdout.strip().splitlines()) == 1 and any("commits already" in m for _, m in p.notes), str(p.notes))
            case("no remote, no remote note", not any("already has a remote" in m for _, m in p.notes), str(p.notes))
            signed_in = "https://" + "someone" + ":" + "sign-in@detail" + "@" + "example.invalid/acme/acme-ai.git"
            _run_git(["remote", "add", "origin", signed_in], real)
            _run_git(["remote", "add", "backup", "git@example.invalid:acme/backup.git"], real)
            p = run(real, dry_run=True, force=True)
            case("existing remotes are all named, for the private check", any("https://example.invalid/acme/acme-ai.git" in m and "git@example.invalid:acme/backup.git" in m and "visibility" in m for _, m in p.notes), str(p.notes))
            case("the remote note carries no sign-in details", not any("detail" in m or "someone" in m for _, m in p.notes), str(p.notes))
            p = run(real, dry_run=True)
            case("the plain refusal names the remotes too", not p.ok and any("already a repository" in m and "https://example.invalid/acme/acme-ai.git" in m for _, m in p.refusals), str(p.refusals))
            _run_git(["remote", "remove", "backup"], real)
            _run_git(["remote", "remove", "origin"], real)

            # 6. Inside a parent repository: refused without --force.
            nested = real / "nested"
            _make_folder(nested)
            p = run(nested)
            case("nested folder refused", not p.ok and any("inside a repository" in m for _, m in p.refusals), str(p.refusals))
            case("untracked nested folder says nothing about tracked files", not any("already tracked" in m for _, m in p.refusals), str(p.refusals))
            _run_git(["remote", "add", "origin", "https://example.invalid/acme/website.git"], real)
            _run_git(["add", "nested"], real)
            p = run(nested)
            case("nested folder names the outer remote and the tracked files", not p.ok and any("https://example.invalid/acme/website.git" in m and "already tracked" in m for _, m in p.refusals), str(p.refusals))
            _run_git(["rm", "-r", "-q", "--cached", "nested"], real)
            _run_git(["remote", "remove", "origin"], real)

            # 7. An existing .gitignore is merged, not replaced.
            merged = base / "merged"
            _make_folder(merged)
            (merged / ".gitignore").write_text("*.bak\nsources/\n", encoding="utf-8")
            p = run(merged)
            text = (merged / ".gitignore").read_text(encoding="utf-8-sig")
            case("gitignore merged", p.ok and text.startswith("*.bak\nsources/\n") and "harness-profile.md" in text and len(re.findall(r"^sources/$", text, re.MULTILINE)) == 1, text)
            case("merged list still keeps the profile out", "harness-profile.md" not in _tracked(merged))

            # 8. --include commits the profile on purpose and says so.
            inc = base / "include"
            _make_folder(inc)
            p = run(inc, includes=["harness-profile.md"])
            case("include commits the profile", p.ok and "harness-profile.md" in _tracked(inc) and "sources/handbook.pdf" not in _tracked(inc), str(p.refusals))
            case("include is recorded in the ignore file", "# harness-profile.md  committed on purpose" in (inc / ".gitignore").read_text(encoding="utf-8-sig"))
            p = run(base / "include2", includes=["README.md"])
            case("include outside the list refused", not p.ok and any("--include only takes" in m for _, m in p.refusals), str(p.refusals))

            # 9. Existing LICENSE and foreign workflow are left alone.
            keep = base / "keep"
            _make_folder(keep)
            (keep / "LICENSE").write_text("MIT, as it happens\n", encoding="utf-8")
            (keep / WORKFLOW_PATH).parent.mkdir(parents=True)
            (keep / WORKFLOW_PATH).write_text("name: Theirs\n", encoding="utf-8")
            p = run(keep)
            case("existing licence kept", p.ok and (keep / "LICENSE").read_text(encoding="utf-8-sig") == "MIT, as it happens\n" and any(k == "LICENSE" for k, _ in p.kept), str(p.kept))
            case("foreign workflow kept", (keep / WORKFLOW_PATH).read_text(encoding="utf-8-sig") == "name: Theirs\n" and any(k == WORKFLOW_PATH.as_posix() for k, _ in p.kept), str(p.kept))

            # 10. No git identity: refused before anything is written.
            noid = base / "noid"
            _make_folder(noid)
            for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL"):
                os.environ.pop(k, None)
            p = run(noid)
            case("missing identity refused", not p.ok and any("name and email" in m for _, m in p.refusals) and not (noid / ".gitignore").exists(), str(p.refusals))
            os.environ["GIT_AUTHOR_NAME"] = "Self Test"
            os.environ["GIT_AUTHOR_EMAIL"] = "self-test@example.invalid"

            # 11. No git at all: the refusal says where to get one.
            nogit = base / "nogit"
            _make_folder(nogit)
            os.environ["PATH"] = str(base / "empty-path")
            p = run(nogit)
            os.environ["PATH"] = saved["PATH"] or ""
            case("missing git refused with directions", not p.ok and any("git is not installed" in m and "GitHub Desktop" in m for _, m in p.refusals) and not (nogit / ".gitignore").exists(), str(p.refusals))

            # 12. A folder with skills/ but no profile still counts.
            noprof = base / "noprofile"
            _make_folder(noprof, with_profile=False)
            p = run(noprof, dry_run=True)
            case("skills without profile accepted", p.ok, str(p.refusals))

            # 13. A refusal after writing puts the folder back as it was.
            undo = base / "undo"
            _make_folder(undo)
            (undo / ".gitignore").write_text("harness-profile.md\n!harness-profile.md\n", encoding="utf-8")
            before = sorted(x.relative_to(undo).as_posix() for x in undo.rglob("*"))
            p = run(undo)
            after = sorted(x.relative_to(undo).as_posix() for x in undo.rglob("*"))
            case("un-ignored profile refused", not p.ok and any("about to be committed" in m for _, m in p.refusals), str(p.refusals))
            case("refusal after writing rolls back", p.rolled_back and before == after and not (undo / ".git").exists() and (undo / ".gitignore").read_text(encoding="utf-8-sig") == "harness-profile.md\n!harness-profile.md\n", str(sorted(set(after) ^ set(before))))

            # 14. A linked sources/ is refused before anything is written.
            linked = base / "linked"
            _make_folder(linked)
            shutil.rmtree(linked / "sources")
            (base / "shared-drive").mkdir()
            (linked / "sources").symlink_to(base / "shared-drive")
            p = run(linked, dry_run=True)
            case("linked sources refused", not p.ok and any("link" in m for p_, m in p.refusals if p_ == "sources"), str(p.refusals))
            case("link refusal writes nothing", not (linked / ".gitignore").exists())

            # 15. The dry run predicts nested matches the way git ignores them.
            nested2 = base / "nested2"
            _make_folder(nested2)
            (nested2 / "backup").mkdir()
            (nested2 / "backup" / "harness-profile.md").write_text("copy\n", encoding="utf-8")
            (nested2 / "notes" / "sources").mkdir(parents=True)
            (nested2 / "notes" / "sources" / "x.pdf").write_bytes(b"x")
            p = run(nested2, dry_run=True)
            case("nested matches predicted ignored", "backup/harness-profile.md" in p.left_out and "notes/sources/x.pdf" in p.left_out, str(p.left_out))
            p = run(nested2)
            case("nested matches ignored by git too", p.ok and "backup/harness-profile.md" not in _tracked(nested2) and "notes/sources/x.pdf" not in _tracked(nested2), str(_tracked(nested2)))

            # 16. An unreadable .gitignore is a plain refusal, not a traceback.
            binary = base / "binary"
            _make_folder(binary)
            (binary / ".gitignore").write_bytes(b"\xff\xfe*.bak\n")
            p = run(binary, dry_run=True)
            case("binary gitignore refused plainly", not p.ok and any("as text" in m for _, m in p.refusals), str(p.refusals))

            # 17. Author variables alone are not an identity.
            half = base / "half"
            _make_folder(half)
            os.environ.pop("GIT_COMMITTER_NAME", None)
            os.environ.pop("GIT_COMMITTER_EMAIL", None)
            p = run(half)
            case("author-only identity refused", not p.ok and any("name and email" in m for _, m in p.refusals), str(p.refusals))
            os.environ["GIT_COMMITTER_NAME"] = "Self Test"
            os.environ["GIT_COMMITTER_EMAIL"] = "self-test@example.invalid"
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    print(f"Self-test: {len(passed)} cases passed.")
    return 0


# --- Driver ----------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Put a company folder under version control, with the sensitive files kept out.")
    parser.add_argument("root", nargs="?", default=".", help="the company folder (default: the current folder)")
    parser.add_argument("--dry-run", action="store_true", help="say what would be written and committed; write nothing")
    parser.add_argument("--owner", metavar="NAME", help="the name in the licence note (default: plugin-author from harness.yaml)")
    parser.add_argument("--include", action="append", default=[], metavar="FILE", help="commit one of the sensitive files anyway, after a scrub: " + ", ".join(INCLUDABLE) + " (repeatable)")
    parser.add_argument("--force", action="store_true", help="carry on inside an existing repository: refresh tools/ and the workflow, merge the ignore list; LICENSE and NOTICE are left alone")
    parser.add_argument("--replace-licence", action="store_true", help="write the default LICENSE and NOTICE again even when they exist (they are otherwise never overwritten)")
    parser.add_argument("--self-test", action="store_true", help="prove the refusals and the ignore list on throwaway folders and exit")
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
    try:
        plan = run(root, dry_run=args.dry_run, force=args.force, owner=args.owner, includes=args.include, replace_licence=args.replace_licence)
    except (OSError, ValueError) as e:
        print(f"REFUSED  {e}", file=sys.stderr)
        return 1
    render(plan)
    return 0 if plan.ok else 1


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
