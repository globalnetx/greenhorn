<!--
Title: The frontmatter schema and the folder contracts the checker enforces
Date: 2026-11-09
-->

# Skill frontmatter schema

The contract for the block at the top of every `SKILL.md`, between the two
`---` lines. Greenhorn's checker, `check_harness.py`, enforces what is
listed here. How to
write the body of a skill is in [`conventions.md`](conventions.md).

This contract is shaped by one consumer: Claude's plugin upload, the
publish path Greenhorn supports out of the box. Other assistants ignore the
frontmatter and read the body, which is why the body is what has to stay
portable. The frontmatter is packaging; the words below it are the product.

## Only six top-level fields

A skill uploaded to claude.ai as part of a plugin accepts exactly these
top-level fields. Any other field at the top level fails the upload
outright, so the checker treats one as an error.

This binds Greenhorn's own skill exactly as it binds every company
plugin. Greenhorn is uploaded the same way, so its
`skills/greenhorn/SKILL.md` carries these six fields and nothing else at
the top level, its repository has no top-level `bin/` folder (claude.ai and
Cowork refuse a plugin that has one), and its SKILL.md stays short, with
one reference file per mode rather than one long document. The checks
workflow runs the checker, `skills/greenhorn/scripts/check_harness.py`, on
this repository for that reason.

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `name` | yes | string | Lowercase letters, digits, and hyphens; 3 to 64 characters; must equal the folder name. Stable: renaming a skill breaks every pointer to it. |
| `description` | yes | string | 40 to 1,024 characters, on one line. The router: see "The description is the router" in `conventions.md`. |
| `license` | no | string | A licence name or a pointer to a licence file, when the skill carries third-party material. |
| `compatibility` | no | string | A short note on what the skill needs to run (a connected system, a document tool). At most 500 characters. Omit when nothing special is needed. |
| `metadata` | no | mapping | One nested level of `key: value` pairs. Everything Greenhorn tracks per skill lives here (next section). |
| `allowed-tools` | no | string | Tool names the skill may use without asking, separated by spaces. Honoured by Claude Code only. Leave it out unless you know you need it. |

### Why the extras live under `metadata`

Version, audience, tags, and lifecycle notes are things a maintainer wants
on every skill. They cannot be top-level fields, because the upload would
reject them. `metadata` is the one field the format sets aside for exactly
this: a bag of simple pairs that the upload accepts and other clients
ignore. So they live there, one level down, and the checker reads that one
nested level. Nothing deeper is allowed; a nested mapping inside `metadata`
is an error.

Keep values simple strings. A list is written as one string with commas
(`tags: "company, orientation"`), because the format documents string
values and a quoted string always uploads.

## Fields under `metadata`

| Key | Type | Notes |
| --- | --- | --- |
| `version` | string | Per-skill version, `major.minor.patch`, for example `0.1.0`. Bump it whenever the content changes. The checker warns when it is missing or not in that shape. |
| `audience` | string | `internal` (default when omitted), `public`, or `restricted`. See "Audiences: one tier by default" in `conventions.md`. Anything else is an error. |
| `tags` | string | A few words for search and filtering, separated by commas. The description carries the routing; keep tags sparse. |
| `language` | string | First the language the skill's instructions are written in, then any languages its content uses (examples, set phrases, reference documents), separated by commas: `en`, or `en, nl`. Two-letter codes, optionally with a region (`en-GB`, `nl-BE`). The first code should match the plugin's instruction language; see Language in `conventions.md`. The checker warns on a malformed code or a mismatch. |
| `role` | string | `conduct` marks the one skill that owns the cross-cutting rules and the routing table. `house-rules` marks the one skill that owns the list of data that never goes into an AI and the allowed routes to company systems. At most one skill per plugin carries each. The organisation-instructions stamp is computed from both (below). |
| `deprecated` | string | A non-empty reason the skill is on the way out. Expected when `replaced-by` is set. |
| `replaced-by` | string | Name of the successor skill. Must resolve to a skill in the same folder. |
| `greenhorn-tool` | string | `true` on Greenhorn's own skill and nowhere else. The build never copies a skill that carries it into a company plugin; a name match is not used, because a company's own authoring skill may mention Greenhorn by name. The checker warns when such a skill sits beside company skills. |

