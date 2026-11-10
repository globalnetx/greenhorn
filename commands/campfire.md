---
description: "Tells your team about their new colleague, in the form you want: an email, a post in your channel, a short note, or a handout, in your voice, with your own examples and a named person to ask."
allowed-tools: Read Edit Grep Glob WebFetch WebSearch Bash(python3 *) Bash(py *) Bash(python *) Bash(mkdir *)
---

Run Greenhorn's campfire mode: telling the team.

1. Read the Greenhorn skill in full:
   `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn/SKILL.md`. It holds the rules
   for every mode: looking at the folder first,
   and who decides what: the admin confirms the facts, the assistant
   writes the files and reads back what it wrote.
   Greenhorn's skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn`.
   Wherever the skill or its references write `${CLAUDE_SKILL_DIR}`,
   use that folder instead.
2. Then follow
   `${CLAUDE_PLUGIN_ROOT}/skills/greenhorn/references/campfire.md` step by
   step.

What the admin typed after the command, if anything: $ARGUMENTS
