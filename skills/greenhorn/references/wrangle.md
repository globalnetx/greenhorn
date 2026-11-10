<!--
Title: Wrangle, add or fix a skill
Date: 2026-11-09
-->

# Wrangle: add or fix a skill

**Command:** `/greenhorn:wrangle`. Also what giddy-up's fixes and
round-up's findings are carried out with.

**Inputs:** one of a lesson ("we never quote before the carrier
confirms"), a document, an existing skill draft, or a complaint ("it keeps
getting X wrong"). The folder's skills, `harness-profile.md`, and
`harness.yaml`.

**Outputs:** one new or changed `SKILL.md` (with its `references/` files
when it needs them), new facts in the profile, then the routing brought up
to date by reins and the folder checked by round-up.

## Steps

1. **Read the folder, and follow it.** The profile; every skill's name
   and description; conduct's routing table; and the skills whose rules
   the new text will state or whose voice it will use, in full, followed
   as if installed (router, "Use what the folder already knows").
   Without this, a new skill duplicates an old one or contradicts it.
2. **Ask what the lesson is**, in the admin's words, and for one real
   case where it went wrong or would have. Ask who it is for: everyone on
   staff, or a group (`references/conventions.md`, "Audiences: one tier by default").
3. **Decide where it lives.** In order:
   - The lesson is already in a skill, but that skill did not open. The
     fix is that skill's description: add the words people actually used.
     No new skill.
   - It belongs in an existing skill's scope. Change that skill.
   - It is a rule that already has a home elsewhere (the table in
     `giddy-up.md`, "One home per rule"). Change it there, and point at it
     from here if needed.
   - Only then: a new skill.

   Tell the admin which of these it is and why, before drafting.
4. **Take in the material.** A document goes through the intake in
   `giddy-up.md`, "Intake, per document", including the refusal list and
   reporting embedded instructions. Every fact goes into the profile with
   its provenance tag. A fact without a confirmed tag is a question for the
   admin, never an addition.
5. **Draft the description first**, following `references/conventions.md`, "The
   description is the router": the trigger and colleagues' own words up
   front, what goes wrong without it when it must not be skipped, and
   every "do NOT use for" naming the sibling skill where that work lives.
   When it shares a border with a sibling, plan the matching phrase in the
   sibling's description too; reins applies it. A skill-creation helper
   in the session (router, "Use what the harness offers") tunes the
   description and tests the trigger; the conventions still decide.
6. **Draft the body** from the skill template
   (`templates/SKILL.md.template` in this skill's folder), shaped like the
   Parcelona skill nearest in kind. Judgment, not manual. One concrete
   example at least, obeying every other skill's rules. A new skill gets
   `metadata.version: 0.1.0`; a changed one gets its version bumped (a
   wording fix the patch number, new content the minor number).
7. **Reference files.** A document kept word for word goes under the
   skill's `references/` with the dated source header from `references/schema.md`,
   "Reference files". Any other file there is named in the body.
8. **Self-check.** Run `self-check.md` over the draft and fix what fails.
9. **Say what will change**, in a sentence or two: which skill, what it
   will say or stop saying, and from which fact. The admin's lesson is
   already their substance; this is the read-back before, not a review of
   text. Then write.
10. **Write**, and run the checker with `--strict`. Fix what it
    reports and include the fixes in the read-back. A stamp error after a change to the
    conduct checklist, the house-rules data list, or the house-rules
    routes is expected: reins
    handles it next, with the admin's review. Never run the stamper
    here.
11. **Run reins** (`reins.md`), then **round-up** (`round-up.md`). Read
    back what changed in easy language, behaviours included, the way the
    router says. After a batch of changes, offer the independent review
    (`independent-review.md`).

## Retiring or renaming a skill

- **Retiring.** Set `metadata.deprecated` to the reason and, when a
  successor exists, `metadata.replaced-by` to its name. Reins drops it
  from the routing. Delete the folder only when nothing points at it any
  more, and say so when it happens.
- **Renaming** breaks every pointer to the old name and makes the
  organisation's copy look like a new skill. Avoid it. When it cannot be
  avoided, create the new skill, retire the old one with `replaced-by`,
  and let reins update every pointer.

## What the admin sees

A question or two about the lesson, a sentence on where it will live and
why, then a short read-back of what changed, in easy language, with a
line from reins and round-up when they had something to say.
