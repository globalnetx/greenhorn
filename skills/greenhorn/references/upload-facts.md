<!--
Title: What the documentation says about uploading a plugin and setting organisation instructions
Date: 2026-11-09
-->

# Upload facts, with dates and sources

What roll-out and reins tell the admin about a Claude organisation comes
from here. Every fact names the page it was read on and the day. Re-read
the pages before a release and move the date; a menu label changes more
often than a rule. `scripts/build_plugin.py` carries the paste path, the
role, and the cap as constants with the same source, and the checker's
default cap is the same number; keep all three in step.

## The organisation instructions field

Source: support.claude.com, "Set organization instructions" (article
14546867, in Admin management, Team and Enterprise plans). Article last
updated 2026-08-31; read 2026-11-09.

- **Where:** Organization settings, then Organization and access, then
  the section called "Organization instructions".
- **Who:** Owners and Primary Owners, on Team and Enterprise plans. The
  article says "You need at least an Owner role"; a plain Admin is not
  named.
- **Cap:** 3,000 characters. The checker's default and the build's
  counter use this number.
- **Reach:** every conversation of every member of the organisation. When
  a member's own instructions contradict it, the organisation's win;
  anything the organisation's instructions do not address, the member's
  still apply. Changes "may take up to an hour to take effect across
  Claude products".
- **Not stated:** whether the field reaches Claude Code and Cowork
  sessions as well as chat. Say so to the admin as unconfirmed, and let
  them check in a Code tab session after pasting.
- The field cannot switch off Claude's own safety rules.

## Uploading a plugin to the organisation

Source: claude.com/docs/plugins/admin, read 2026-11-09. Pages carry no
date of their own.

- **Where:** Organization settings, then Plugins & skills, on the
  Inventory tab. Then Add, then "Upload a plugin" (a zip).
- **Who:** Owners and Primary Owners, on Team and Enterprise plans. On
  Enterprise, also a custom role whose Libraries permission allows
  managing. The role labelled Admin in the members list does not include
  this page. A view-only library role sees the page without the Add
  menu.
- **Default access**, set from the plugin's row menu:

  | Value | What members get |
  | --- | --- |
  | Not available | Hidden; nobody can install it. |
  | Available to install | Listed under Discover; members install it if they want it, and can remove it. |
  | Installed by default | Already installed for every member; a member can turn it off. |
  | Required | Installed and always on, marked as required by the organisation; members cannot turn it off. |

- **Groups:** on Enterprise a user group can have its own access value
  for a plugin ("Group access"). Team has no group setting; a Team pilot
  shares with named people instead (next section). Where several groups
  apply, the most permissive wins, in the order Required, Installed by
  default, Available to install, Not available.
- **Updates:** the item's menu, "Upload new version". The version members
  get is marked Current. Version history lets an Owner revert to an
  earlier version or make another one current; nothing is deleted. The
  manifest's version must rise on every release (claude.com/docs/plugins/build,
  read 2026-11-09: "Raise it on every release"); the build does this.
- **Reach:** chat and Cowork for every member who gets the plugin. Claude
  Code picks a member's plugins up in Cowork and in sessions signed in
  with the claude.ai account on Claude Code v2.1.273 or later
  (claude.com/docs/plugins/org-rollout, read 2026-11-09). The platform
  table counts the desktop app's Code tab under Claude Code
  (claude.com/docs/plugins/platform-support, read 2026-11-09).

## Uploading a plugin for yourself, or sharing it

Source: claude.com/docs/plugins and claude.com/docs/plugins/admin (Policy
tab), read 2026-11-09.

- A member uploads under their own account: Customize, then Plugins,
  then Add, then "Upload plugin". This is where Greenhorn itself goes.
- Whether members may do this is the organisation's "User-created
  skills" policy; when it is off, the upload options are missing from
  the member's Add menu.
- "Skill sharing" lets a member share a plugin with named people (and,
  on Enterprise, with groups).
- "Publish to org" on a plugin's page asks for it to be added to the
  organisation's inventory. The publishing policy is Requires review,
  Open, or Off; Owners approve. Team defaults to Open.

## The zip and its limits

- **Manifest:** `.claude-plugin/plugin.json` "at the zip root (or inside
  a single top-level directory)" (claude.com/docs/plugins/build, read
  2026-11-09). "Zip either the plugin folder itself or its contents; both
  work as long as the archive holds one .claude-plugin/plugin.json"
  (claude.com/docs/plugins, read 2026-11-09). The build uses one
  top-level folder named after the plugin.
- **Manifest fields:** `name` is the only required key; `version` is "a
  version string, not checked against semver"; `author` is an object with
  `name` (code.claude.com/docs/en/plugins-reference, read 2026-11-09).
  Reserved plugin names: claude, anthropic, anthropics, claude-code,
  claude-mods, and names starting claude-, anthropic-, anthropics-,
  cc-plugin- (same page).
- **Size:** "Each plugin can contain up to 5,000 files and 200 MB, and
  200 MB is also the largest file that Upload plugin accepts"
  (claude.com/docs/plugins/platform-support, read 2026-11-09).
- **No top-level `bin/`:** claude.ai rejects a plugin with one, uploaded
  or synced (claude.com/docs/plugins/org-sync, read 2026-11-09).
- **Skill folder names:** not `synced` in any capitalisation, and not
  `anthropic-skills` (code.claude.com/docs/en/skills, read 2026-11-09).
- **Skill frontmatter:** outside Claude Code the accepted fields are
  `name`, `description`, `license`, `compatibility`, `metadata`, and
  `allowed-tools`; any other key fails with "Unexpected key(s) in SKILL.md
  frontmatter" (code.claude.com/docs/en/skills, read 2026-11-09). The
  same six are the whole field list of the Agent Skills specification:
  `name` up to 64 characters, lowercase letters, digits, and hyphens,
  matching the folder; `description` up to 1,024 characters;
  `compatibility` up to 500; `metadata` a map of string keys to string
  values (agentskills.io/specification, read 2026-11-09).
- **Marketplace `source`:** `"./"` is the form the publishing guide uses
  for a plugin at the repository root; `"."` is also accepted
  (code.claude.com/docs/en/plugins/publish and
  code.claude.com/docs/en/plugins/marketplace-reference, read 2026-11-09).

## Known from use, not from the pages

- A skill whose description is longer than 1,024 characters is dropped
  from an organisation plugin with only a warning in the admin settings,
  rather than failing the upload. The pages state the cap and not the
  consequence. The checker fails on the cap for exactly this reason.