Unknown keys under `metadata` are accepted silently so a maintainer can add
a note without waiting for a checker change. Established names are reserved
here so their meaning does not drift.

## The name and the folder

The folder is the identity. `skills/acme-voice/SKILL.md` must declare
`name: acme-voice`. Prefix every skill with the company's short name
(`acme-`) so that routes between skills are unambiguous and so the checker
can spot a route to a skill that does not exist: any token with the same
prefix in a description that resolves to no folder is flagged.

## The description

One line, quoted when it contains a colon or a hash. Plain text, no
Markdown. Between 40 and 1,024 characters; the upper bound is the upload's
limit, beyond which the plugin sync drops the skill with only a warning in
the admin console. The checker also warns when the description has no
trigger wording ("Use this skill when", "Trigger when") and when a "Do NOT
use" exclusion names no sibling skill as the destination.

## Other contracts the checker enforces

**The organisation-instructions block.** `README.md` in the folder carries
the paste-ready block for the organisation's instruction field, inside a
` ```text ` fence between two markers:

```text
<!-- ORG-INSTRUCTIONS:START -->
<!-- ORG-INSTRUCTIONS:CONDUCT-HASH=0123456789abcdef -->
(the fenced block)
<!-- ORG-INSTRUCTIONS:END -->
```

The fenced text must stay under 3,000 characters, the field's cap; the
checker's summary shows the current count. The stamp is a fingerprint of
what Layer B of the block restates:

- the conduct skill's checklist: the section under the first `##` heading
  whose text contains "checklist" or "TL;DR", up to the next `##` heading
  or horizontal rule;
- the house-rules skill's data list, when a skill carries
  `metadata.role: house-rules`: the section under the first `##` heading
  that has the word "data" in it (a whole word, so "metadata" does not
  count), up to the next `##` heading or horizontal rule;
- the house-rules skill's routes section, when it has one: the section
  under the first `##` heading with the word "route" or "routes" in it,
  up to the next `##` heading or horizontal rule. A company with no
  connected systems may have no such section; then the stamp covers the
  checklist and the data list alone.

The sections are joined and hashed together after whitespace is
collapsed, so reflowing never trips it. A folder without a house-rules
skill is stamped from the checklist alone. When any covered section
changes, or one appears or disappears, the stamp no longer matches and
the checker fails until a person has reviewed the block and run the
stamper, `stamp_org_instructions.py`. That is the point: a rule change
forces a human re-read of the always-on surface. A folder without the
markers skips this check.

### Reference files

Every Markdown file under a skill's `references/`
opens with a dated source header, so its age can be seen and a stale copy
noticed. The header is either an HTML comment at the very top of the file,
which does not show when the file is rendered, or else the file's first
paragraph. It carries one line starting `Source:` or `Title:` and one
line starting `Date:` followed by a real date (`2026-03-01`, or `2026-03`
when only the month is known). Other lines, such as `Version:` or
`Owner:`, are welcome:

```text
<!--
Source: Acme Customer Guide
Version: 3.2
Date: 2026-03-01
-->
```

For a document kept word for word, `Source` names the document and `Date`
is the document's own date. For a file the maintainer wrote, `Title` names
it and `Date` is the day it was last reviewed. Files of other kinds under
`references/` (images, fonts, data) need no header; the body of `SKILL.md`
names each of them instead.

**Command files.** A plugin may carry commands as Markdown files under
`commands/`, one per command; Claude Code shows `commands/name.md` as
`/plugin:name`. Company plugins usually have none; Greenhorn has one per
mode. Each file has frontmatter with a `description`, the line shown in
the slash menu, and a body saying what to do. Claude Code accepts more
fields on a command, such as `argument-hint`. Greenhorn keeps its command
frontmatter to the six fields a skill upload accepts anyway, as a house
choice, since nobody has yet confirmed how the organisation upload treats
command files; the checker warns on anything else.

