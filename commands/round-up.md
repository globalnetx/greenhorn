---
description: "Checks the folder and reports in plain words: broken pointers, overlapping skills, stale references, claims with no source."
allowed-tools: Read Edit Grep Glob WebFetch WebSearch Bash(python3 *) Bash(py *) Bash(python *) Bash(mkdir *)
---

Run Greenhorn's round-up mode: the checks and the audit report.

1. Read the Greenhorn skill in full:
   `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn/SKILL.md`. It holds the rules
   for every mode: looking at the folder first,
   and who decides what: the admin confirms the facts, the assistant
   writes the files and reads back what it wrote.
   Greenhorn's skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn`.
   Wherever the skill or its references write `${CLAUDE_SKILL_DIR}`,
   use that folder instead.
2. Then follow
   `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn/references/round-up.md` step by
   step.

What the admin typed after the command, if anything: $ARGUMENTS
