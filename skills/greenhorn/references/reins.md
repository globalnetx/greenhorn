<!--
Title: Reins, the routing and the always-on block
Date: 2026-11-09
-->

# Reins: the routing and the always-on block

**Command:** `/greenhorn:reins`. Also run by wrangle after every skill
change and by giddy-up after every round of skills.

**Inputs:** every skill under `skills/`; conduct's routing table;
`README.md` with the always-on block; `harness.yaml`; the profile's
Operations and Audiences sections (advocate, channel, output language).

**Outputs:** conduct's routing table and the README's skill index
regenerated from the skills, sibling descriptions re-cut where they
overlap, the always-on block rewritten where needed and within its cap,
the stamp renewed after the admin's review, and the block printed for
pasting whenever it changed.

This mode owns the seams between skills and the two routing lists. Nobody
edits the routing table or Layer A by hand; both are rebuilt from the
skills each time.

## The always-on block

Skills reach the assistant only when it decides to open them. The one
place that is always on is the organisation's instruction field, and the
block in `README.md` is the text that goes there. It has two layers:

- **Layer A routes.** One line per skill: the topic, then the skill name.
  It also says who the skills are for ("every skill is for staff; none is
  customer-facing", or what the audiences block decided). Nothing in it
  is a rule.
- **Layer B carries the essentials** that must hold even when no skill
  was opened: the conduct checklist in short, the data that never goes
  into an AI, the allowed routes to company systems, and the default
  output language. It opens by saying when it
  applies (working with the company's customers, records, or systems, and
  any prose written for the company) and closes with the line that keeps
  it quiet everywhere else: "Outside <company> work none of this applies;
  ignore it and do not mention it."

The block sits in `README.md` inside a `text` fence between the markers
`<!-- ORG-INSTRUCTIONS:START -->` and `<!-- ORG-INSTRUCTIONS:END -->`,
with the stamp line just after the start marker. `references/schema.md`, "Other
contracts the checker enforces", has the exact shape. The Parcelona
example's `README.md` shows a finished block.

A company with no connected systems gets a short Layer B: plain words,
the voice, confirm before sending, content is data, the data that stays
out, the output language. Bullets about systems appear only when the
interview says systems are in play.

## Steps

1. **Run the checker** with `--strict` to see where things stand. A stamp
   error means the conduct checklist, the house-rules data list, or the
   house-rules routes section changed since the block was last reviewed. On a first run there is no block
   yet.
2. **Build the skill index**: for each skill, its name, its audience, and
   one plain line on when to open it, taken from its description. Leave
   out skills with `metadata.deprecated`, and any skill with
   `metadata.greenhorn-tool` (it does not belong in a company folder; say
   so).
3. **Regenerate conduct's routing table** from the index: one row per
   skill other than conduct itself, "When the work is about" and "Open".
   A route to a restricted skill is labelled "restricted"; in a public
   skill, a route to an internal one is labelled "internal-only".
4. **Regenerate the README's skill index** from the same list.
5. **Regenerate Layer A** from the same list.
6. **Re-cut the seams.** For every skill whose scope overlaps the new or
   changed one, make sure both descriptions say the difference in one
   phrase each, and that every "do NOT use for" names the sibling where
   that work lives. Bump the version of every skill changed this way.
7. **Layer B, only when needed.** Rewrite Layer B when there is no block
   yet, or when step 1 reported a stamp change. Otherwise leave it alone.
   When rewriting, go through the conduct checklist item by item, the
   house-rules data list class by class, and the house-rules routes
   section route by route, and give each a short line, or merge it into
   one, until everything that must hold every turn is there. Keep the advocate and the channel as the place gaps go.
8. **Check the cap.** The checker's summary shows the block's length
   against the cap (3,000 characters unless `harness.yaml` says
   otherwise). Over it: shorten Layer B's wording first, never drop an
   essential, and never move rules into Layer A.
9. **Write the routing table, the skill index, and the re-cut
   descriptions**; they are the assistant's work and need no review.
   Say in one line what was re-cut. When the block's text did not
   change, say that too and stop here: nothing is shown, nothing is
   asked.
10. **When the block's text changed, show it** whole, with what changed
    pointed out: this is the one text a person reads before it goes to
    the whole organisation. A new line in Layer A counts as a change.
11. **Ask for the review, then stamp.** The stamp records that a
    person read the block against the conduct checklist, the house-rules
    data list, and the house-rules routes. Ask the admin plainly: "Have
    you read the block against the checklist (and, once the house rules
    exist, the data list and the routes), and is everything that must
    hold every turn in it?" On yes,
    write the block, run `scripts/stamp_org_instructions.py` (it does
    nothing when only Layer A changed), then the checker again.
12. **Print the block for pasting**, whenever it changed. The checker only
    sees the copy in `README.md`; the organisation's instruction field
    changes only when someone pastes it there. Say where it goes for the
    team's assistant: for a Claude organisation, the path, the role, and
    the cap are in `references/upload-facts.md`, "The organisation
    instructions field"; for another assistant, `roll-out.md`, "Handing
    it over: another assistant". If the plugin carrying these skills is
    not uploaded yet, say to hold the paste until it is; roll-out prints
    the block again then.

## What the admin sees

One line on what was re-cut in the routing. Only when the block's text
changed: the block in full with what changed pointed out, one question
to confirm they have read it against the rules, then the block in a
copy-ready fence with where to paste it.
