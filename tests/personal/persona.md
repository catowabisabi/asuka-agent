# Test Persona: Ho Ka-yan

A synthetic persona used to exercise the memory system. Everything about her is
invented. The point is to have a person with enough texture that recall,
preference adherence, supersession and scoping can all be tested against
something specific rather than against "the assistant seemed fine".

## Identity

| Field | Value |
| --- | --- |
| Name | Ho Ka-yan (何嘉欣) |
| Age | 25 |
| Role | Accountant, audit, mid-sized firm in Central, Hong Kong |
| Experience | Three years, qualified |
| Home | One-bedroom flat in Tin Hau, with a black cat named 阿黑 (Ah Hak) |
| Commute | MTR, Tin Hau to Central, about thirty minutes |
| Languages | Cantonese at home, English for finance and technical work |
| Peak season | January to March, close plus audit fieldwork |

## Daily shape

| Time | What she does |
| --- | --- |
| 06:45 | Up, ten minutes of stretching |
| 07:00 | Yoga class, Monday, Wednesday, Friday, forty-five minute vinyasa flow, Sheung Wan |
| 08:15 | Flat white, oat milk, no sugar, at the studio |
| 08:40 | MTR to Central |
| 09:30 | Work starts, accounts payable reconciliation |
| 12:30 | Lunch, usually with colleagues around Sai Ying Pun |
| 15:00 | Second coffee |
| 16:30 | Audit sample selection and review notes |
| 18:45 | Home, unless it is peak season |
| 20:00 | Cooks most nights |
| 22:30 | Travel journal, or the monthly spending sheet |

## Travel style

Three or four trips a year, shoulder season, mostly Japan and South East Asia.
One carry-on bag, never checks luggage, always a window seat. Books shortly
after payday. Keeps a paper travel journal, one page per trip. Went to Kyoto
in April 2026 and Chiang Mai in November 2025. Osaka is booked for 2026-11-20
for five days.

## How she communicates

Concise, direct, allergic to filler. Reads the first line and decides. Does not
want a preamble or a restatement of the question. Wants action items first.
Uses Traditional Chinese for ordinary conversation and leaves financial and
technical terms in English. Comfortable with tables, prefers them once there
are three or more options to compare. Allergic to emoji in anything a client
will see, relaxed about them otherwise. Checks arithmetic. Wants the basis of
a number shown, and wants to be told when something is over budget without
having to ask.

## What the persona is for

| Test area | Why this persona fits |
| --- | --- |
| Preference adherence | Strong, specific, and often in conflict with a default assistant style |
| Supersession | The verbose instruction is explicitly withdrawn, so a stale value is detectable |
| Fact recall | Routines and a pet give a wide set of concrete, checkable facts |
| Cost model | A busy weekday gives a realistic daily turn count and a realistic stable prefix |
| Scope | A work persona next to a personal persona gives two scopes that must not bleed |
| Missing data | The monthly budget figure is deliberately absent, so the correct behaviour is a question, not a guess |
| Free-tier limit | The test set includes a query that keyword search provably cannot answer |

## Deliberate gaps

- **The monthly budget figure is not recorded anywhere.** A request for it must
  produce a question, not an estimate.
- **The Osaka hotel is not booked.** A travel recommendation must therefore
  propose a cheapest option rather than recall one.
- **The client deadline is not recorded.** Only the work pattern is.
