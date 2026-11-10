<!--
Title: Roll-out, build and publish
Date: 2026-11-10
-->

# Roll-out: build and publish

**Command:** `/greenhorn:roll-out`. Also offered by giddy-up after each
round of skills.

**Inputs:** the folder; from the profile's Operations section, which
assistant the team uses and which plan the organisation is on.

**Outputs:** the company plugin as a zip in `dist/` with a higher version
than the last build, the always-on block printed for pasting whenever it
changed, the hand-over steps for the team's assistant, and the backup
reminder.

This is the one place the admin hears about the two plugins (router,
"Two plugins, said once"): one sentence, inside the hand-over steps for
the team, when the zip exists. Nothing about it before that, and
nothing again once the profile's "Where we are" carries `two-plugins
line said <date>`.

## Who this build is for

Before anything else, unless the admin already said which: one card
with the question tool. "Just me for now", recommended until everything
under "Ready for the team" is met, or "the whole team". The answer
decides the rest. A build for the admin alone skips the readiness
checklist and the paste; a build for the team runs both. Never assume
the answer from the word "publish".

## Trying it yourself first

The first build is usually for the admin alone, right after the first
round of skills: the same zip, uploaded under their own account the way
"Not an Owner?" below describes, and used for a day or two in real work.
Nothing is pasted into the organisation's instructions for this; the
always-on block waits for the team publish. Run the steps below with
that destination, skip the readiness checklist, and say at the end: what
they notice comes back as "add a skill" or "it keeps getting X wrong",
and the next chapters fill in the rest.

## Ready for the team

Before the build that goes to the whole organisation, check these
against the profile and say which are missing. A missing item is a stop
for the team publish, never for a build the admin uses alone.

- The house-rules chapter is done and its sign-off is recorded
  (`harness-profile.md`, AI house rules), and the ai-house-rules skill
  exists.
- The confirmations card was answered: maintainer, advocate, channel,
  audience, languages, placeholder names (the profile's Operations and
  Audiences sections carry no `[assumed, open]` line).
- The working-with-ai skill exists, written from the "AI in our daily
  work" chapter.
- Conduct's essentials come from the "AI in our daily work" chapter, or
  the admin has said the checklist as it stands is enough for now.
- The always-on block was reviewed by the admin and stamped (reins).
- An independent review has run since the last change to any skill,
  the routing, or the block, and its must-fix findings are fixed
  (`independent-review.md`); the profile's "Where we are" carries
  `independent review <date>`, and nothing changed after it except the
  fixes that review asked for. It
  catches what the writer can no longer see: a skill that does not open
  on the words colleagues use, a real name or a piece of sensitive data
  that slipped through, prose the team's assistants cannot follow.
- The exact-facts list (round-up, "Exact facts": phone numbers,
  addresses, URLs, registration and VAT numbers, prices, timelines,
  reference formats) has been confirmed by the admin: the profile's
  "Where we are" carries `exact facts confirmed <date>`, and no exact
  value was added or changed after it. A wording fix elsewhere in a
  skill does not reopen the list. Not needed for the build the admin
  uses alone.
- **A backup of the folder exists**, somewhere the admin controls, and
  they know to keep making them: the folder is the company's AI
  knowledge in source form, and after this build `dist/` holds the
  plugin too. Ask where the copy is; if there is none, make this the
  moment. Homestead later takes over for the skills; the profile, the
  sources, and the brand sources never go into the repository, so they
  keep needing a copy of their own.

## Steps

1. **Run round-up** (`round-up.md`) and show its report.
2. **Refuse while anything mechanical fails.** Any finding from the
   checker with `--strict`, or from the secret scanner in `skills/` or
   `README.md`, stops the build. Say which, offer to fix it through
   wrangle or reins, and stop here. Judgment findings do not block: show
   them and ask whether to fix them first.
3. **First build only: the plugin's own name tag.** The manifest the
   build writes names who made the plugin and says in one line what it
   is. Neither is guessed. Ask the admin how the maker should be named
   (usually the company's name) and whether they want a one-line
   description; without one, the build takes the first paragraph of
   `README.md`. Then write the two lines into `harness.yaml` and say so:

   ```yaml
   plugin-author: "Acme Kitchenware"
   plugin-description: "What Acme's assistant knows: who we are, how we write, our terms, and the AI house rules."
   ```

   The plugin's name is the prefix every skill shares (`acme` for
   `acme-conduct`). Only when the admin wants another, add
   `plugin-name:` too. The shape is in `references/schema.md`, "The
   settings file".
4. **Dry run.** From the company folder, with the skill folder's real
   path in place of the variable, as the router says:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_plugin.py" --dry-run .
   ```

   Read the output and say it in plain words: which skills go in, by
   name; what stays out and why, in one line each; the version the zip
   will get; and whether the always-on block changed since the last
   build. If the script refuses, every line starting `REFUSED`, `ERROR`,
   `WARN`, or `SECRET` is one thing to fix, with its file (warnings count,
   because the build is strict); explain each, offer the fix through
   wrangle or reins, and stop. Lines starting `NOTE` do not stop the
   build; pass them on. Never work around a refusal by hand, and never
   assemble a zip any other way: the script exists so the allowlist
   cannot be got wrong. Two refusals that need the admin rather than a
   skill change: a missing or damaged `build-state` block in
   `harness.yaml` (say what the script complains about, fix or remove
   the block, and say so; the next build writes it fresh), and a
   missing `plugin-author` on a folder that was built before (step 3
   again).
