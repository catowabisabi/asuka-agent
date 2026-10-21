# CJK Retrieval Notes

Field notes from building the test persona and running the index against real
Cantonese text. These findings are empirical, measured on SQLite 3.40.1 with
FTS5, and they change the free-tier advice in
[03-cost-and-caching.md](03-cost-and-caching.md).

Reproduce everything here with:

```
python3 tests/personal/verify-index.py
```

## The tokenizer setting is not a preference

OpenClaw's default FTS5 tokenizer is `unicode61`. It splits on non-alphanumeric
characters, and CJK ideographs count as alphanumeric, so a run of Chinese
characters becomes a **single token**. A query therefore only matches when it
equals a complete CJK run, and whether that happens depends on where
punctuation falls in the note.

Measured against the seeded persona workspace:

| Probe | unicode61 | trigram |
| --- | --- | --- |
| 做會計 | 0 | 1 |
| 去大阪 | 0 | 1 |
| 瑜伽課 | 1 | 2 |
| flat white | 2 | 2 |
| audit | 2 | 2 |

unicode61 happened to match some probes and miss others, with no way to
predict which. `trigram` treats a run of three or more characters as a
substring, so recall stops depending on the note's phrasing.

**Setting: `memory.search.store.fts.tokenizer = "trigram"`.**

## The three character floor

A trigram index cannot match a pattern shorter than three characters. This
holds for `MATCH` and for `LIKE` alike, because FTS5 intercepts the `LIKE`
operator on a trigram table and applies the same rule.

| Query | Result |
| --- | --- |
| 瑜伽 | 0 hits |
| 阿黑 | 0 hits |
| 大阪 | 0 hits |
| AI | 0 hits |
| 瑜伽課 | hits |
| 佢叫阿黑 | hits |
| flat white | hits |

A prefix query does not rescue it. `瑜伽*` also returns nothing.

Two-character Cantonese words are everywhere: 瑜伽, 阿黑, 大阪, 意粉, 開肩, 貓.
None of them can be searched on their own.

**Practical rule: never let a fact live only as a two-character term.** Write
it inside a longer phrase, and search with that phrase.

- `佢叫阿黑` instead of `阿黑`
- `去大阪嘅機票` instead of `大阪`
- `上瑜伽課` instead of `瑜伽`

## The rule that decides whether the free tier is usable

A trigram match needs a **contiguous run of three or more characters that
appears in both the query and the note**. Not a word. Not a concept. The same
characters, next to each other, in the same order.

| Query style | Example | Result |
| --- | --- | --- |
| Two-character keyword | `中環` | 0 hits |
| Paraphrase | `我喺邊度返工㗎` | 0 hits |
| Paraphrase | `我隻貓叫咩名` | 0 hits |
| Shared phrase | `喺中環` | 1 hit |
| Shared phrase | `隻貓叫` | 1 hit |
| Verbatim note text | `我喺中環一間中型核數師事務所做會計` | 1 hit |

So the free tier gives **literal string retrieval, not memory**. A question
phrased differently from the note will not find it, no matter how good the
assistant is.

Two consequences for the design.

**The notes must be written in the language the user speaks.** If the notes
are in English and the user asks in Cantonese, there is almost no shared
character run and recall collapses. The persona's notes in this repository are
in Cantonese for exactly that reason, even though the profile directives and
the project code are in English.

**The assistant must search with phrases, not keywords.** Taking the question
`我隻貓叫咩名` and searching for the whole string fails. Searching for the
substring `隻貓叫` succeeds, because that substring is contiguous in the note.
A useful retrieval strategy is to try each entity-like fragment of the
question as a separate query, rather than one query for the whole message.

## Why this makes the embedding tier a requirement, not an upgrade

The research in [03-cost-and-caching.md](03-cost-and-caching.md) treats the
local embedding model as an optional step five, to be taken once the corpus
justifies it. For a Cantonese-speaking user, the experiment above says
otherwise: on the free tier, recall only works when the user happens to use
the same words as the note.

The test set encodes this as a pair per fact. The `as_written` cases must pass.
The `paraphrased` cases must still fail. When a local embedding provider is
enabled, the paraphrased cases should start passing, and their assertions in
[testset.yaml](../tests/personal/testset.yaml) should be inverted. That flip is
the measurement that the upgrade actually bought something.

## Trigger phrases have the same floor

Trigger phrases are compared against the inbound message by a lexical prefilter,
so they face the same three-character minimum. A trigger of `瑜伽` or `咖啡` or
`核數` will not fire. Triggers in this project are written as three or more
characters, and phrased the way a person would actually type them:

| Instead of | Use |
| --- | --- |
| 瑜伽 | 上瑜伽, 瑜伽課, yoga |
| 咖啡 | 飲咖啡, 咖啡訂單, coffee |
| 核數 | 核數師, 工作內容, audit |
| 京都 | 去京都, 去過邊 |

## What was not tested

- The behaviour of the runtime's own search layer, which may handle short
  terms differently from a raw `MATCH`. OpenClaw's documentation states that
  short terms use substring matching under the trigram tokenizer, which raw
  FTS5 cannot do, so the runtime must be doing something extra. This project
  relies on the documented behaviour and writes notes that satisfy the stricter
  raw floor anyway, so it does not depend on which is true.
- LM Studio's own documentation, for the same reason given in
  [report.md](report.md).
