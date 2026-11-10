<!--
Title: Homestead, version control
Date: 2026-11-10
-->

# Homestead: version control

**Command:** `/greenhorn:homestead`. Optional. Suggested when a second
maintainer appears (the profile's Operations section names two or more)
or when the admin wants a history of changes; never a step a publish
depends on.

**Inputs:** the folder; the profile's Operations section (maintainers,
how often things change, how the folder is backed up); whether the
company has a GitHub organisation, a developer colleague, or an IT
person with a view on where company repositories live.

**Outputs:** the folder as a Git repository on `main`, with an ignore
list that keeps the sensitive files out, a licence note, Greenhorn's two
checks under `tools/` and a workflow that runs them on every change, and
one first commit. Then the admin's chosen route to a private repository
on GitHub, with the second maintainer invited, and a short addition to
the folder's house rules.

This reference is advice from someone who has set up a dozen of these,
not a manual. The admin hears the arguments, picks a route, and is
walked through it one step at a time.

## When to suggest it

- The confirmations card or a later chapter names a second maintainer.
  Two people editing one folder on a shared drive overwrite each other
  sooner or later; a repository is how they do not.
- The admin asks for history ("who changed this?", "can I go back?").
- The folder has been copied to a drive for backup a few times and the
  admin is tired of it. A private repository on GitHub is a decent
  backup, said with the caveat below.

Never in the opening of giddy-up, never before the first publish, and
never as a condition for anything else.

## The arguments, in plain words

What it gives this folder: a history of every change, with who made it
and why, in their own words; a way back to any earlier version; a second
maintainer working on the same folder without overwriting the first;
the checks running on every change, so a broken skill is caught before
it is published; and the public-or-private choice made once, at the
start, and then kept.

What it costs: a little ceremony per change (a message, a button), and
a few new words. And one honest caveat: a repository is not a backup by
itself. The folder on the admin's computer is still the folder; the
copy on GitHub is the backup, and only once it is pushed there, and only
for what the ignore list lets through. The profile and the sources stay
on the computer and still need their own copy somewhere the admin
controls, as before.

Two sentences for the admin, then: a repository gives the folder a
history and lets a colleague work on it with you safely. It is not
needed to publish, and the sensitive files stay out of it.

## The sensitive-files decision

By default `harness-profile.md`, `sources/`, and `brand-sources/` never
go into the repository, together with `dist/`, built zips, local notes,
and machine files. These hold real names, internal documents, and the
unscrubbed interview, and a private repository on GitHub is still a copy
on someone else's computer. Say that in one sentence.

If the admin wants any of them in anyway, it is their decision, made
after a scrub and knowing who can read the repository, and the script
takes it as `--include`. Either way, record the decision in the
profile's Operations section, in one line:

```text
- Version control: private repository, <where it lives>, maintainers <names>.
  harness-profile.md, sources/, and brand-sources/ stay out. [you said]
```

## Choosing a route

Offer two, with the question tool, and recommend by who the admin is.
The route is chosen before the script runs, because the script needs
git on the computer, with a name and an email set, and each route
brings those its own way.

- **GitHub Desktop, no command line.** For most admins. A free app for
  Mac and Windows with buttons for everything below.
- **git and the gh command line.** For an admin who is comfortable in a
  terminal, or whose developer colleague is. Fewer clicks, same result.

Before either, the sane choices, said once as the recommendation and
not as a lecture:

- **Private.** Always, for this folder. The ignore list keeps the worst
  out, but the skills still describe how the company works.
- **Owned by the company**, not by a person. If the company has a GitHub
  organisation, the repository goes there. If not, a company-controlled
  account (one IT or the company itself owns) rather than the admin's
  personal one, so the folder does not leave with them. If the company
  has a developer colleague or an IT person, they will have a view on
  this; ask them before publishing, since moving a repository later is
  a chore. Without either, the Desktop route below is enough on its own.
- **The second maintainer as a collaborator**, by invitation, with
  write access. Nobody else needs access to make the plugin work; the
  plugin is uploaded, not read from the repository.
- **Protect `main` lightly or not at all** at this size. Two
  maintainers who talk to each other do not need a review gate; the
  checks on every push are the gate.
- **Never force-push**, and never rewrite history to remove a file that
  should not have been committed: once pushed, treat it as seen, change
  any secret it held, and remove the file in a new commit.

