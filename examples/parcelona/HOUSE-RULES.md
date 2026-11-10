# House rules for this folder

This file tells an assistant working in the Parcelona folder how to
behave here, the way a project instruction file does. It applies to
whoever maintains the skills, human or assistant. It stays in the folder
and is never built into the plugin.

The links and commands below are written for this example inside the
Greenhorn repository. In a company's own folder, Greenhorn runs the same
checks for you, from wherever it keeps them.

## Before changing anything

- Read Greenhorn's
  [conventions](../../skills/greenhorn/references/conventions.md) and
  [schema](../../skills/greenhorn/references/schema.md) first. They are
  the rules every skill here follows; this file only adds what is
  specific to the folder.
- Say what will change and why before changing it, in a sentence; read
  back what changed afterwards in plain words, behaviours included. The
  maintainer confirms the substance, not the text.
- Facts about Parcelona come from `harness-profile.md`. A fact the
  profile does not support is a question for the maintainer, never an
  addition.

## While changing a skill

- Keep one home per rule. A rule's home says so in its own text ("This
  rule lives here in full"); everywhere else, point at it by skill and
  role rather than restating it.
- Bump `metadata.version` in every skill whose content changes.
- When a skill is added, renamed, or retired, update the routing table
  in `parcelona-conduct`, the skill index and Layer A of the block in
  `README.md`, and every sibling's "do not use for" line that the change
  affects, together.

## The always-on block

- Never change the conduct skill's checklist, or the data list or the
  sanctioned routes in the house-rules skill, without re-reading the
  organisation-instructions block in `README.md` against it. Change the block where the change
  needs it, then re-stamp it.
- Never re-stamp without that re-read. The stamp is the record that a
  person looked.
- After the block changes, paste the new text into the organisation's
  instructions field. The checker only sees the copy in this folder.

## Before any publish

Have an independent reviewer go over the changes first, a fresh session
with Greenhorn's review brief, and fix what it must-fixes; it catches a
skill that does not open on the right words, a real name that slipped
in, and prose the assistants cannot follow. Then run both checks from
the repository root, and publish nothing while either reports a
problem:

```bash
python3 skills/greenhorn/scripts/check_harness.py --strict examples/parcelona
```

```bash
python3 skills/greenhorn/scripts/scan_secrets.py examples/parcelona
```

## The repository

In a company's own folder, homestead adds a section like this once the
folder is a repository. Parcelona's lives inside the Greenhorn
repository, so the names below are the example's.

This folder is a private repository at the company's GitHub
organisation. Ana Costa and Lena Hoffmann push to it.

- Commit after the two checks pass, never before; the same checks run
  on GitHub and mark the commit red when one fails.
- One change per commit, with what changed and why in the message, in
  plain words.
- Pull before starting a change, push after finishing one.
- `harness-profile.md`, `sources/`, and `brand-sources/` stay out of
  the repository; the ignore list keeps them out, and a line removed
  from it is a decision recorded in the profile first.
- Never force-push. A file that should not have been committed is
  removed in a new commit, and any secret in it is changed.
- After a Greenhorn update, homestead refreshes `tools/` and the
  workflow; nothing under `tools/` is edited by hand.

## What stays on this computer

In a real company folder, `harness-profile.md`, `sources/`, and
`brand-sources/` never go into the plugin and stay out of version
control. Parcelona's profile is fictional and scrubbed, which is the
only reason it is committed here.
