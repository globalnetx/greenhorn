#!/usr/bin/env python3
# Copyright 2026 GNX. Licensed under the Apache License, Version 2.0;
# see the LICENSE file in the Greenhorn repository,
# https://github.com/globalnetx/greenhorn.
"""
Stamp the organisation-instructions block in README.md with the current
fingerprint of what its Layer B restates: the conduct skill's checklist and
the house-rules skill's data list.

Run this after a person has reviewed the block in response to a change in
either. check_harness.py fails until the stamp matches, so
re-stamping records that the review happened. Re-running with nothing
changed is a no-op.

The hashing and the extraction are imported from check_harness.py, which
sits in the same folder, so the stamper and the checker can never compute
the fingerprint differently.

Usage (from wherever this file sits; in the Greenhorn repository that is
skills/greenhorn/scripts/):
    python3 stamp_org_instructions.py              # the current folder
    python3 stamp_org_instructions.py path/to/folder
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_harness as ch  # noqa: E402  (path set up just above)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Stamp the organisation-instructions block after review.")
    parser.add_argument("root", nargs="?", default=".", help="the folder whose README.md to stamp (default: the current folder)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    readme = root / "README.md"
    if not readme.is_file():
        print(f"No README.md in {root}.", file=sys.stderr)
        return 1
    text = readme.read_text(encoding="utf-8-sig")
    if ch.ORG_BLOCK_START not in text:
        print("README.md has no organisation-instructions block; nothing to stamp.")
        return 0

    skills = ch.load_skills(root)
    expected, problem = ch.org_block_fingerprint(skills)
    if problem:
        path, message = problem
        where = f"{path.relative_to(root)}: " if path is not None else ""
        print(f"Cannot stamp. {where}{message}.", file=sys.stderr)
        return 1
    stamp = f"<!-- ORG-INSTRUCTIONS:CONDUCT-HASH={expected} -->"
    head, rest = text.split(ch.ORG_BLOCK_START, 1)
    if ch.ORG_BLOCK_END in rest:
        region, tail = rest.split(ch.ORG_BLOCK_END, 1)
        tail = ch.ORG_BLOCK_END + tail
    else:
        region, tail = rest, ""
    if ch.ORG_HASH_RE.search(region):
        region = ch.ORG_HASH_RE.sub(stamp, region, count=1)
    else:
        region = f"\n{stamp}" + region
    new = head + ch.ORG_BLOCK_START + region + tail

    if new == text:
        print(f"The block is already stamped with the current fingerprint ({expected}).")
        return 0
    readme.write_text(new, encoding="utf-8")
    print(f"Stamped README.md with fingerprint {expected}.")
    return 0


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
