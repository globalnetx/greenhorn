# Contributing

<img src=".github/assets/poses/has-a-question.svg" width="150" align="right" alt="Greenhorn, a pixel-art cow in a cowboy hat, holding a clipboard with a question mark over its head.">

Thank you for the interest. Greenhorn is public and at version 0.1, a
pre-release: it works end to end, and it's still finding its feet. Anyone
is welcome to help make it better.

**What helps most right now.** Tell us how it went. Run it on a company,
yours or a made-up one, and open an issue with what confused you, what it
got wrong, what was missing, and what worked. A transcript of the moment
it went sideways is worth more than a paragraph about it. Scrub anything
private first.

**Ideas and bigger changes.** Open an issue before you write the code or
the prose, so the shape can be talked through first. We do our best to
read what comes in. We can't promise a reply, a timeline, or that a
suggestion makes it in: Greenhorn stays small on purpose, and some good
ideas belong in a company's own folder rather than in the tool.

**Bugs and typos.** Small fixes are welcome as pull requests any time.
Read the skill's [`conventions.md`](skills/greenhorn/references/conventions.md)
and [`schema.md`](skills/greenhorn/references/schema.md) first; they're
short, and the checks in `skills/greenhorn/scripts/` enforce them. Run the
checks before you push:

```sh
python3 skills/greenhorn/scripts/check_harness.py --strict
python3 skills/greenhorn/scripts/check_harness.py --strict examples/parcelona
python3 skills/greenhorn/scripts/scan_secrets.py
python3 skills/greenhorn/scripts/build_plugin.py --self-test
python3 skills/greenhorn/scripts/init_repo.py --self-test
npx -y markdownlint-cli2 "**/*.md" "!**/references/**"
```

**Writing.** Plain, warm, short sentences, the way a colleague talks. Say
what the reader needs and stop. No company names other than the fictional
ones (Parcelona Logistics, Tulipware, Nordlicht Optics). No secrets, ever;
the scanner checks, but don't rely on it.

**Working with AI.** Greenhorn itself was written with AI, and
contributions made that way are welcome. Read what your assistant wrote
before you send it, run the checks, and have a second reader, human or
AI, go over a change to the skill; that habit catches more than we like
to admit.

**Security problems.** Not in a public issue, please. Use "Report a
vulnerability" under the repository's
[Security tab](https://github.com/globalnetx/greenhorn/security).

**Licence.** By contributing you agree your contribution is licensed under
the repository's Apache 2.0 licence.