5. **Build.** For a build the admin uses alone, just build and say what
   was made. For the build that goes to the team, run "Ready for the
   team" first and ask for the go-ahead in one line. Then:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_plugin.py" .
   ```

   The version rises by the smallest step by default. Add `--bump minor`
   when a skill was added or retired, `--bump major` when the admin says
   this is a new generation of the plugin, or `--set-version X.Y.Z` when
   the admin names the number. Say which you chose and why before the
   build. The version must rise every time: the organisation only notices
   an update when it does, and the script refuses a lower one, including
   one that an earlier zip in `dist/` already carries. If a zip with the
   same version is replaced, the script says so; that only happens when
   the number was set by hand. Tell the admin the zip's path and version.
6. **Hand it over** for the team's assistant: the two sections below.
   Pick the one the profile says; when the profile does not say, ask.
7. **The always-on block.** The build prints it with where it goes. For
   a build the admin uses alone, say only that the block waits for the
   team publish. Otherwise, when the script says the block CHANGED, or
   the admin says it was never pasted, walk them through
   "Pasting the always-on block" below. Otherwise say it is unchanged and nothing needs pasting. If the
   script says there is no block to paste, the folder has no conduct
   skill yet or reins has not run; say so and offer reins. The plugin
   does not carry the block.
8. **The backup reminder**, at the end of every roll-out, one line; the
   full conversation about backups happened in "Ready for the team".
   Before homestead: the folder's full path, and "copy it to a drive
   you control; `dist/` now holds the plugin too". Once the folder is a
   repository: "the repository holds the skills; the profile, the
   sources, and the brand sources still need their own copy".
9. **After the first team publish**, offer campfire once, in one line:
   telling the team, as an email, a post, a note, or a handout, in the
   company's voice, with their own examples. Only when the voice skill exists and the look is settled
   (`campfire.md`, "The gate"); otherwise name what is missing and
   which chapter supplies it, and offer campfire after that chapter.

## Handing it over: a Claude organisation

Every path, role, and limit below is from the documentation as read on
the date in `references/upload-facts.md`; open that file when the admin
asks where a fact comes from, and check it against the live screens
when a label does not match. Walk the admin through one step at a time,
and ask them to say what they see before the next.

### Who can do it

An Owner or Primary Owner on a Team or Enterprise
plan. The role shown as Admin in the members list cannot. If the admin
is not an Owner, use "Not an Owner?" below.

### Uploading to the organisation

1. In Claude, open Organization settings, then Plugins & skills, and stay
   on the Inventory tab.
2. Choose Add, then "Upload a plugin", and pick the zip from `dist/`:
   `dist/<name>-vX.Y.Z.zip`, the one the build just named.
3. Check the name on the row: it is the company's, never "greenhorn".
   This is where the one sentence goes, unless the profile says it was
   said before: "This zip is your company's plugin and goes to the
   organisation; Greenhorn itself stays under your own plugins." Then
   write `two-plugins line said <date>` under "Where we are" in the
   profile. If the row says greenhorn, stop: the wrong zip was picked.
4. Set its default access from the row's menu. Say the four values in
   plain words (they are in `upload-facts.md`) and suggest: "Available
   to install" while a few colleagues try it, "Installed by default"
   when it is for everyone, "Required" when the house rules must hold
   for everyone and nobody should be able to switch it off. On
   Enterprise, a group can get its own value, which is how a restricted
   tier's plugin stays with its department; on Team there is no group
   setting.
5. Say what reaches whom: chat and Cowork for every member who has it;
   Claude Code sessions signed in with the claude.ai account on a recent
   Claude Code. Changes can take a little while to show up.

### Updating later

Same place, the plugin's row menu, "Upload new
version", then pick the new zip. The version members get is marked
Current; an earlier version can be made current again from Version
history. The plugin's name never changes; its version always rises,
which the build takes care of.

### Not an Owner?

The admin uploads it for themselves (Customize, then
Plugins, then Add, then "Upload plugin"), tries it, and then either
shares it with named colleagues or uses "Publish to org" on its page,
which asks an Owner to add it to the inventory under whatever review the
organisation has set. Before sharing or "Publish to org", check the
name on the plugin's page: it is the company's, never "greenhorn". Two
plugins sit side by side under the admin's own plugins at this point,
and publishing the wrong one hands the team the builder instead of the
assistant. This is where the one sentence about the two plugins goes
when the profile does not record it yet; then record it. If the Add menu has no upload option, the
organisation has switched user-created skills off; an Owner has to do
the upload.

### Pasting the always-on block

Pasted by an Owner or Primary Owner, after the
plugin is uploaded, so the skills it routes to exist:

1. Open Organization settings, then Organization and access.
2. Find the section called "Organization instructions".
3. Replace whatever is in the field with the whole block, exactly as
   printed, and save. The field holds 3,000 characters; the build prints
   the block's length next to that cap.
4. Say what it does: it applies to every conversation of every member,
   and wins over a member's own instructions where they clash. Its last
   line keeps it quiet outside company work. Changes can take up to an
   hour to reach everyone. Whether it also reaches Code tab and Cowork
   sessions is not stated in the documentation; suggest the admin asks
   the assistant in a Code tab session a day later and sees.

The checker only ever sees the copy in `README.md`. Every time the block
changes, reins or roll-out prints it again, and someone pastes it again.

## Handing it over: another assistant

The folder is the same; only the packaging differs. The built zip still
helps: unzip it and the `skills/` folder inside is exactly the set of
company skills, with nothing from the folder that should stay home.
Say which text goes where, in that product's own terms, and have the
admin check the product's current documentation for the exact menu; never
guess a menu path.

- **The always-on block** goes into the setting the product applies to
  every conversation for the whole team: the organisation-wide, workspace,
  or shared custom instructions. Check that field's length limit. If it
  is smaller than 3,000 characters, shorten Layer B's wording with reins
  first and set `org-block-max` in `harness.yaml` to the real limit, so
  the checker holds the block to it from then on. Never drop an
  essential to fit; never move rules into Layer A.
- **The skills**, if the product reads skill folders in the open Agent
  Skills format: the `skills/<prefix>-*/` folders go where it looks for
  them, each folder whole. The manifest is for Claude only and is left
  out.
- **The skills**, if it does not: they become the team's shared knowledge
  files or project documents, each `SKILL.md` as one document, conduct
  and the house rules first, the rest after. Files under a skill's
  `references/` go beside it. The description line at the top of each
  skill still tells a reader what it is for.
- **Nothing else travels.** The profile, the sources, the brand sources,
  the house rules for the folder, the settings, and the README stay on
  the admin's computer, exactly as for a Claude plugin.

## What the admin sees

The round-up report; then either a stop with the reason, or a finished
zip with its version and path; the always-on block in a copy-ready fence
with where it goes, when it changed; the hand-over steps for their
assistant, one at a time; and the backup reminder.