**The full set for a relied-on document.** A skill built on a document
the company owns usually carries three layers under `references/`: the
summary and judgment in `SKILL.md`, the full text converted to Markdown
with the header above, and the original file (PDF, Word) beside it for
when it has to be sent or attached. Only the company's own general
documents travel as originals; material written for one customer or one
deal (offers, quotes, contracts, customised proposals, mail) never does,
since it carries that customer's details, and it feeds templates and
scrubbed examples instead. When it is unclear whether a file may go to
every colleague, the admin is asked before it is bundled. Every
non-Markdown file under `references/` is named in the body with its
purpose, or the checker cannot tell a bundled original from a stray
file. A plugin carries files
whole, so the originals travel with the skill; keep them to the
documents staff actually need, since the plugin upload has a size cap.

### The settings file

An optional `harness.yaml` at the folder root, in the
same simple shape as frontmatter:

```yaml
instruction-language: en
placeholders: "Tulipware, Nordlicht Optics"
never-name:
  - Real Customer B.V.
  - Real Supplier GmbH
org-block-max: 3000
plugin-author: "Acme Kitchenware"
plugin-description: "What Acme's assistant knows: who we are, how we write, our terms, and the AI house rules."
build-state:
  version: 0.1.0
  built: 2026-11-09
  org-block-stamp: 0123456789abcdef
```

`instruction-language` is the one language every skill's instructions are
written in. Content may be in other languages, and the default output
language lives in the organisation-instructions block, not here (see
Language in `conventions.md`). The checker warns on any skill whose
`metadata.language` starts with a different code. Without this setting, it
warns when the skills disagree among themselves, naming the language most of
them use.

`never-name` lists real names that must not appear in any skill: customers,
suppliers, partners, and any other name the company wants kept out. The checker
errors on each occurrence with file and line. Colleagues are not listed here;
the names in a who-owns-what skill are there on purpose. `placeholders` is what it
suggests instead. `org-block-max` overrides the cap only if the organisation's
field is known to differ.

The `plugin-` keys feed the manifest the build writes. `plugin-author` is
required: the manifest names who made the plugin, and the build refuses
to guess it. `plugin-name` is optional and defaults to the prefix every
skill folder shares (`acme` for `acme-conduct`, `acme-voice`); it must be
lowercase letters, digits, and hyphens, and a handful of names are
reserved by the platform (the build says which). `plugin-description` is
optional and defaults to the README's first paragraph. `plugin-license`
is optional.

`build-state` is written by the build after every zip and read before the
next: the plugin version it produced, the date, and the stamp of the
always-on block at that moment. The next build raises the version from
it (patch by default) and flags the block whenever its stamp differs, so
the admin knows to paste it again. Leave the block alone; the build
replaces it in place and touches nothing else in the file. If it is ever
damaged or lost, the build says so and refuses; fix or remove the block,
and the next build writes it fresh, refusing a version that an earlier
zip in `dist/` already carries.

## Parser shape

The checker parses frontmatter with a small built-in reader, no library.
Supported: top-level `key: value` with a plain or quoted single-line value;
one nested mapping under `metadata:`; flow lists (`[a, b]`) and block lists
(`- item`) where a list is allowed. Not supported, on purpose: multi-line
block scalars (`|`, `>`), anchors, deeper nesting. If a description does not
fit on one line, it is too long to be a router; trim it.

## Example

```yaml
---
name: acme-compass
description: "Use this skill when the conversation involves Acme as a company, its services, customers, or what it is not; trigger on 'who are we', 'what do we do', 'is this something we offer'. Do NOT use for how we sound in writing (acme-voice) or for what a product term means (acme-glossary)."
metadata:
  version: 0.1.0
  audience: internal
  tags: "company, orientation"
  language: en
---
```
