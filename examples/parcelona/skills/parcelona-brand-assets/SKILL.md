---
name: parcelona-brand-assets
description: "Use this skill whenever the assistant makes something visual for Parcelona: a slide deck, a one-pager, a document or PDF, an HTML page, a chart, a diagram, or a social image, or when someone mentions our logo, colours, fonts, or house style. Trigger even when nobody asks for branding but the output is for customers or for colleagues, since a deck in default colours reads as someone else's. Carries the palette with hex values, the two typefaces and where to get them, the logo mark and its rules, and a default layout. Do NOT use for the words on the slide (parcelona-voice) or for facts about the company (parcelona-compass)."
license: "The Parcelona mark is for Parcelona's internal and customer material only. The typefaces are under the SIL Open Font License and are not bundled here."
metadata:
  version: 0.1.1
  audience: internal
  tags: "brand, design, visual"
  language: en
---

# Parcelona brand assets

How anything the assistant makes should look. The goal is that a deck,
a page, or a chart is recognisably Parcelona's at a glance, whoever
asked for it.

## Palette

| Name | Hex | Use for |
| --- | --- | --- |
| Port Navy | `#1B2A41` | Primary. Headings, the mark's background, title slides |
| Terracotta | `#C8553D` | Accent. One highlight per page or slide, never body text |
| Sand | `#F2E8D5` | Light backgrounds, table header rows |
| Sea Teal | `#2A7F82` | Secondary accent, the second series in a chart |
| Graphite | `#3A3A3A` | Body text on light backgrounds |
| White | `#FFFFFF` | Page background |

Body text is Graphite on White or Sand. Terracotta on Port Navy is for
large text only, since small text in that pairing is hard to read.

## Typefaces

- **Archivo** for headings, semibold.
- **Source Sans 3** for body text and tables, regular.

Both are under the SIL Open Font License and available from Google Fonts.
They are not bundled in this folder: load them from Google Fonts, or use
the installed copies. When neither is possible, fall back to the
system's default sans-serif and say so.

## The mark

The logo mark is in `references/parcelona-mark.svg`: a cream "P" on a
Port Navy square with a terracotta block, like a container on a quay.

- Use it on title slides, page headers, and footers, at least 24 pixels
  tall.
- Keep clear space around it of at least a quarter of its height.
- Never recolour, stretch, or put it on a busy photo.
- The full logo with the wordmark lives with the marketing team; ask for
  it rather than rebuilding it from the mark.

## Default layout

- Title slide: Port Navy background, white Archivo title, the mark top
  left.
- Content: White background, Port Navy headings, Graphite body, one
  Terracotta highlight at most.
- Tables: Sand header row, no vertical lines.
- Charts: Port Navy first, Sea Teal second, Terracotta only for the one
  number that matters.

## Example

**Input:** "Make me a one-slide summary of Tulipware's delayed shipments
for the Monday call."

**Expected:** A White slide with a Port Navy Archivo heading, a short
Sand-headed table of the delayed shipments (shipment numbers and the
carrier's current estimates copied from Cargo Desk), the one shipment at
risk for their launch highlighted in Terracotta, and the mark in the
footer. The words follow parcelona-voice.
