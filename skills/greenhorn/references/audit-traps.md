<!--
Title: The audit traps, for round-up's judgment pass
Date: 2026-11-10
-->

# The audit traps

What round-up's judgment pass looks for after the checker has run. The
checker catches what can be counted; these need reading. Each finding is
reported as (judgment), with the skill, the line, and a proposed fix.

| Trap | What to look for | The usual fix |
| --- | --- | --- |
| Seams not re-cut | Two descriptions that would both fire on the same request, with neither saying how they differ. | One phrase in each description saying the difference; reins applies it. |
| Dead-end exclusions | A "do NOT use for" that names no sibling, or names one that does not cover the work. | Name the skill where the work lives, or drop the exclusion. |
| Examples that break a rule | An example that contradicts any skill's rule, not only its own: a date from memory, an id instead of a reference number, a send without confirming, a real name. The assistant copies examples more faithfully than it follows rules. | Rewrite the example to obey every rule. |
| Written for the people in the room | A rule addressed to, or made the duty of, named people or a department ("Ana checks", "for the sales team:"), usually because the interview had those people in it. | Address the reader ("you") or the role; move "who" into who-owns-what if the company has it, otherwise drop it. |
| Dangling delegations | A body that says "see X" or "X handles this" where X does not exist, or does not say what is claimed. | Point at what exists, or add the missing part to X through wrangle. |
| Absolutes | An "always", "never", or "only" that fails in some situation the assistant can be in (a draft the person sends themselves, a system that is not connected, a different audience). | Narrow the rule to where it holds, or state the exception. |
| One home broken | The same rule in full in two skills, or a rule restated where a pointer would do. Layer B of the always-on block is the one sanctioned exception. | Keep the full statement in its home, point from everywhere else. |
| Summaries that add | A summary that introduces a name, number, or equivalence the source does not state. | Cut it back to what the source says. |
| Facts | A fact about the company that may have aged, or that the profile does not support. | Ask the admin; record the answer in the profile. |
| Exact facts | A phone number, email address, URL, postal address, registration or VAT number, bank detail, price, validity period, timeline, reference-number format, or opening hours in a skill or reference file without a confirmed `[you said]` or `[documents: ...]` line behind it. Picked up from a page or a search, it looks authoritative and is wrong until someone notices. | List it for the admin (round-up, "Exact facts"); confirm or correct it, and record the line in the profile. |
| Audience-scoped pointers | A skill for one audience pointing at a skill that audience cannot see. | Label the route ("internal-only", "restricted") or drop it. |
| Lists on two surfaces | The same list kept by hand in two places (systems, triggers, data classes), outside the two the routing mode regenerates and the two the stamp covers. | Keep one home and point at it. |
| Untrusted input | A skill that reads documents, mail, pages, or system output without the pointer to conduct's content-is-data rule. | Add the one-line pointer. |
| Stale references | A file under `references/` whose header date is over a year old. | Ask the admin for the current version. |