## Running the script

1. **Get git ready, by the chosen route.** For GitHub Desktop: install
   it and sign in first (route one, step 1), which sets git's name and
   email. Desktop's own copy of git is not on the command line, so on
   Windows git itself is installed too, from git-scm.com; on a Mac the
   command line tools include it, and `git --version` offers to install
   them when they are missing. For the
   command line route: install git and gh and sign in (the first lines
   of route two). Done in this order, the dry run below has nothing to
   refuse on that score.
2. **Say what it will write**, in a few lines: the ignore list, a
   licence note that defaults to "proprietary, internal use only" in the
   company's name, a NOTICE crediting Greenhorn's Apache-licensed
   templates (the company's own skills stay the company's), copies of
   the checker and the secret scanner under `tools/`, and the workflow
   that runs them. Then the first commit, of everything the ignore list
   allows. No repository exists on GitHub after this; that comes with
   the rest of the chosen route.
3. **Dry run first.** From the company folder, with the skill folder's
   real path in place of the variable, as the router says:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/init_repo.py" --dry-run .
   ```

   Read it back: what will be written, what stays out and which of
   those are present in the folder, and how many files the first commit
   will hold. Every line starting `REFUSED` is one thing to settle; the
   script explains each in plain words, and it writes nothing while one
   stands. The one refusal that can come after writing, a sensitive
   file that a line in an existing `.gitignore` un-ignores, puts the
   folder back as it was and says so.
   The ones that need the admin: git is missing or has no name and
   email yet (step 1 was skipped; go back to it), or the folder is
   already a repository or sits inside one.
4. **Run it** without `--dry-run`, with `--include` for any sensitive
   file the admin decided to commit, and `--owner` when the licence
   note should carry a name other than `plugin-author` from
   `harness.yaml`. Then say what happened: the branch, the number of
   files in the first commit, and what was kept out. The script refuses
   the commit itself if a sensitive file is about to go in, so a clean
   result means the ignore list held.
5. **Add the house-rules section** ("What changes in the house rules")
   to the folder's `HOUSE-RULES.md`. It is committed with the message
   "House rules for the repository" as the first change once the
   repository is published: route one, steps 7 and 8, or route two's
   day-to-day lines.

The script is route-neutral: it prepares the folder, and both routes
below continue from the folder it leaves. Running it again later, with
`--force`, refreshes the copies under `tools/` and the workflow after a
Greenhorn update and adds any line missing from the ignore list;
`LICENSE` and `NOTICE` are left as they are (a company that re-licensed
its folder keeps that; `--replace-licence` writes the defaults again on
purpose). A line the admin removed from the ignore list to commit a
sensitive file comes back on a refresh unless `--include` names that
file again, so the recorded decision in the profile is what to read
before running it.

## Route one: GitHub Desktop

Step 1 comes before the script runs; the rest follows it. Menu labels
below are as GitHub's documentation gives them; the pages and the day
they were read are in "The facts" at the end. The Mac and
Windows labels differ in capitalisation only.

1. **Install and sign in.** From desktop.github.com, "Download for
   macOS" or "Download for Windows"; it needs macOS 12.0 or later, or
   Windows 10 64-bit or later. Open it and sign in to GitHub.com from
   its first screen, with the account the repository should be made
   under (the sane choices above). Signing in also tells git the
   admin's name and email, which the script needs for the first commit
   (known from use; the facts section says so), which is why this step
   comes before the script runs.
2. **Add the folder.** In the menu bar, "File", then "Add Local
   Repository" (on Windows, "Add local repository"). Click "Choose...",
   pick the company folder, then "Add Repository" ("Add repository" on
   Windows). Dragging the folder onto the GitHub Desktop window does
   the same. Because the script already ran `git init`, Desktop takes
   the folder as a repository with one commit in it and opens it.
3. **Publish it, private.** In the repository bar, click "Publish
   repository". In the "Publish Repository" window: the name is
   prefilled from the folder; give it a one-line description; make sure
   **"Keep this code private" is ticked**; if an "Organization"
   drop-down shows, pick the company's organisation rather than the
   admin's own account; then click "Publish Repository". The
   documentation does not say whether the private box is ticked by
   default, so look at it every time rather than assume.
4. **Check it is private.** Open the repository on GitHub.com (in
   Desktop, "Repository", then "View on GitHub"). The word "Private"
   sits next to the repository name at the top of the page. If it says
   "Public", stop and change it under "Settings", at the bottom of the
   General page, under "Danger Zone", "Change repository visibility".
5. **Invite the second maintainer.** On the repository page on
   GitHub.com: the "Settings" tab, then in the "Access" section of the
   sidebar, "Collaborators & teams". Under "Manage access", "Add
   people", search for the colleague's GitHub username or email, pick
   the role "Write" under "Choose a role", and click the "Add ... to
   ..." button. GitHub sends them an invitation to accept; until they
   do, they see nothing. A private repository on a free account can
   have collaborators.
6. **The second maintainer's side.** They install GitHub Desktop, sign
   in, accept the invitation, and clone the repository: "File", "Clone
   Repository...", pick it from the list, choose where it goes on their
   computer. They get the folder without the profile, the sources, or
   the brand sources; that is by design, and they take those from the
   admin by another route if they need them.
7. **How a change becomes a commit.** After Greenhorn (or a person)
   changes a file, Desktop lists it under the "Changes" tab on the
   left, with the exact lines changed on the right. Before committing,
   the checks run in the folder ("Before any publish" in the house
   rules). Then, at the bottom left, type what changed and why in the
   "Summary" field, in plain words ("Glossary: add the difference
   between a quote and an estimate"), optionally more in "Description", and click "Commit to
   main". The change is now in the local history.
8. **How it gets to GitHub.** Click "Push origin" in the repository
   bar. That sends the new commits up, and the checks start on GitHub
   shortly after. The other maintainer gets them next time they click
   "Fetch origin" (the same button, which changes name when there is
   something to pull; known from use), then "Pull origin". Pull before
   starting a
   change, push after finishing one, and two people rarely collide; when
   they do, Desktop says so and shows both versions to choose from.
9. **When the checks fail on GitHub.** The commit gets a red cross on
   GitHub.com, and GitHub emails whoever pushed it. Open the
   repository's "Actions" tab, click the failing run, then the job, and
   the step that went red shows the same plain-language findings the
   checker and the scanner print locally, with file and line. Fix them
   in the folder (wrangle for a skill, reins for the block), commit,
   push again. For a branch with a pull request, Desktop shows the
   checks badge next to the branch name, red for failing, and a system
   notification when checks fail; the "Re-run" button there re-runs
   them, which is for a flaky run, not for a real finding.

## Route two: git and gh on the command line

For an admin at home in a terminal. Before the script: on a Mac with
Homebrew, `brew install git gh`; on Windows, the Git for Windows
installer from git-scm.com and the gh installer from cli.github.com (or
`winget install Git.Git GitHub.cli`). Then sign in:

```bash
gh auth login
```

Pick GitHub.com, HTTPS, and the browser flow; sign in with the account
the repository should be made under. If git has no name and email yet,
set them with `git config --global user.name` and `git config --global
user.email`. After the script, the folder is a repository with one
commit on `main`, so the rest is short.

```bash
gh repo create <organisation-or-account>/<company>-ai --private --source=. --remote=origin --push
```

Run from the company folder. `--private` is the one flag that must not
be forgotten; `--source=.` uses the existing folder rather than making
a new one; `--push` sends the first commit up. Then invite the second
maintainer on the repository's Collaborators page on GitHub.com (route
one, step 5), or in one line:

```bash
gh api --method PUT "repos/<organisation-or-account>/<company>-ai/collaborators/<their-username>" -f permission=push
```

Day to day: `git pull` before a change, the two checks, then
`git add -A`, `git commit -m "Glossary: add demurrage versus detention"`,
`git push`. The ignore list does the rest; `git status` never lists the
profile or the sources, and if it ever does, stop and look at
`.gitignore` before adding anything.

The pitfalls, named once: `git add -A` after someone deleted a line
from `.gitignore` commits the profile; `gh repo create` without
`--private` makes a public repository, and the skills are the company's
inner workings; a repository created under a personal account belongs to
that person's GitHub account, and moving it later is a chore; `git push
--force` rewrites history the other maintainer has, so it is never used
here.

## What changes in the house rules

Once the folder is a repository, add this section to the folder's
`HOUSE-RULES.md`, after "Before any publish", with the folder's own
names in place of the brackets:

```markdown
## The repository

