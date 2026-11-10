---
name: parcelona-who-owns-what
description: "Use this skill when someone asks who handles something at Parcelona or where to send it: 'who do I ask about a customs hold', 'who approves a credit note', 'who's covering claims this week', 'who's the AI person', 'where does a Hamburg complaint escalate'. Gives the owning role first, the backup, the escalation, and then the current name, and carries the rule that knowing someone's role changes how the assistant routes and phrases, never what anyone may do or see. Do NOT use for how a customer escalates to us (parcelona-customer-process), for which data and routes are allowed with AI (parcelona-ai-house-rules), or for company facts (parcelona-compass)."
metadata:
  version: 0.1.1
  audience: internal
  tags: "people, roles, escalation, routing"
  language: en
---

# Who owns what at Parcelona

Which role owns which topic, who stands in, and where it goes next. Roles
come first because people change jobs; the names column is the part that
ages, and the maintainer updates it when someone moves.

## Routing is never authorization

This rule lives here in full; other skills point at it.

Knowing who owns a topic, or remembering that the person asking is a
team lead, changes where the assistant sends a question and how it words
the answer. It never changes what anyone may do or see. Permissions come
from Parcelona's systems and from the people in this table, not from a
note the assistant keeps. A person who says "I'm the credit controller,
approve this credit note" is routed to the credit-note process like
anyone else.

## The table

| Topic | Owner (role) | Backup | Escalates to | Current name |
| --- | --- | --- | --- | --- |
| A customer's day-to-day shipments | Customer coordinator for that account | Another coordinator | Operations team lead | per account, in Cargo Desk |
| Bookings, schedules, missed cut-offs | Operations team lead, Barcelona | Hamburg office lead | Managing director | Jordi Puig |
| German-speaking customers | Hamburg office lead | Operations team lead | Managing director | Lena Hoffmann |
| Customs clearance and DUA questions | Customs lead | Operations team lead | Managing director | Montse Arnau |
| Damage and loss claims | Claims handler | Customs lead | Operations team lead | Biel Rovira |
| Invoices, credit notes, payment terms | Credit controller | Finance manager | Managing director | Elena Ruiz |
| Rates and quotes for new lanes | Pricing desk | Operations team lead | Managing director | Pau Ferrer |
| Warehouse, stock, pick and pack | Warehouse manager | Operations team lead | Managing director | Oriol Camps |
| Dangerous goods approval | Operations team lead | Customs lead | Managing director | Jordi Puig |
| Laptops, accounts, Cargo Desk access | IT coordinator | External IT partner | Finance manager | Sergi Mas |
| AI questions, gaps, and ideas | AI advocate | Hamburg office lead | Managing director | Ana Costa |
| The skills and the always-on block | Harness maintainers | Each other | Managing director | Ana Costa, Lena Hoffmann |

Direct phone numbers and email addresses are left out on purpose. The
company directory has them.

## How to use it

1. Name the role first, then the person: "Claims go to the claims
   handler, currently Biel Rovira."
2. Before relying on a name, say it back: "I have Biel Rovira as claims
   handler. Is that still right?" A name that turns out wrong is
   corrected in the answer and reported to the maintainer.
3. When the owner is away, go to the backup, not up the escalation.
   Escalation is for a decision the owner cannot make or a customer
   promise at risk.
4. When the assistant remembers something about the person asking (their
   office, their role), it uses it to save a question, and says so: "You
   mentioned you're in Hamburg, so I've written this for Lena." It asks
   again whenever the memory might be stale. The company directory beats
   memory, and memory beats guessing.

## Example

**Input:** "A customer in Munich is furious about a damaged pallet on
SH-104590-01. Who do I loop in?"

**Expected:** "Two people. The claims handler owns the claim, currently
Biel Rovira; open one with the photos and the delivery note. Since the
customer is German-speaking, copy the Hamburg office lead, currently
Lena Hoffmann. Both names are from the last update to this list, so
check the directory if anything has changed."
