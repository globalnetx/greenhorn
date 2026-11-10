---
name: parcelona-compass
description: "Use this skill when the conversation is about Parcelona Logistics as a company: what we do, which services we offer, who our customers are, where our offices are, which languages we work in, or what we are not. Trigger on 'who are we', 'do we do X', 'can we handle this shipment', 'is that something Parcelona offers', 'what should I tell a new customer about us', and whenever a draft states a fact about Parcelona. Without it the assistant assumes a freight forwarder owns ships and trucks, or treats Parcelona as a parcel courier because of the name. Do NOT use for what a freight term means (parcelona-glossary), how a shipment moves from quote to invoice (parcelona-customer-process), or how to word the reply (parcelona-voice)."
metadata:
  version: 0.3.0
  audience: internal
  tags: "company, services, orientation"
  language: en
---

# Parcelona compass

Who Parcelona is, in the words a new colleague would need in their first
week. Use it as the factual source whenever a draft says something about
the company. When a fact here and a current document disagree, the
document wins and the maintainer hears about it.

## What we do

Parcelona Logistics is a freight forwarder. We organise the transport of
other companies' goods, mostly from Asia into Europe, and we handle what
surrounds it: customs clearance in Spain, storage, and the paperwork. We
buy space from carriers (shipping lines, airlines, road hauliers) and
sell our customers a managed shipment.

- **Sea freight**, full containers (FCL) and shared containers (LCL),
  mainly from Chinese and Southeast Asian ports to Barcelona, Valencia,
  and Rotterdam.
- **Air freight** for urgent or high-value goods.
- **Road freight** within Europe, run with partner hauliers.
- **Customs clearance in Spain**, where Parcelona acts as the customer's
  customs representative.
- **Warehousing** in our own warehouse near the port of Barcelona:
  storage, pick and pack, and onward distribution to business addresses.

Sea freight is the bulk of the work; customs clearance is the second
earner; air, road, and warehousing are occasional and mostly for existing
customers.

**A typical sea-freight case.** Tulipware asks for a price on a container
from Ningbo to Barcelona. Sales quotes from the rate sheet against the
packing list and the Incoterm; operations books with the carrier and
collects the shipping documents from the shipper; the customs lead clears
the goods in Barcelona; a partner haulier delivers; finance invoices from
the completed shipment. Six to eight weeks door to door. The step that
goes wrong most often is the documents: a commercial invoice that arrives
late holds everything behind it. The transit time in the quote is the
carrier's estimate, never Parcelona's promise.

Offices: Barcelona (headquarters) and Hamburg (sales and operations for
German-speaking customers). Hamburg is its own office, not a branch of
Barcelona: write "our Hamburg office", never "the Hamburg branch". We
work in Spanish, Catalan, English, and German. Internal writing is in
English or Spanish.

## Who we serve

1. **Regular importers**, mid-sized European brands that ship every month
   on a rate agreement. Tulipware is the typical example in our skills.
2. **Occasional shippers**, who ask for a quote per shipment.
3. **Overseas agents**, the partner forwarders at origin who hand over
   cargo and paperwork to us.

## What we are not

The list people get wrong most often. Check a draft against it.

- **Not a carrier.** We own no ships, aircraft, or trucks. We never write
  "our vessel" or "our trucks"; we write "the carrier" or name the
  carrier from the booking.
- **Not a parcel or courier service**, whatever the name suggests. We do
  not deliver to private homes and do not offer next-day parcels.
- **Not a customs broker outside Spain.** In Hamburg and elsewhere, a
  partner broker clears the goods, and the customer is told so.
- **Not a carrier of every cargo.** We do not handle explosives or
  radioactive goods. Any other dangerous goods need the operations team
  lead's approval before a quote goes out.
- **Not the party that sets transit times.** The carrier does. We pass on
  the carrier's schedule and say that it is the carrier's.

## Key links

- Website: `https://www.parcelona.example`
- Customer guide and terms of business: `https://www.parcelona.example/guide`
- Tracking for customers: `https://track.parcelona.example`

Point customers at these rather than restating them.

## Example

**Input:** "A new lead asks if we can deliver 300 parcels to their
customers' homes in Madrid next week. Can we?"

**Expected:** "Not as asked. We are a freight forwarder, not a parcel
service, so we do not deliver to private homes. We could bring the stock
into our Barcelona warehouse and ship it on to a parcel carrier of their
choice." A reply to the lead goes through parcelona-voice.

## Notes

- Figures about the company (headcount, warehouse size, founding year)
  are left out on purpose. They change, and nobody decides better for
  knowing them. The website carries them.
- Facts here come from the interview profile. A fact the assistant cannot
  trace there is a question for the maintainer, not an addition.
