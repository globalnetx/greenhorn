<!--
Title: Round-up, the checks and the audit report
Date: 2026-11-10
-->

# Round-up: the checks and the audit report

**Command:** `/greenhorn:round-up`. Also run by roll-out before every
build, by wrangle after every change, and by giddy-up after every round
of skills.

**Inputs:** the folder, and `harness-profile.md` for tracing claims.

**Outputs:** one plain-language report. Round-up changes nothing; every
fix it proposes goes through wrangle or reins, each said in a sentence.

## Steps

1. **The mechanical checks.** From the company folder, run the checker
   with `--strict` and the secret scanner (commands in the router, "The
   scripts"). Every finding comes with a file and a line. Translate each
   one into a plain sentence and a suggested fix. The scanner reads the
   whole folder. A finding in `skills/` or `README.md` would ship. A
   finding in `sources/`, `brand-sources/`, or the profile does not ship,
   but the folder is backed up: the admin removes the credential from
   that file, and changes it if it is real.
2. **The judgment pass.** Read every skill, with `audit-traps.md` as the
   list of what to look for: overlapping descriptions, pointers in a
   skill's body that do not land, absolutes, examples that break a
   sibling's rule, a rule stated in two homes, summaries that add claims,
   facts that may have aged, and pointers a reader of that audience
   cannot follow.
3. **Untraceable claims.** For every factual claim about the company in a
   skill (a service, a figure, a name, a promise, a "we never"), find the
   line in the profile that supports it with a confirmed tag. List each
   claim with no such line: the skill, the line, the claim, and what is
   missing (no profile line, or only an unconfirmed one). Without a
   profile, say that no claim can be traced, and skip this step.
4. **Exact facts.** Values picked up along the way (the website read, a
   search, a document) end up in a skill looking authoritative, and a
   wrong one goes unnoticed until it has caused trouble: phone numbers,
   email addresses, URLs, postal addresses, company registration and
   VAT numbers, bank details, prices, validity periods and timelines,
   reference-number formats, opening hours. Gather every such value
   from every skill and reference file into one list: the skill, the
   line, the value, and the profile line and tag that supports it, or
   "none". A pass with patterns finds the candidates (digits with
   separators, an @, http, words like VAT, IBAN, registration);
   reading finds the rest. A value is covered when its profile line is
   tagged `[you said]` or `[documents: ...]`, which is what the yes on
   a round's summary leaves behind (`giddy-up.md`, "Each round").
   Covered values are not shown again. A value that is not covered
   goes under "Exact facts" in the report, for the admin's yes or
   correction; one that the profile contradicts goes under "fix before
   publishing". Values with placeholder names (an example order
   number, a sample price marked as such) are checked the same way,
   labelled as example values, since they get copied.
5. **Stale references.** For each file under a skill's `references/`, read
   the date in its header. Flag any source dated more than a year ago, so
   the admin can check for a newer version.
6. **Write the report** (below).
7. **Offer the fixes**, starting with "fix before publishing". Each fix is
   a wrangle or reins change, said in a sentence for a yes or no.

## The report

One line first, from the profile's "Where we are": which chapters are
done, which are parked, and how many open items there are. Then three
groups, in the order below.

Every finding from the judgment pass and the untraceable-claims list is
labelled **(judgment)**: it is the assistant's reading, not a mechanical
fact, and the admin decides. Mechanical findings carry no label.

When everything is clean, say so in one line and stop.

### Fix before publishing

Every checker error, every warning (the build uses `--strict`), every
secret-scanner finding in `skills/` or `README.md`, and judgment
findings that would make the assistant wrong or unsafe: an example that
contradicts a rule, a pointer to a skill that does not exist, a claim
or an exact value the profile contradicts.

### Worth a look

Everything else: overlaps, absolutes to verify, stale references,
untraceable claims the admin may simply confirm, and scanner findings
in files that never ship.

### Exact facts

Only the values from step 4 that no confirmed line covers, one line per
value with where it is, for the admin to confirm or correct in one go.
On the yes, re-tag their profile lines `[you said]` and record `exact
facts confirmed <date>` under "Where we are" in the profile; roll-out's
readiness check reads that line. When every value is already covered,
this group is one line: how many exact values there are and the date
they were confirmed. The whole list, with what supports each value, is
shown only when the admin asks for it.

## What the admin sees

A short report in three groups, each finding one line with the file, what
is wrong, and the fix, and any exact values still to confirm, followed
by "Shall I start on the first group?" when there is something to fix.
