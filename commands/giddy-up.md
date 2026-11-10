---
description: "The first run. Reads your website, takes your documents, interviews you, and builds the first version of your company's AI skills."
allowed-tools: Read Edit Grep Glob WebFetch WebSearch Bash(python3 *) Bash(py *) Bash(python *) Bash(mkdir *)
---

Run Greenhorn's giddy-up mode: the first run.

1. Read the Greenhorn skill in full:
   `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn/SKILL.md`. It holds the rules
   for every mode: looking at the folder first,
   and who decides what: the admin confirms the facts, the assistant
   writes the files and reads back what it wrote.
   Greenhorn's skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn`.
   Wherever the skill or its references write `${CLAUDE_SKILL_DIR}`,
   use that folder instead.
2. Then follow
   `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn/references/giddy-up.md` step by
   step. It is your procedure, not a script to read out: the admin sees
   short messages and one question at a time, never the step list, an
   empty template, or reasoning about how the run works.

What the admin typed after the command, if anything: $ARGUMENTS
