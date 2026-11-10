#!/usr/bin/env python3
# Copyright 2026 GNX. Licensed under the Apache License, Version 2.0;
# see the LICENSE file in the Greenhorn repository,
# https://github.com/globalnetx/greenhorn.
"""
Secret scanner for a company plugin folder, and for this repository.

Scans files for patterns that look like committed credentials: provider
tokens, private keys, and `key = value` assignments where the name of the
key suggests a secret. No external service, no third-party dependencies.

Usage (from wherever this file sits; in the Greenhorn repository that is
skills/greenhorn/scripts/):
    python3 scan_secrets.py            # scan the folder you are in (tracked files when it is a git repo); exit 1 on any finding
    python3 scan_secrets.py --json     # machine-readable output
    python3 scan_secrets.py path/...   # scan specific files or folders instead

Tuned to stay quiet on documentation: anything wrapped as an obvious
placeholder (`<your-api-key>`, `xxx`, `example`, `changeme`, an all-caps
variable name with no value) is allowed through.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


# With no arguments the scanner covers the folder it is run from, so it can
# be pointed at a company folder as easily as at this repository.
REPO_ROOT = Path.cwd()

# Files we never scan: binary or plainly outside our content surface.
# Font binaries are excluded deliberately (they'd otherwise survive only by
# failing UTF-8 decode); SVG stays in scope: it's text and part of the
# content surface.
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".ico", ".ttf", ".otf", ".woff", ".woff2"}
SKIP_DIR_PARTS = {".git", "node_modules", "__pycache__", ".venv"}
# This file documents secret patterns; it would otherwise self-flag.
SELF_FILE = Path(__file__).resolve()

# Strings whose presence in or near a match downgrades it to a placeholder.
# Kept conservative: a real secret usually doesn't contain these markers.
PLACEHOLDER_MARKERS = (
    "your-",
    "your_",
    "<",
    ">",
    "example",
    "placeholder",
    "changeme",
    "redacted",
    "xxxxx",
    "...",
    "dummy",
    "fake",
)

# Provider-specific shapes. These are the patterns most likely to indicate a
# real leak rather than illustrative text. Keep the list short and well-known
# to keep false-positive rate low.
PROVIDER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("AWS temporary access key id", re.compile(r"\bASIA[0-9A-Z]{16}\b")),
    ("GitHub personal access token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("GitHub OAuth token", re.compile(r"\bgho_[A-Za-z0-9]{36}\b")),
    ("GitHub app token", re.compile(r"\bghs_[A-Za-z0-9]{36}\b")),
    ("GitHub user-to-server token", re.compile(r"\bghu_[A-Za-z0-9]{36}\b")),
    ("GitHub refresh token", re.compile(r"\bghr_[A-Za-z0-9]{36}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("Slack webhook", re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]{20,}")),
    ("Bearer token in a header", re.compile(r"(?i)\bauthorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._\-+/=]{20,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe live key", re.compile(r"\bsk_live_[0-9a-zA-Z]{16,}\b")),
    ("Stripe restricted key", re.compile(r"\brk_live_[0-9a-zA-Z]{16,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b")),
    ("PEM private key block", re.compile(
        r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |PGP |ENCRYPTED )?PRIVATE KEY-----"
    )),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
]

# Generic shape: a key=value or key: "value" assignment where the key looks
# like a secret name. The value must be non-trivial and not look like a
# placeholder. Length floor keeps "TOKEN=x" out of the noise.
SECRET_KEY_NAMES = (
    r"api[_-]?key|secret|password|passwd|pwd|token|access[_-]?key|"
    r"private[_-]?key|client[_-]?secret|auth[_-]?token|bearer"
)
ASSIGNMENT_RE = re.compile(
    # The key may sit inside a longer name (DB_PASSWORD, apiKey) and may be
    # quoted, as in JSON; only letters on either side rule a match out.
    r"(?<![A-Za-z])(?P<key>(?:" + SECRET_KEY_NAMES + r"))(?![A-Za-z])"
    r"['\"]?\s*[:=]\s*"
    r"(?P<quote>['\"]?)"
    r"(?P<value>[A-Za-z0-9+/=_\-\.]{16,})"
    r"(?P=quote)",
    re.IGNORECASE,
)

# Passwords are often short and full of symbols, which the generic shape
# above lets through. A password-named key with a value of eight or more
# characters that mixes letters and digits is reported too.
PASSWORD_RE = re.compile(
    r"(?<![A-Za-z])(?P<key>password|passwd|pwd)(?![A-Za-z])"
    r"['\"]?\s*[:=]\s*"
    r"(?P<quote>['\"]?)"
    r"(?P<value>[^\s'\"]{8,})"
    r"(?P=quote)",
    re.IGNORECASE,
)

# user:password@host inside a connection string.
CONNECTION_RE = re.compile(r"\b[a-z][a-z0-9+.\-]*://[^\s:/@]+:(?P<value>[^\s@/]{6,})@")


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    snippet: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    not_text: list[str] = field(default_factory=list)


def _is_placeholder(value: str, line: str) -> bool:
    """Heuristic: does this look like documentation rather than a real secret?"""
    lower = value.lower()
    if any(marker in lower for marker in PLACEHOLDER_MARKERS):
        return True
    line_lower = line.lower()
    # If the surrounding line itself screams "example" or "placeholder", trust it.
    if "placeholder" in line_lower or "e.g." in line_lower or "example:" in line_lower:
        return True
    # All-character-class repeats (xxxxx, *****, ......) are obvious masks.
    if re.fullmatch(r"(.)\1{6,}", value):
        return True
    return False


def _scan_text(path: Path, text: str, report: Report) -> None:
    if path.resolve() == SELF_FILE:
        return
    if path.is_absolute():
        try:
            rel = path.relative_to(REPO_ROOT)
        except ValueError:
            rel = path
    else:
        rel = path
    for lineno, raw in enumerate(text.splitlines(), start=1):
        # Provider-specific patterns: high signal, never softened by placeholder check.
        for rule, pattern in PROVIDER_PATTERNS:
            for m in pattern.finditer(raw):
                report.findings.append(
                    Finding(str(rel), lineno, rule, _excerpt(raw, m.start(), m.end()))
                )
        # Generic key=value assignments: softer signal, allow placeholders through.
        for m in ASSIGNMENT_RE.finditer(raw):
            value = m.group("value")
            if _is_placeholder(value, raw):
                continue
            report.findings.append(
                Finding(
                    str(rel),
                    lineno,
                    f"suspicious assignment ({m.group('key').lower()}=...)",
                    _excerpt(raw, m.start("value"), m.end("value")),
                )
            )
        seen = {(f.line, f.snippet) for f in report.findings if f.path == str(rel)}
        for m in PASSWORD_RE.finditer(raw):
            value = m.group("value")
            if _is_placeholder(value, raw) or not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value)):
                continue
            excerpt = _excerpt(raw, m.start("value"), m.end("value"))
            if (lineno, excerpt) not in seen:
                report.findings.append(Finding(str(rel), lineno, f"suspicious assignment ({m.group('key').lower()}=...)", excerpt))
        for m in CONNECTION_RE.finditer(raw):
            value = m.group("value")
            if _is_placeholder(value, raw):
                continue
            report.findings.append(Finding(str(rel), lineno, "password inside a connection string", _excerpt(raw, m.start("value"), m.end("value"))))


def _excerpt(line: str, start: int, end: int, width: int = 80) -> str:
    """Return a compact view around the match, masking the matched value."""
    masked = line[:start] + "*" * (end - start) + line[end:]
    if len(masked) <= width:
        return masked
    half = width // 2
    pivot = (start + end) // 2
    lo = max(0, pivot - half)
    hi = min(len(masked), lo + width)
    return ("…" if lo > 0 else "") + masked[lo:hi] + ("…" if hi < len(masked) else "")


def _git_ls_files() -> list[Path]:
    """List tracked + untracked-but-not-ignored files via git, falling back to walk."""
    try:
        out = subprocess.check_output(
            # -z keeps names with accents or spaces intact; without it git
            # quotes them and the file would be skipped.
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return _walk(REPO_ROOT)
    paths = [REPO_ROOT / name.decode("utf-8", errors="surrogateescape") for name in out.split(b"\0") if name]
    return [p for p in paths if p.is_file()]


def _walk(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIR_PARTS for part in p.parts):
            continue
        out.append(p)
    return out


def _should_scan(path: Path) -> bool:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    if any(part in SKIP_DIR_PARTS for part in path.parts):
        return False
    return True


def _read_any_text(path: Path):
    """Text in any common encoding, or None for a binary or unreadable file.
    A secret is ASCII whatever the file's encoding, so a lossy read is fine."""
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            return None
    if b"\x00" in raw[:4096]:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def scan(paths: list[Path]) -> Report:
    report = Report()
    for path in paths:
        if not _should_scan(path):
            continue
        text = _read_any_text(path)
        if text is None:
            report.not_text.append(str(path))
            continue
        report.files_scanned += 1
        _scan_text(path, text, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repo for committed-secret-shaped strings")
    parser.add_argument("paths", nargs="*", help="paths to scan; defaults to git-tracked files")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    if args.paths:
        targets = []
        for p in args.paths:
            path = Path(p).resolve()
            if not path.exists():
                print(f"{p} does not exist; check the path.", file=sys.stderr)
                return 2
            targets.extend(_walk(path) if path.is_dir() else [path])
    else:
        targets = _git_ls_files()

    report = scan(targets)

    if args.json:
        print(json.dumps({
            "files_scanned": report.files_scanned,
            "findings": [f.__dict__ for f in report.findings],
        }, indent=2))
    else:
        for f in report.findings:
            print(f"SECRET  {f.path}:{f.line}: {f.rule}: {f.snippet}", file=sys.stderr)
        print(file=sys.stderr if report.findings else sys.stdout)
        print(f"Files scanned: {report.files_scanned}")
        if report.not_text:
            print(f"Not text, so not scanned: {len(report.not_text)}")
        print(f"Findings:      {len(report.findings)}")

    return 1 if report.findings else 0


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
