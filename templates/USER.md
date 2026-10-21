# USER PROFILE

<!--
  The user model. Stable preferences, communication style, relationships and
  active-project context, written as directives.

  Rules, from the platform's own contract:
    1. Begin with an imperative: Always, Never, Prefer.
    2. Record the date the preference was observed.
    3. Use only "active" or "superseded" for status.
    4. Keep one behavioural instruction per directive.
    5. Do not turn this file into a dossier.

  Hard cap: 4,000 characters. Configuration can lower it, never raise it.
  When it fills up, move durable facts to MEMORY.md, move running context to
  memory/YYYY-MM-DD.md, and move event-conditioned actions to standing intents.

  To change a preference: edit its existing section in place, flip the old
  entry to "superseded", and put the new entry next to it. Never append a
  second active directive for the same topic. Appending contradictory history
  is what makes a model keep applying the old value.

  Search note: with the trigram tokenizer, a query term must be at least three
  characters to match. Two-character Cantonese words do not match at the raw
  FTS5 layer, so trigger phrases here are written as three or more characters
  ("上瑜伽" rather than "瑜伽").
-->

<!-- observed: YYYY-MM-DD | status: active -->

- Always reply in Traditional Chinese, keeping English for financial and technical terms.

<!-- observed: YYYY-MM-DD | status: active -->

- Never open a reply with a preamble or a restatement of the question.

<!-- observed: YYYY-MM-DD | status: active -->

- Prefer action items first, then supporting detail.

<!-- observed: YYYY-MM-DD | status: active -->

- Prefer bullet points over numbered lists.

<!-- observed: YYYY-MM-DD | status: active -->

- Ask one specific question when a required figure is missing, instead of estimating.

<!-- observed: YYYY-MM-DD | status: active -->

- Never re-ask for information already recorded in memory.

<!-- observed: YYYY-MM-DD | status: active -->

- Always show the calculation basis for any financial figure.

<!-- observed: YYYY-MM-DD | status: active -->

- Always flag any budget variance above ten percent without being asked.

<!-- observed: YYYY-MM-DD | status: active -->

- Prefer the cheapest option when a recommendation involves spending.

<!-- observed: YYYY-MM-DD | status: active -->

- Always use metric units for distance, weight and temperature.

<!-- observed: YYYY-MM-DD | status: active -->

- Never use emoji in client-facing deliverables.

<!-- observed: YYYY-MM-DD | status: active -->

- Prefer a table when comparing three or more options.

<!-- observed: YYYY-MM-DD | status: active -->

- Prefer short replies between 09:00 and 19:00 on weekdays.

<!-- observed: YYYY-MM-DD | status: active -->

- Never write a reply longer than ten lines unless a table is used.

<!-- observed: YYYY-MM-DD | status: active -->

- Always include the departure date and the trip length when discussing travel.

<!-- observed: YYYY-MM-DD | status: active -->

- Prefer one carry-on bag only, and never check in luggage.
