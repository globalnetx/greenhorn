---
name: parcelona-templates
description: "Use this skill when a colleague needs to produce one of Parcelona's recurring documents and wants the baseline rather than a blank page: a delay notice, a booking confirmation, or any piece that 'we send every week'. Trigger on 'is there a template for', 'how do we usually write a delay notice', 'draft the booking confirmation for', 'start from our standard'. Carries the structure and the fixed parts of each document, distilled from Parcelona's own sent examples, with the fill-in parts marked. Do NOT use for how the words should sound (parcelona-voice), for the process facts a document states such as quote validity or claim steps (parcelona-customer-process), or for the look of a rendered document (parcelona-brand-assets)."
metadata:
  version: 0.1.1
  audience: internal
  tags: "templates, documents, baseline"
  language: en
---

# Parcelona's templates

Baselines for the documents we send again and again, distilled from
real ones we were happy with. A template is a starting shape, not a
form to fill in blindly: the fixed parts carry what every version must
say, the fill-in parts are where the case lives, and the voice skill
decides how it sounds. Each template names the skill whose facts it
relies on, so a change there reaches the document.

## When to use this skill

- A colleague asks for "the usual" version of a recurring document.
- A draft is being written from scratch for something we send weekly.
- A new colleague wants to see what a finished one looks like.

## When NOT to use this skill

- How a sentence should sound, or the de-AI pass: parcelona-voice.
- What we promise customers about delays, claims, or quote validity: the
  facts come from parcelona-customer-process; the template only leaves
  room for them.
- Colours, fonts, and the logo for a rendered PDF or slide:
  parcelona-brand-assets.

## What to know

| Template | File | Facts it relies on |
| --- | --- | --- |
| Delay notice to a customer | `references/delay-notice.md` | parcelona-customer-process (what we tell customers about delays) |
| Booking confirmation | `references/booking-confirmation.md` | parcelona-glossary (reference formats), parcelona-customer-process (quote validity) |

How to work from one:

1. Open the template and keep its structure and fixed parts.
2. Fill the marked parts from the case: the shipment's reference number,
   the dates as the carrier states them, the customer's name as they
   use it. Nothing filled in from memory: dates and rates are copied
   from Cargo Desk or the valid quote (parcelona-conduct).
3. Pass the result through the register parcelona-voice names for the
   piece: calm and factual for a delay notice, warm and direct for a
   confirmation.
4. A rendered version (PDF, letter) takes its look from
   parcelona-brand-assets.

A template is changed only through the maintainers, from a sent example
that was better than the baseline; a one-off deviation is just a draft.

## Examples

A colleague writes: "Delay notice for SH-104233-01, the vessel is now
ETA Barcelona 26 May instead of 19 May."

The assistant opens `references/delay-notice.md`, fills the reference,
the old and new dates as the carrier's estimate, and Tulipware's
contact, and renders it in the calm register. It does not add a reason
for the delay the carrier did not give, and it does not promise the new
date as firm.

## Notes

Two templates to start with; the weekly customer status report and the
quote email are candidates once their examples are in. The templates
carry Tulipware and Nordlicht Optics as the example customers, never a
real one.
