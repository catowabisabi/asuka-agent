# Cost and Prompt Caching

Deep dive into the constraint that actually binds an API-backed assistant: token
spend, and the ratio of cache-hit tokens to uncached ones.

## Where the bottleneck moved

Moving inference to an API does remove compute as the local constraint, but it
relocates the bottleneck rather than removing it. The new binding constraints are
token spend per turn, rate limits on the extraction tier, and the precision of
retrieval, since even a long-context API does not remove the need to choose
what to put in the context.

The largest of these is the first, and it is controllable. All three providers in
the project configuration offer prefix caching, and all three match on a prefix
rather than on semantic content.

## Provider mechanics

MiniMax builds the cached prefix in the order tool list, then system prompts,
then user messages, and applies caching to calls with 512 or more input tokens
[21]. Cache hit tokens are reported in the response usage as
`usage.prompt_tokens_details.cached_tokens` on the OpenAI-compatible API and
`usage.cache_read_input_tokens` on the Anthropic-compatible one [21].

OpenAI caches the full rendered context including OpenAI-provided instructions,
developer messages, tool definitions and conversation history [22]. Cache reuse
requires the entire rendered prefix to match, so a change before a breakpoint
invalidates everything after it [22]. The minimum cacheable prompt length is
1,024 tokens for GPT-5.6 and later and varies by request settings for earlier
models [22]. Explicit mode places breakpoints manually and allows up to four
cache writes per request, and `prompt_cache_options.ttl` selects the minimum
cache lifetime [22]. Writes for GPT-5.6 and later cost 1.25x the uncached input
rate for the default 30-minute lifetime and 2.5x for a 12-hour lifetime, while
reads cost 0.1x on most of these models [22].

Kimi stores cache entries in blocks, so a portion smaller than one block counts
as a miss and is billed at the cache-miss rate [24]. `prompt_cache_options.mode`
supports only `implicit` and `ttl` supports `5m` and `1h`, defaulting to `5m`
when omitted [24]. A cache entry's TTL is locked at first write and cannot be
changed later; a hit renews the entry for free under the original TTL [24].

## Rate card

Rates are per million tokens, from each provider's own pricing page [23][25][22].

| Provider and model | Uncached input | Cached input | Cache write | Output |
| --- | --- | --- | --- | --- |
| MiniMax M3, prompt 512k or less | $0.30 | $0.06 | none listed | $1.20 |
| MiniMax M3, prompt over 512k | $0.60 | $0.12 | none listed | $2.40 |
| MiniMax M3.1-Flash | $0.15 | $0.015 | none listed | $0.60 |
| Kimi K3 | CNY 20 ($3.00) | CNY 2 ($0.30) | CNY 20 (5m) / CNY 40 (1h) | CNY 100 ($15.00) |
| Kimi K2.6 | CNY 6.50 | CNY 1.10 | not supported | CNY 27.00 |
| Kimi K2.7 Code | CNY 6.50 | CNY 1.30 | not supported | CNY 27.00 |
| OpenAI GPT-5.6 and later | model specific | 0.1x uncached rate | 1.25x for 30min TTL, 2.5x for 12h | model specific |

MiniMax's priority tier costs one and a half times standard and is selected with
`service_tier: "priority"` [23]. Only `kimi-k3` supports Cache Write; `kimi-k2.6`,
`kimi-k2.7` and `kimi-k2.7-highspeed` do not [24]. Kimi bills cached input at
one tenth of the cache-miss rate for K3 [24].

## Two routing consequences

**Kimi K3 uncached input costs exactly ten times MiniMax M3 uncached input, and
five times on cache hits** [23][25]. For a memory-heavy turn that replays a
20,000-token stable prefix, that is the difference between a few cents and tens
of cents. Routing routine retrieval-heavy and high-frequency turns to a cheaper
model is worth more than any prompt-level optimisation, because the prefix
dominates the bill.

**Kimi is the only one of the three that charges for writing the cache, and only
on K3** [24]. A one-hour write costs twice a five-minute write but saves more
on the second hit, so it is worth taking when calls arrive more than five
minutes apart. When calls arrive continuously, the five-minute default already
renews on every hit at no extra charge, and a one-hour write adds cost without
benefit [24].

## Worked cost model

With a 20,000-token stable prefix at 100 turns per day:

| Provider | Fully cached | Uncached | Kimi with a write every turn |
| --- | --- | --- | --- |
| MiniMax M3 | $0.12 per day | $0.60 per day | not applicable |
| Kimi K3 | CNY 4 per day | CNY 40 per day | CNY 80 per day |

OpenAI's own documentation states the same effect in general terms: one write
and nine full reads cost 2.15x ordinary input, against 10x without caching
[22].

These are illustrations of the shape, not a quote. The real figure depends on
message volume, profile size, and how often the conversation history grows
inside the prefix.

