<!--
Title: Campfire, the staff handout
Date: 2026-11-10
-->

# Campfire: the staff handout

**Command:** `/greenhorn:campfire`. Offered once after the first team
publish; made again whenever the admin asks, and worth making again
after a chapter that adds a group of colleagues, a wrong-answer case, or
a skill from the parked list. Campfire is how the team hears about its
new colleague, in whatever form the admin wants: an email, a post in
the shared channel, a short note of instructions, a handout, or several
of these.

**Inputs:** the admin, first: what they want to say to the team, what
they want people to try first, which story to tell, what to leave out.
Then the finished folder. From the profile: the advocate and the channel
(Operations), the phase and the one the company is heading for, the
day-one list and the wrong-answer cases (Working with AI, written in the
"AI in our daily work" chapter), the typical case of the main offering
(What we offer), the data classes and routes (AI house rules), the
parked candidate skills (Open items), the maintainers and how often
things change (Operations), the language colleagues read best. From the
skills: the compass, the persona skill's introduction and behaviours,
the voice skill's tuned samples and de-AI pass, the
house-rules skill, the working-with-ai skill's check-before-trusting
table, the skill index in `README.md`, and the brand-assets skill when
there is one. The skills are read in full and followed while writing,
never summarised from their descriptions (router, "Use what the folder
already knows"): the handout is the first real test of whether the
assistant now knows the company.

**Outputs:** `handout/` in the company folder, holding whichever forms
the admin chose: `announcement.md`, the email, ready to paste;
`post.md`, the chat post; `note.md`, the short instructions; and for
the handout `handout.md`, the filled source, `handout.html`, the same
with the brand look, and `handout.pdf` when the session can print one.
A staff handout is read in ten minutes, so it is three to six printed
pages; the email is read in two, the post in thirty seconds.

The template is `templates/handout.template.md` in this skill's folder.
It carries the general craft of working with an AI colleague as fixed
text, and slots for everything that is the company's and the admin's
own.

## The gate

Campfire runs only when two things exist: the voice skill, built from
real writing with "How we sound" done, and a settled look, which means
the brand-assets skill or at least the palette and fonts confirmed in
the profile's Brand section. If one of them is missing, say so in one
sentence, name what is missing and which chapter supplies it ("How we
sound" for the voice, "Our look" for the brand), and offer that chapter
now with one card (do it now, recommended / not today). Nothing of the
handout is written until the gate is met. No handout is written
from a generic voice and default styling: a handout that reads like an
AI wrote it works against its own purpose. This is the rule in
`giddy-up.md`, "Enough to write", applied to the handout.

## What the handout is for

It introduces the team to a new colleague. Its job is engagement: get
people to try the assistant this week on something real, help the ones
who like it become the people others ask, and bring the company into
working with AI with the team on board. Not everyone will come along,
and that is fine; the handout is written for the ones who might, never
against the ones who will not.

So it reads as a story, not a manual: a colleague introducing a new
colleague to the team, in the company's voice, warm and short and
concrete, with no rollout language, no fear, and no hype. It opens with
the advocate's note, then the new colleague introduces itself in its
own words, as an AI and saying so: what it was taught, what it is here
for, how to brief it, what it does not know. Then the practical part,
in one order: getting started, what to check, the ground rules, where
this goes next, where to go with questions. Bullets and the one table
are kept for that practical part. The advocate
signs it, and the handout is theirs in a stronger sense than the
skills are: it is the one piece of the harness every colleague reads,
and what the admin wants said in it matters more than anything the
profile holds.

## Ask the admin first

The handout is made with the admin, not for them. Before a word is
drafted, a short conversation in plain chat, their own words asked for
and taken as given. Not a form: one question at a time, the next one
shaped by the last answer, and nothing asked that the profile already
answers.

- **What do you want to say to the team?** In their own words, as if
  they were telling a colleague over coffee why this exists and what
  they hope people do with it. This becomes the note at the top. Ask
  whether they want to write it themselves or be helped: helped means
  two or three questions (why now, what they hope people try, the one
  worry they want to settle), a draft from the answers in the voice,
  and their edits taken as they are. Never rewritten into something
  they would not say.
- **The assistant introduces itself.** Say that the handout has a
  section written by the assistant in the first person, labelled as
  its own words: an AI, saying so, with no human name and no invented
  feelings or history (the honesty rule in the voice skill). It grows from the
  introduction paragraph in the persona skill, and is headed with the
  name when the persona has one; without a name, "your new colleague".
  Ask what the admin wants it to be sure to say, and what it must not
  say. The section is read back in full and the admin can strike any
  line.
- **What should people try first?** For each main group of colleagues:
  the one or two asks the admin would put in front of them on day one.
  The day-one list from the interview is the starting point, read back
  for them to pick from and add to.
- **Which story do you want to tell?** A win the admin saw, a moment
  the assistant surprised them, or the wrong-answer case they are
  comfortable sharing with everyone. One story, told in the handout as
  a before-and-after with the real draft behind it. If they would
  rather keep the wrong-answer case out, it stays out.
- **What are people worried about?** Job fears, "is this allowed",
  customers noticing, getting it wrong in front of a client. The
  handout answers the real worry in the section where it belongs,
  never with a reassurance paragraph of its own.
- **What should stay out?** Anything the admin does not want in
  writing yet: a parked skill they are not ready to promise, a group
  that is not on board, a rule still being argued.
- **How formal?** The tuned voice samples set the register; the admin
  says whether the handout sits at the warmer or the plainer end of it,
  and whether the advocate writes in the first person throughout or
  only in the note.

With the question tool, once: the phase to show and the one the
company is heading for, which parked skills may be named as "next up",
and the language, when the profile has two and they differ. Write the
answers into the profile under a "Handout" heading, tagged
`[you said]`, so the next campfire starts from them instead of asking
again; read back only what changed.

## Which form

Ask, with the question tool, which forms they want, more than one
allowed, and recommend from how the company talks to itself (the
profile's Operations section: the channel, how people use the
assistant, how big the team is):

- **An email announcement.** The advocate's note, one paragraph from
  the assistant's own introduction labelled as its words, two or three
  asks to try this week, the ground rules in four lines, where to go
  with questions. Two minutes to read, pasted
  into their mail client under the advocate's name. The usual first
  form, and often enough on its own for a small team.
- **A post in the shared channel.** The same in a hundred to a hundred
  and fifty words, in the register of the channel, saying plainly that
  the new colleague is an AI, with one ask to try and the invitation to
  post what worked. Where the channel is
  new, this is its first post.
- **A short note of instructions.** For a team that wants the practical
  part only: how to ask, what to check, the ground rules, where to go.
  One page, no story.
- **The handout.** The full story below, as a PDF or a page, for a
  company that onboards with a document and wants something to keep.

Every form is cut from the same material and says the same things in
the same voice, so a colleague who reads two of them hears one
colleague. Not the same sentences, though: a list that appears word for
word in the email, the post, and the handout reads as pasted. The
confirm rule is the exception; it has one wording, the conduct skill's,
in every form and every section. The handout's template is the long form; the short forms are
in the template under "Short forms", each a cut of it with its own
slots. The admin's answers from "Ask the admin first" fill all of them;
the story and the sample go into the handout only, and into the email
when the admin wants it there. When several forms are chosen, write the
handout first and cut the others from the corrected text, so a change
at read-back lands in all of them.

## Filling the template

Work through the template top to bottom. Every slot is filled from the
admin's answers first, then the profile or a skill, in the company's
voice; the voice skill's register dial and its de-AI pass apply to
every line, because this is prose the whole company will read. Where
there is nothing for a slot, the slot and its sentence go, never the
section's point; the parts marked "only when" in the template are left
out whole when their source is missing or the admin said no. Three
voices, kept apart: the advocate's note in the admin's words, the
assistant's introduction in its own first person, and the practical
part in the company's plain voice.

1. **The note from the advocate.** The admin's own words from "What do
   you want to say", four to six sentences, first person, signed with
   the advocate's first name and role. Their reason for doing this, when
   they gave one, stays in. One sentence that it does not replace
   anyone's judgment, and the hand-over line to the next section ("I
   asked it to introduce itself; the next section is its own words").
   Edit for the voice, never for substance.
2. **Hello from your new colleague**, or "Hello from <name>" when the
   persona skill has a name. Written by the assistant in the first
   person, under the line "Written by the assistant itself", in the
   company's voice, from the persona skill: its introduction paragraph
   is the opening, as written, and its behaviours set how the rest
   comes across. Four paragraphs: who I am and what I was taught,
   from the compass and the profile, as things a colleague would notice
   (what we are and are not, the unwritten rules, the reference formats,
   how we write, who owns what, the look), never a skill name; what I am
   here for, from the day-one list and the first-month uses, with "I
   draft, you read and send under your name" and what I can reach when
   a system is connected; how to brief me, the five parts in a sentence
   and the three or four habits from the working-with-ai skill that
   matter most here, "ask me how to ask" among them, then the confirm
   rule in the conduct skill's wording as "the rules we agreed"; what I do
   not know, and, only when the admin wants it in, one thing I got
   wrong and which rule now stops it, with nothing the profile does not
   say, ending with "when I get something wrong, tell [the advocate]".
   Plain that it is an AI; no human name, no invented feelings or
   history; no "I'm excited". This is the section the read-aloud test is hardest
   on.
3. **Getting started.** One line, then one paragraph per main group,
   "If you are a ...", with the asks the admin chose woven into the
   sentences in quotation marks, each a brief the reader can copy: the
   task, the reference or customer as a colleague would say it, who it
   is for, what good looks like. Each is an ask the published skills
   answer well today, with placeholder names; nothing aspirational,
   that goes under "Where this goes next". Then the story the admin
   chose as a before-and-after in prose, with the voice skill's tuned
   sample quoted in full, placeholder names kept, signed the way the
   sample is signed or with the advocate's first name; when the sample
   is bad news, one line that this is where people hesitate and where
   it helps most.
4. **Before you trust an answer.** The working-with-ai skill's table,
   reworded for a reader who is not the assistant. Keep its rows; add
   none. The practical part starts here, and tables are fine from here
   on.
5. **The ground rules.** The data classes and the routes from the
   house-rules skill, one phrase each, in plain words. The confirm rule
   and the honesty rule from conduct and voice, one line each. Who
   agreed the rules and which policy they sit under, from the profile.
   This section is read by the sceptics and by whoever agreed the rules,
   so it says what the skill says: nothing softened, nothing added, no
   second wording of a rule that has one home. The worry the admin
   named is answered here when it is about permission.
6. **Where this goes next.** One paragraph: where the company is today
   and what it is heading for, for whom first, in the words of the
   three phases but without the table, and that moving on is a choice
   made together. Then the parked skills the admin allowed as "next up,
   if you want them", one line each with the role who would help shape
   them, never with a date.
7. **Where to go with questions.** The advocate, in the first person
   when the note is, as the colleague with the open door, with "it got
   this wrong" framed as welcome news; the channel by name, for
   questions, ideas, wins, and gaps, with the invitation to post what
   worked and the ask that produced it; who keeps it current and roughly
   how often; and that everything it says about the company traces to
   something a colleague said or handed over.

Then the self-check's prose rules over the whole text: placeholder names
only, no secrets, nothing the profile or the admin does not support,
every pointer lands. Product names do not belong in it, except the
company's own system when a route names it. Staff names appear only
where the who-owns-what exception allows them: the advocate and the
maintainers by name, everyone else by role.

## It has to read as something a colleague wrote

Run the finished text through the voice skill's de-AI pass and the quiet
rule, then read it once more as the sceptical colleague who will get it
in their inbox. Out go: em and en dashes; any sentence a person would
not say out loud to a colleague; spelled-out obviousness; "we're excited
to"; offers of further help; a closing summary; a bullet list where a
sentence would do; the "it is not this; it is that" turn more than once
in the whole piece; a paragraph that lists every habit; anything that
makes the reader feel managed. In
stay: short sentences, the admin's and the company's own words, and the
register the tuned samples chose. The read-aloud test is the advocate
saying it to their own team; a paragraph that fails it is rewritten or
cut. The handout is the one piece of the harness every colleague reads,
so this pass is not optional.

## The look

From the brand-assets skill, when there is one; without it, from the
palette and fonts confirmed in the profile's Brand section, which the
gate requires, and say that the skill itself is still to come.

- **Palette.** The primary colour for headings and the cover band; body
  text in the body colour on white; the accent for one highlight per
  page at most, never for body text; the light tint for table header
  rows and the quoted sample.
- **Fonts by name**, with a fallback stack: the heading face for
  headings, the body face for text and tables. Load them the way the
  skill says (usually from a public font service by name); when that is
  not possible, the system's default sans-serif, and say so in the
  read-back. Font files are never copied into the folder for this.
- **The mark** at the top of the first page and in the footer, at the
  size and clear space the skill gives, never recoloured. Use the logo
  file the skill names; the full wordmark only when the skill carries it.
- **Layout.** A cover band in the primary colour with the title, the
  company name, and the date; then one column, generous margins, tables
  with the light header row and no vertical lines, and the mark with
  the company's name in a footer that repeats on every page, with page
  numbers where the renderer can count them. A4 or Letter by the
  company's country.

The look is applied in `handout.html`: a single file with the styles
inside it, the mark inline, and the fonts named. The Markdown source
carries no styling.

## Read-back and render

1. **Save the draft** as `handout/handout.md` (or `announcement.md`,
   `post.md`, `note.md` for the short forms) and read it back section
   by section, the way "Who decides what" in the router says, with the
   note, the assistant's introduction, and the story in full since they
   go out under a name, and the rest as its main points in easy
   language; an email or
   a post is short enough to show whole. The admin changes what they
   like, in their words; those edits are taken as they are, and only
   checked against the ground rules and the facts. Whatever the form,
   it is theirs to send: the assistant never posts or mails it.
2. **Render**, for the handout only; an email or a post is pasted as
   text, and a note is a page. Write `handout/handout.html` from the corrected source
   with the look above. Then the PDF, by whatever the session has, in
   this order: a document tool in the session that prints HTML or
   Markdown to PDF; a browser on the computer that can print a page
   headless (on a Mac, Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
   with `--headless --print-to-pdf`; on Windows, Edge with the same
   flags), saying first that it will run the browser once for this;
   else no PDF: say that `handout.html` opens in any browser and prints
   to PDF from there, which is the fallback. Check the PDF opens, has the
   fonts (or the fallback, said so), and is small: under a megabyte, so
   it can go in an email.
3. **Say where it is**: the files, the page count, and that the
   source is the one to edit next time; campfire re-renders it. Nothing
   in `handout/` goes into the plugin; the build copies only `skills/`.
   It is fine to commit, when the folder is under version control.

## The general part

The handout's fixed text is deliberately short. The craft behind it, for
when the admin asks why a line is there or wants the working-with-ai
skill to say more, is in `working-with-ai-craft.md`: the five-part
brief, the three phases, the habits, "ask it how to ask", and why the
examples are the company's own.

## What the admin sees

A short conversation about what they want to say, what people should
try first, which story to tell, and what stays out; one card for the
forms they want, and one for the phase, the next-up skills, and the
language; each draft to read and change, section by section; then the
files and where they are, with the page count and which renderer was
used or why there is no PDF, and for an email or a post the text in a
fence, ready to paste.
