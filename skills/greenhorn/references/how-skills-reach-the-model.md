<!--
Title: How skills reach the assistant
Date: 2026-11-09
-->

# How skills reach the assistant

For the admin who asks why Greenhorn needs the Code tab, or why the
always-on block exists. Say it in their terms; this page is the substance.

**A skill is a folder with a short document in it.** The document starts
with a name and a one-line description. The assistant sees every
installed skill's name and description all the time, and nothing else of
them. When a request matches a description, it opens that skill and reads
the rest. That is why the description does the routing, and why a skill
with a vague description never gets opened.

**Files beside the document are read on demand.** A reference file, a
logo, or a font in the skill's folder is only used when the skill's text
names it and the assistant decides it needs it. A file nothing names is
dead weight.

**Scripts only run where code can run.** In the Code tab of the desktop
app, the assistant works in a folder on your computer and can run small
programs. That is what Greenhorn needs to build: files on disk, and Python
to run the checks. In chat, the assistant reads skills but cannot work
with your folder or run the checks, so Greenhorn itself lives in the Code
tab.

**The company plugin works everywhere plugins do.** Once uploaded for the
organisation, its skills reach chat, Cowork, and Code sessions alike. The
company skills hold no scripts, so they need nothing special to run.

**The always-on block is the one thing that is always read.** Skills are
opened only when the assistant thinks they apply. The organisation's
instruction field is read in every conversation, so the block that goes
there routes to the skills (Layer A) and carries the few rules that must
hold even when no skill was opened (Layer B). It does not travel inside
the plugin; someone pastes it into the admin settings. The copy in the
folder's `README.md` is what the checks can see.

**Why the block has a stamp.** Layer B repeats rules whose full statement
lives in the conduct skill (its checklist) and the house-rules skill (its
data list and its routes). When any of them changes, the checks fail until a person has re-read the block and renewed
its stamp, so the always-on copy cannot quietly drift from the rules.

**Other assistants** read the same skill folders when they support the
open Agent Skills format, and have their own place for always-on
instructions. Only the packaging changes; roll-out says what goes where.
