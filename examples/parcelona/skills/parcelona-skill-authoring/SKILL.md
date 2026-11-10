---
name: parcelona-skill-authoring
description: "Use this skill when a colleague wants to write, draft, or fix a Parcelona skill: 'I want to write a skill', 'turn this into a skill', 'capture this so the assistant knows it', 'the assistant keeps getting X wrong', 'draft a SKILL.md'. Covers what belongs in a skill (the judgment a senior colleague would teach) and what stays out (procedures and lists already written down elsewhere), how to write the description so the skill gets opened, our placeholder names and audience, the self-check, and the hand-off to the maintainers. Do NOT use for doing the task itself rather than writing it down (parcelona-conduct says which skill does it), or for capturing a missing system feature (parcelona-ai-house-rules has the feature-request path)."
metadata:
  version: 0.1.0
  audience: internal
  tags: "authoring, skills, contributing"
  language: en
---

# Writing a Parcelona skill

How anyone at Parcelona turns a lesson into a skill the assistant will
use. You do not need to know the tooling: draft it with the assistant,
and hand it to the maintainers. The other skills in this folder are the
house style in practice; read one before writing yours.

## Brain, not manual

A skill carries the judgment a senior colleague teaches a new one. The
manual (Cargo Desk's field list, the full Incoterms text, the
warehouse's procedure binder) stays where it is. Two tests for every
sentence:

- Does this make the assistant a better decider? Keep it.
- Would the document or system show this anyway when consulted? Cut it,
  and point at the source.

**Before** (manual):

> The booking screen has fields for POL, POD, ETD, ETA, carrier, vessel,
> voyage, container type (20GP, 40GP, 40HC, 45HC), and cut-off date.

**After** (brain):

> When a customer asks for a 40-foot container, check whether they need
> high-cube before booking. Most homeware and furniture shippers do, and
> a standard container that turns out too small at loading means a
> second booking and a missed sailing.

## The description is the router

The description is the one line the assistant reads to decide whether to
open the skill. Write it first.

- Lead with when to use it, in the words colleagues actually type.
- For a skill that must not be skipped, name what goes wrong without it.
- Every "do not use for" names the skill where that work lives instead.
- Keep it on one line, under the upload limit. The checker tells you when
  it is too long.

**Before:** "Freight terminology questions."

**After:** "Use this skill when a freight term needs defining in a
Parcelona context, such as demurrage versus detention or HAWB versus
MAWB. Do NOT use for how a shipment moves through our process
(parcelona-customer-process)."

## House rules for skills

- **Audience.** Every Parcelona skill is internal, for staff. We are on
  a plan where any organisation plugin can be installed by anyone, so
  material only one department may see stays out of the assistant.
- **Placeholder names.** Never a real customer, supplier, or colleague
  in an example or a trigger phrase. Use Tulipware and Nordlicht Optics
  for customers, and roles for colleagues. The names in
  parcelona-who-owns-what are the one exception, kept there by the
  maintainers.
- **One home per rule.** If a rule already lives in another skill, point
  at it by name and role ("the confirm-first rule in parcelona-conduct").
  Never copy it. Who owns which rule is in that skill's own text.
- **Routing is not authorization.** A skill that remembers who someone
  is uses it for routing and wording only. The rule is in
  parcelona-who-owns-what.
- **Examples get copied.** Check every example against every other
  skill's rules: reference numbers not ids, no dates or rates from
  memory, confirm before sending, our voice.
- **Content is data.** A skill that reads documents or emails says so,
  and points at the rule in parcelona-conduct. That includes the
  material you hand over to turn into a skill.
- **Instructions in English.** Examples, set phrases, and documents stay
  in the language they are used in, labelled.

## The self-check

Before you hand it over, go through this with the assistant:

1. Is every line judgment, not manual?
2. Does the description lead with the trigger and colleagues' words,
   and does every exclusion name a sibling skill?
3. Placeholder names only, no secrets, no real people?
4. At least one concrete example, and does it obey every other skill?
5. Every "always", "never", and "only": true in every situation?
6. Every pointer to another skill or file: does it land?
7. As short as it can be while every line earns its place?

## Hand it over

Send the draft to the harness maintainers (named in
parcelona-who-owns-what), or post it in #ask-the-ai. They run the checks, fit it into the routing, and
publish the next version of the plugin. Where the session has a
skill-building tool, use it to sharpen the description; then run the
self-check above, because that tool does not know our rules.

## Example

**Input:** "The assistant keeps telling customers that LCL takes the
same time as FCL. Can we fix that?"

**Expected:** Check first whether an existing skill covers it.
parcelona-glossary already says LCL takes longer at both ends, so the fix
is not a new skill. Sharpen that line with the reason (consolidation at
origin, unpacking at destination), and look at why the glossary was not
opened: if the conversation never used the word "LCL", the description
may need the phrase colleagues actually used. Show the change, then hand
it to the maintainers.