This folder is a private repository at [where]. [Maintainer] and
[maintainer] push to it.

- Commit after the two checks pass, never before; the same checks run
  on GitHub and mark the commit red when one fails.
- One change per commit, with what changed and why in the message, in
  plain words.
- Pull before starting a change, push after finishing one.
- `harness-profile.md`, `sources/`, and `brand-sources/` stay out of
  the repository; the ignore list keeps them out, and a line removed
  from it is a decision recorded in the profile first.
- Never force-push. A file that should not have been committed is
  removed in a new commit, and any secret in it is changed.
- After a Greenhorn update, homestead refreshes `tools/` and the
  workflow; nothing under `tools/` is edited by hand.
```

Commit it as the first change on the route the admin chose; it doubles
as the walkthrough's practice run.

## The facts

What the walkthrough says about GitHub Desktop and GitHub.com comes from
GitHub's own documentation, read 2026-11-10. The pages show no date of
their own. Menu labels change more often than rules; re-read these
before a release and move the date.

- **Adding a folder:** docs.github.com, "Adding a repository from your
  local computer to GitHub Desktop". Mac: "File", "Add Local
  Repository", "Choose...", "Add Repository". Windows: "File", "Add
  local repository", "Choose...", "Add repository". Dragging the folder
  onto the window also works.
- **Publishing:** docs.github.com, "Creating your first repository
  using GitHub Desktop". The repository bar button "Publish
  repository"; the "Publish Repository" window with "Name",
  "Description", the "Keep this code private" checkbox ("if you leave
  this option unselected, other users on GitHub will be able to view
  your code"), the "Organization" drop-down "if present", and the
  "Publish Repository" button. The page does not state the checkbox's
  default. After publishing, "Push origin" is the same button.
- **Committing:** docs.github.com, "Committing and reviewing changes to
  your project in GitHub Desktop". The "Changes" tab, the "Summary"
  field with an optional "Description", the "Commit to BRANCH" button,
  which reads "Commit to main" on `main`.
- **Pushing:** docs.github.com, "Pushing changes to GitHub from GitHub
  Desktop". "Push origin" in the repository bar; a "New Commits on
  Remote" window with "Fetch" when the other maintainer pushed first.
- **Inviting a collaborator:** docs.github.com, "Managing teams and
  people with access to your repository". The repository's "Settings"
  tab, the "Access" section, "Collaborators & teams", "Manage access",
  "Add people", then "Choose a role" and "Add NAME to REPOSITORY".
- **Checks:** docs.github.com, "Viewing workflow run history" (the
  "Actions" tab, the workflow, the run, the job and step logs) and
  "Viewing and re-running checks in GitHub Desktop" (the checks badge
  next to the branch name for a pull-request branch, "a red cross for
  failing checks", a system notification when checks fail, "Re-run"
  and "Re-run Failed Checks").
- **Installing:** docs.github.com, "Installing GitHub Desktop". "Download
  for macOS" and "Download for Windows"; macOS 12.0 or later, Windows 10
  64-bit or later; "Linux is not yet supported".
- **Cloning:** docs.github.com, "Getting started with GitHub Desktop".
  "File", then "Clone Repository...".

Known from use, not from the pages, 2026-11-10: GitHub Desktop brings
its own copy of Git for its own use, so the app works on a computer
with no git on the command line; signing in to Desktop sets git's name
and email for the command line too, from the account, and they can be
changed in Desktop's settings under Git; "Keep this code private" has
been ticked by default in recent versions; the "Push origin" button
reads "Fetch origin" when there is nothing to push, and "Pull origin"
when the remote has new commits; the checks on GitHub start shortly
after a push; a collaborator receives the invitation by email and sees
nothing until they accept; GitHub emails the author of a push whose
workflow fails, and shows a red cross next to the commit on the
repository page; a private repository on a free personal account can
have collaborators; the word "Private" or "Public" appears next to the
repository name, and visibility changes under "Settings", "General",
"Danger Zone", "Change repository visibility".

## What the admin sees

The two-sentence explanation and the arguments; the list of what stays
out, for their yes; the route choice with a recommendation, and that
route's install and sign-in; the script's dry run read back, then its
result; and then one step at a time,
with the check at the end that the repository says "Private" and the
colleague has accepted.
