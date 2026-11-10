<!--
Title: The independent review, after each round of skills
Date: 2026-11-10
-->

# The independent review

Offered after every round of skills in giddy-up and after a batch of
wrangle changes, and required before every build that goes to the team
(roll-out, "Ready for the team"): after any change to a skill, the
routing, or the always-on block, a review runs before the plugin does.
It always catches something. The admin cannot judge a skill by reading it; a second
reader on the AI side can. The review is a helper session on the most
capable model available, at its highest effort, given the folder and
this brief. Nothing in the folder changes during the review; its
findings come back to the main session, which turns them into fixes.

## Offering it

One line, with the question tool: "Shall I have an independent reviewer
go over what we wrote? It takes a few minutes and catches what I can no
longer see." Recommended yes. Say what it costs when the admin asks:
tokens and a few minutes, nothing else.

## The brief

Give the reviewer: the company folder's path, Greenhorn's skill folder
path (so it can open the three references), the names of the skills
written in this round, the exact-facts list the admin confirmed in the
round's summary (every phone number, address, URL, registration or VAT
number, price, timeline, and reference format the round writes, each
marked confirmed, or unconfirmed where the admin has not yet said yes),
and the text below, with nothing else of the conversation. It reads
`harness-profile.md`, every skill under `skills/`, `README.md`, and
Greenhorn's `references/conventions.md`, `references/schema.md`, and
`references/self-check.md`.

> Review these skills as the colleague who was not in the room. For each
> finding give the file, the line, what is wrong, and the fix in one
> sentence. Check, in this order:
>
> 1. **Facts.** Every claim about the company traces to a confirmed line
>    in the profile. List any that do not, and any that contradict one.
>    Every exact value in a skill (a number, address, URL, price,
>    timeline, or format) matches the confirmed exact-facts list you
>    were given; a value not on that list, or marked unconfirmed, is a
>    finding.
> 2. **Coherence.** Skills that disagree with each other, a rule stated
>    in two places, an example that breaks a sibling's rule, a "do NOT
>    use for" that points at the wrong sibling.
> 3. **Conventions.** Everything `self-check.md` lists, applied to each
>    skill; `conventions.md` and `schema.md` where the self-check points
>    at them. Look hardest for what slips through most: a real customer,
>    supplier, or staff name where a placeholder belongs; a value that
>    looks like personal data, a credential, or anything on the
>    house-rules refusal list; a rule or responsibility assigned to a
>    named person.
> 4. **Workable for a smaller model.** The team will run these skills on
>    faster, less capable models too. For each skill: does the
>    description's first sentence carry the trigger in the words a
>    colleague would use; is every rule short enough to follow without
>    inference; is there one concrete example per rule that matters; does
>    nothing depend on knowledge only the interview had; could two skills
>    be opened for the same request, and if so, which wins and does the
>    text say so?
> 5. **Routing.** Conduct's routing table and the always-on block's
>    Layer A name every skill, and nothing else; Layer B holds only
>    essentials; the block is within its cap.
>
> Say which findings must be fixed before the team sees the skills and
> which can wait. Where you are genuinely unsure whether something is a
> finding, list it as a question rather than deciding either way. Do
> not rewrite the skills; report.

## What comes back to the admin

Not the report. Three lines: how many findings, how many must be fixed
first, and what kind they are ("two facts I can't trace, one place where
two skills disagree"). Then the fixes, one at a time, each as a plain
sentence ("the voice skill says we're always informal; the house rules
say sober for incidents; I'll make the voice skill say so too"), through
wrangle. The admin says yes or no to the substance; the wording of the
fix is the assistant's. Findings about untraceable facts become
questions to the admin, never silent deletions.

When the admin has asked for evals and the session has a
skill-creation helper that runs them (router, "Use what the harness
offers"), run it on the round's descriptions as well and fold what it
finds into the same list of fixes; it tests triggering in a way a
reader cannot.

When the helper cannot be started (no helper tool, no capable model),
say so and run the five checks in the main session instead, reading each
skill fresh, and label the result as a self-review.