## The layout rule

The system prompt, tool definitions and the profile block go first, unchanged.
Volatile content goes last. Nothing dynamic belongs in the prefix, including
timestamps, and a memory block that mutates mid-session breaks the cache for
everything after it, which is why both OpenClaw and Hermes freeze the profile
snapshot at session start [6][10].

OpenAI's explicit mode is the right tool when the profile and the conversation
history change at different rates, since up to four breakpoints can be placed
independently [22]. MiniMax's 512-token threshold is low enough that even a
modest profile qualifies [21], so there is no reason to delay setting it up.

## Local embeddings

The default is the opposite of what a private memory system wants. OpenClaw
uses OpenAI embeddings by default, and any other provider has to be selected
explicitly [35][37]. Setting `provider: "none"` selects FTS5 keyword-only
search with no embeddings at all, which is a reasonable starting position for a
small private corpus [35][37].

| Model | Dimensions | Max context | Licence | Note |
| --- | --- | --- | --- | --- |
| Qwen3-Embedding-0.6B | 1024, Matryoshka 32-1024 | 32,768 | Apache-2.0 | Multilingual mean around 64 on MMTEB, the strongest of this set |
| BAAI/bge-m3 | 1024 | 8,192 | MIT | Dense, sparse and multi-vector from one model; MIRACL 18-language focus |
| EmbeddingGemma-300m | 768, Matryoshka 128-768 | 2,048 | Gemma | The bundled local default; short context |
| nomic-embed-text | 768 | 8,192 | permissive | English-centric, unsuited to a Chinese corpus |

For a Chinese and Cantonese corpus the first two are the right picks, with
Qwen3-Embedding-0.6B ahead on multilingual quality and bge-m3 ahead on hybrid
retrieval and licence clarity [26]. Reported CPU throughput for models of this
class is roughly 20 to 80 chunks per minute, which is fine for a personal corpus
and irrelevant for bulk indexing, and the 4B and 8B Qwen variants are not
practical without a GPU [27].

One configuration detail is easy to miss. OpenClaw knows the dimensions for
`text-embedding-3-small` and `text-embedding-3-large` only, so any other model
needs an explicit `embedding.dimensions` value or the vector column cannot be
created [38]. The `ollama` and `local` adapters accept a local model, and
OpenClaw's bundled local default is an `embeddinggemma-300m` quantised GGUF
[36].

## Local inference as the extraction tier

The expensive part of any memory system is the extraction pass that decides what
to store, and OpenClaw runs it as a dedicated background consolidation model
turn rather than on the busy reply path [6]. Running that tier locally, on a
small model, removes the recurring per-turn API cost. It is also the tier that
must not be run on a weak model, because a bad extractor poisons everything
above it.

## The local runtime

Both Ollama and LM Studio sit on llama.cpp, and both do have KV cache, so the
question of whether they lack one has a definite answer. The cache is automatic
in Ollama, and the lever is `keep_alive`: the default unload after five minutes
discards the cached state, `-1` keeps the model and its cache resident
indefinitely, and `OLLAMA_KEEP_ALIVE` sets the default for the server [28].

The K/V cache can itself be quantised through `OLLAMA_KV_CACHE_TYPE`, with
`q8_0` using roughly half the memory of the default `f16` and `q4_0` roughly a
quarter, both requiring flash attention to be enabled [28]. The llama.cpp server
exposes the same capability as flags, with `--cache-prompt` on by default, `-np`
setting the number of parallel slots each holding its own cache, `--cache-reuse`
and `--cache-idle-slots` extending reuse, and a slot save and restore API for
persisting a warm cache to disk [29]. Ollama also has an experimental
`OLLAMA_PREFILL_CACHE=1` mode that saves the prefill cache to disk before unload
and restores it on reload, capped at 8 GiB and off by default [31].

Two operational details are easy to lose. Cache reuse is process-scoped rather
than session-scoped, so a shared local server benefits every client sending the
same prefix, with no per-session isolation [30]. And the context window must be
set explicitly and held constant, because changing it between requests is
treated as a different model configuration and forces a reload [30].

## Configuration notes

For OpenClaw with a local embedding provider and a stable prefix:

```json5
{
  memory: {
    search: {
      provider: "ollama",          // or "none" for FTS-only, "local" for GGUF
      model: "bge-m3",             // dimensions must be set explicitly below
      fallback: "none",
    },
  },
  models: {
    providers: {
      moonshot: {
        baseUrl: "https://api.moonshot.ai/v1",
        apiKey: "${MOONSHOT_API_KEY}",
        api: "openai-completions",
        models: [{ id: "kimi-k3", name: "Kimi K3" }],
      },
    },
  },
}
```

The `${ENV_VAR}` expansion syntax in the provider block matches the convention
already used in `config/config.yaml` [38].

Full reference list: [05-sources.md](05-sources.md)
