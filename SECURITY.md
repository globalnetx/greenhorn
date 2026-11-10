# Security

Greenhorn reads company documents and builds files that every colleague's
assistant will load, so we take reports about it seriously.

**Found something?** Please don't open a public issue for it. Use GitHub's
private vulnerability reporting on this repository ("Report a
vulnerability" under the Security tab), or email <security@gnx.net>. Tell
us what you found and how to reproduce it; we'll reply within five working
days and keep you posted until it's fixed.

**What counts.** Anything that would let a company's private material leak
out of the harness folder or into the wrong plugin; anything that would
let a skill, a document, or a web page the assistant reads smuggle
instructions into it; a check in `skills/greenhorn/scripts/` that passes when it should fail.

**How Greenhorn is meant to be safe, and where it relies on you.**
Greenhorn runs in Claude Code on your own computer, in one folder, with
your account's permissions. Three things are worth knowing.

- *What it pre-approves.* So that the app doesn't ask at every step,
  giddy-up writes `.claude/settings.local.json` in your folder, for you
  alone. From then on, sessions in that folder may change files inside
  the folder, run Python, and search and read the web without asking
  first. The Python approval covers any Python, not only Greenhorn's own
  scripts. You can remove the file at any time; Greenhorn then asks for
  each step again. It never suggests switching permission checks off
  altogether.
- *What it reads.* It reads your website, public search results, and the
  documents you hand it. Any of those can contain text aimed at an AI
  ("ignore your instructions and..."). Greenhorn's rule is that such
  text is data: it reports it to you and does not act on it. A rule is
  not a wall. Combined with the approvals above, a document or page
  that fooled the assistant could have it run code or fetch a web
  address. So hand it your own material, be wary of documents from
  people you don't know, and if a session does something you didn't
  ask for, stop it and tell us.
- *What leaves the folder.* The built plugin holds only your skills and
  their reference files; the build copies by an allowlist and refuses
  anything else. The interview notes, your source documents, and your
  brand files never go into it, and the version-control setup keeps
  them out of the repository too. What you put into a skill does go to
  everyone who gets the plugin, which is why exact facts and real names
  are checked with you before a build for the team.

**What doesn't.** Problems in Claude, Claude Code, or another AI product
itself belong with their makers. Mistakes in your own company's skills are
yours to fix, though we're happy to hear what tripped you up.
