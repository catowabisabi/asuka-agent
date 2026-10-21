# Memory Architecture for a Telegram-Driven Personal Agent

## Core judgment

The memory layer that holds up for a personal assistant running on OpenClaw or Hermes with API-backed models is file-first, bounded, and scope-filtered: a small human-editable profile injected at the front of the prompt, over a searchable archive. The vector store is the archive underneath, not the brain of the system. Three findings from the source material drive that recommendation, and each one argues against reaching for a dedicated memory framework.

Published memory benchmarks no longer support the case for a sophisticated retrieval stack. A 2026 survey of agent memory reports that systems scoring near-perfectly on LoCoMo fall to 40-60% on MemoryArena, which interleaves memory with decision-making rather than testing recall in isolation [1]. The figures quoted in that work put Mem0 at 37.09%, MemOS at 42.55% and Zep at 39.97%, all below a Gemini-3-Flash full-context baseline of 72.61% [2]. The distance between vendor self-reports and independent runs is wide: Mem0 reports 94.4 on LongMemEval, while an independent run under a competitor's harness places the same system at 49 [3], and earlier published Zep and Mem0 figures have been retracted outright [4]. A nine-point swing on a single dataset arose when Zep's original 84% was challenged as 58.44% and then revised to 75.14% [5]. On one maintained benchmark, a naive cosine baseline outscored a tuned system on recall@k [4]. For a single-user assistant whose entire corpus is one person's preferences and projects, the full-context baseline is not a strawman; it is the bar.

The write path dominates retrieval quality. OpenClaw's own design principle states that writing is the hard part, that retrieval over notes files is competitive with far heavier designs, and that long-horizon evaluations consistently show what was written matters more than how it is indexed [6]. The survey frames memory the same way, as a write-manage-read loop rather than a retrieval component [1]. Effort spent on a better embedder is effort spent on the smaller half of the problem.

Preference-following and fact-recall fail in different ways, so they need different structures. PrefEval found that models stop applying a preference that is merely present in context after a handful of turns, and that restating the directive near the point of use restores adherence better than heavier retrieval machinery [7]. HorizonBench found that systems often keep applying an originally stated preference after the user has changed it [8]. A vector store that faithfully retrieves a superseded preference is not doing its job.

The remainder of this report covers the evidence behind those three claims and the specifics that follow from them: how scope actually works, what the prompt-cache economics look like across the three providers already in the project configuration, what can be kept on the local machine, and what the resulting architecture for `asuka-agent` looks like.

## Benchmark reliability in agent memory

LoCoMo is the standard reference for long-term conversational recall: roughly 1,986 questions across single-hop, multi-hop, temporal and open-domain categories, of which 446 are adversarial [2][5]. Recent comparisons have begun omitting the adversarial subset, which inflates headline accuracy precisely because those items are designed to catch over-confident answers [5]. The most useful signal is not any single score but the spread between how the same system scores when different parties run it.

The table below lists the same system measured by different parties, which is the only comparison that survives the grading-recipe problem.

| System | Self-reported | Independent run | Source |
| --- | --- | --- | --- |
| Mem0 on LongMemEval | 94.4 | 49 | [3][6] |
| Zep / Graphiti on LongMemEval | 90.2 | 58.6 | [3] |
| Naive cosine baseline against a tuned system, recall at 10 | 0.7138 (floor) | 0.6939 (tuned) | [4] |

Two patterns matter. A single framework's score can swing tens of points depending on who is running it, so a vendor ranking is marketing rather than measurement. And in the one benchmark where a naive baseline was published alongside a tuned system, the baseline won on recall at 10 [4].

The practical consequence for a personal assistant is not that memory systems are useless. It is that the reason to add one is manageability, not recall quality. A file-based profile gives a human the ability to read, edit, audit and delete what the agent believes, and a hard character budget that keeps the always-injected block small. Those properties are what actually differentiate an assistant that feels trustworthy from one that feels uncanny, and they are exactly what a hosted memory platform does not give.

The survey's own framing agrees: memory is formalised as a write-manage-read loop coupled to perception and action, with five mechanism families examined, and its open problems are continual consolidation, causally grounded retrieval, trustworthy reflection and learned forgetting [1]. Those are research problems, not configuration problems.

## Memory shapes and framework fit

Agent memory tooling divides into three shapes, and the distinction determines the amount of work required to adopt it.

| Shape | Examples | What it optimises | Fit for this stack |
| --- | --- | --- | --- |
| Memory layer or API | Mem0, Graphiti and Zep, Supermemory | Extraction quality, multi-backend storage, managed hosting | High integration cost; the benchmark spread does not justify it |
| Agent runtime with built-in memory | Letta, the ex-MemGPT lineage | Long-horizon autonomous agents that edit their own memory | Overkill; requires moving the agent into the runtime |
| Local-first file and index layer | OpenClaw built-in, Hermes built-in, Holographic, LanceDB plugin | Inspectable files, bounded injection, no cloud dependency | Already installed; the layer to build on |

The third row is the one that matches the constraint set. OpenClaw's memory is plain Markdown in the agent workspace with no hidden state [9]. Hermes stores the same two files, `MEMORY.md` and `USER.md`, under `~/.hermes/memories/` and injects them as a frozen snapshot at session start [10]. Both treat the file as the source of truth and the index as derived, which is the property that makes the memory auditable and editable without touching vendor tooling.

Hermes also exposes eight external providers for the cases where the built-in pair is insufficient, and one of them, Holographic, is a local SQLite fact store with FTS5, trust scoring and algebraic queries that needs no external dependencies and costs nothing [11]. That is the upgrade path which preserves locality. Honcho and Hindsight, the two providers most often discussed for deep user modelling, are considerably heavier. Honcho's open-source code is AGPL-3.0, which matters if it is self-hosted and linked into a networked service, while Hindsight's local mode is described as fully local with Ollama but still relies on a bundled PostgreSQL, embedder and reranker [12].

## Tiered storage and write-path curation

OpenClaw's architecture documents memory as five tiers, and the tier structure is the most transferable design idea in either platform [6].

Instructions are the human-authored `AGENTS.md` and workspace instruction files, always injected and never written by the model. The curated core is `MEMORY.md` and `USER.md`, written only through gated consolidation and injected at session start under a budget. The episodic tier is `memory/YYYY-MM-DD.md` daily notes plus session transcripts, written freely during work and retrieved on demand rather than at session start. Prospective memory is standing intents in SQLite and cron jobs, injected only when their trigger fires. Review material, `DREAMS.md` and dreaming reports, is never injected and exists for human reading.

Two properties of this design deserve emphasis. First, nothing crosses from episodic into curated without passing promotion gates; the consolidation model turn is the only primary writer to the curated tier, and it is allowed to merge, supersede and deduplicate, with the previous version stored as a pre-image so the change is reviewable afterwards [6]. Second, a single writer to the curated tier removes the failure mode where a model accumulates contradictory entries indefinitely, which is the same failure HorizonBench documents for preferences [8].

The write path is also where the security boundary sits. OpenClaw tags every memory with a provenance class drawn from a closed set of `owner`, `agent`, `untrusted` and `system`, stored in SQLite columns the model cannot write through prose, and it marks content recalled from memory so that it is never re-extracted as a new fact [6]. Content that a tool reports as network-sourced taints the remainder of that turn, so a web page cannot launder itself into the curated core. A poisoning attempt in the platform's own worked example lands in the episodic tier as untrusted, never auto-injects, and cannot be promoted by recall frequency no matter how often it is retrieved [6].

The design principle generalises: enforce provenance at write time and gate promotion structurally, rather than trying to detect bad memories at read time. The memory-poisoning literature reaches the same conclusion, and detection-based defences measure poorly [6][13].

## Preference storage as a distinct artifact

Preferences are not memories, and conflating the two produces the characteristic failure of assistants that recall correctly and still behave wrongly.

OpenClaw keeps `USER.md` separate from `MEMORY.md` for exactly this reason, with a fixed 4,000-character bootstrap cap that configuration can only lower and never raise [14]. Each entry is a metadata line plus a single imperative directive:

```markdown
<!-- observed: 2026-07-27 | status: active -->

- Prefer concise progress updates during implementation work.
```

The contract has four rules: begin with an imperative such as Always, Never or Prefer; record the date the preference was observed; use only `active` or `superseded` for status; and keep one behavioural instruction per directive [14]. A changed preference is updated in place and the superseded entry is left adjacent to its replacement, so the current directive stays unambiguous [14]. That design is a direct response to the two benchmark findings above: PrefEval on restatement, HorizonBench on stale-value selection.

Hermes enforces the same separation with character limits rather than a richer format: `MEMORY.md` for the agent's own notes at 2,200 characters, `USER.md` for the user profile at 1,375 characters, entries separated by a section-sign delimiter, with a usage percentage rendered into the system prompt so the agent can see its remaining budget [10]. Hermes also notes that a fact saved during a session appears in the prompt only at the next session start, because the snapshot is frozen [10].

That frozen snapshot has a second purpose that is easy to miss. Hermes states the reason directly: the freeze preserves the LLM's prefix cache for performance [10]. The memory block is part of the cached prefix, and a memory block that mutates mid-session invalidates the cache for everything after it. This is the mechanism that connects memory design to token cost, and it is why the profile belongs at the front of the prompt rather than appended near the user's message.

The practical storage rule follows from the budget. Preferences are directive-sized and belong in `USER.md`; durable facts and lessons move to `MEMORY.md`; running context and observations move to daily notes, where they stay reachable without consuming the always-injected budget; event-conditioned future actions become standing intents and exact-time actions become scheduled tasks [14]. The profile file is the smallest and most valuable layer, and it should be the one a human edits by hand.

## Scope as a retrieval filter

The question of whether ChatGPT's project behaviour is a scoping effect has a precise answer, and it generalises to a self-built system.

ChatGPT's project-only memory is documented as a hard boundary: chats can reference other conversations in the same project, but they cannot reference conversations outside the project, and chats outside the project cannot reference conversations in it [15]. Claude implements the same model, with a separate memory space per project plus a global memory for non-project conversations, and an incognito mode that feeds neither [16]. The mechanism is a namespace partition, but the deeper principle is that retrieval must not cross a boundary the user expects to be sealed.

The same boundary in OpenClaw is implemented as a filter rather than a partition, and the difference is instructive. Repository work adds a trailing project annotation to the memory entry, derived from the normalised `origin` remote, and project scope changes ranking and automatic injection without partitioning the files [6]. Each session keeps up to four recently active repository keys; ranked search boosts entries from active repositories and mildly demotes entries from others, and trigger injection is stricter, requiring every project key on an entry to be in the active set. `USER.md` and standing intents remain user-level and are never project-scoped [6].

That is the right shape for a personal assistant: one store, one filter column, multiple scopes. A separate database per scope multiplies the write path and makes cross-scope recall impossible; a filter keeps the archive single while letting the retrieval predicate express scope. Mem0 exposes the same primitive at the API level, where a search takes a filter on the owner identifier [17].

Scope also has to be attached to the write, not only the read. A memory written inside one project but not tagged leaks into every other project on the next retrieval. OpenClaw solves this by having the runtime pass the resolved project key into the memory prompt sections and instructing the agent to annotate new repository-specific entries with it [6].

## Per-agent memory under Telegram multi-account routing

The project configuration already has the right shape for this: a list of agent bot tokens, a list of manager bot tokens, and a list of allowed user IDs. OpenClaw's model maps onto it closely.

Each agent is one brain with its own workspace, its own state directory, and its own SQLite-backed session history, and its own memory index at `~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite` [18]. Routing is by binding, with a fixed precedence order: exact peer, parent peer, peer wildcard, guild plus roles, guild, team, account, channel, then fallback owner [18]. Multiple bindings matching at the same tier resolve to the first in configuration order. Traffic that matches no binding is not handed to an arbitrary first-listed agent; it needs an explicit owner [18].

Telegram is one of the channels that supports multiple accounts, each identified by `accountId` and routed to its own agent [18]. A manager bot is therefore an account bound to the orchestrating agent, and each worker bot is an account bound to its own agent, with each agent keeping an isolated memory index.

Two consequences follow for the configuration. Since v2026.8.1 the QMD backend was retired and built-in memory no longer searches another agent's transcript corpus; shared reference material is placed in an explicit shared directory via `memory.search.extraPaths`, and each agent indexes it independently [18]. The global user profile is the one thing that should cross agent boundaries, and in OpenClaw that role belongs to the shared workspace `USER.md` or to the per-person file under `users/<canonical-profile-id>/USER.md` on a shared Gateway [14]. The per-agent `MEMORY.md` stays private to that agent.

Access control has an equivalent in the Telegram channel layer. The direct-message policy is `pairing`, `allowlist` or `open`; `allowlist` requires at least one sender ID in `allowFrom`, and `open` requires `allowFrom` to include a wildcard [19]. The allowed-ID list takes numeric Telegram user IDs, with `telegram:` and `tg:` prefixes accepted and normalised [19]. Two failure modes are worth designing against. An `allowlist` policy with an empty `allowFrom` blocks all direct messages and is rejected by configuration validation [19], so an empty list in the YAML is a startup failure rather than a silent open door. And a restrictive top-level `allowFrom` is a safety boundary: an account-level wildcard does not make that account public unless the merged effective allowlist still contains an explicit wildcard [19]. For a deployment with one manager bot and several worker bots, the top-level list should hold the real numeric IDs and each account should inherit it, rather than each account carrying its own wildcard.

Token resolution follows a separate precedence from the access list: `tokenFile` beats `botToken`, `botToken` beats the environment, and the `TELEGRAM_BOT_TOKEN` environment variable resolves only for the default account [20]. Named accounts therefore need an explicit `botToken` or `tokenFile`, which is a better fit for the list-of-tokens structure in the project configuration than a single environment variable would be.

## Prompt-cache economics across MiniMax, Kimi, and OpenAI

The bottleneck for an API-backed assistant is not compute, as the earlier part of this discussion concluded. It is token spend, and specifically the ratio of cache-hit tokens to uncached ones. A stable prefix is what turns that ratio in your favour, which is why memory placement and cost are the same design problem.

All three providers in the project configuration offer prefix caching, and all three match on a prefix rather than on semantic content. MiniMax builds the prefix in the order tool list, then system prompts, then user messages, and applies caching to calls with 512 or more input tokens [21]. OpenAI caches the full rendered context including instructions, developer messages, tool definitions and conversation history, requires the entire rendered prefix to match, and sets a minimum cacheable prompt length of 1,024 tokens for GPT-5.6 and later [22]. Kimi stores cache entries in blocks, so a portion smaller than one block counts as a miss [24].

| Provider and model | Uncached input | Cached input | Cache write | Output |
| --- | --- | --- | --- | --- |
| MiniMax M3, prompt 512k or less | $0.30 | $0.06 | none listed | $1.20 |
| MiniMax M3.1-Flash | $0.15 | $0.015 | none listed | $0.60 |
| Kimi K3 | CNY 20 ($3.00) | CNY 2 ($0.30) | CNY 20 (5m) / CNY 40 (1h) | CNY 100 ($15.00) |
| Kimi K2.6 | CNY 6.50 | CNY 1.10 | not supported | CNY 27.00 |
| OpenAI GPT-5.6 and later | model specific | 0.1x uncached rate | 1.25x for 30min TTL, 2.5x for 12h | model specific |

Rates are per million tokens, from each provider's own pricing page [23][25][22]. MiniMax prices prompts over 512k input tokens at twice the listed standard rate, and its priority tier at one and a half times standard [23].

Two consequences follow that are easy to miss.

Kimi K3 uncached input costs exactly ten times MiniMax M3 uncached input, and five times on cache hits [23][25]. For a memory-heavy turn where a 20,000-token stable prefix is replayed, that is the difference between a few cents and tens of cents. A routing policy that sends retrieval-heavy or high-frequency turns to a flagship model and routine turns to a cheaper one is worth more than any prompt optimisation.

Kimi is also the only one of the three that charges for writing the cache, and only on K3. K2.6 and the other K2 models do not support Cache Write at all [24]. A one-hour write costs twice a five-minute write but saves more on the second hit, which is worth taking when calls are more than five minutes apart; when calls arrive continuously, the five-minute default already renews on every hit at no extra charge [24]. A cache entry's TTL is locked at first write and cannot be changed later [24].

The arithmetic makes the design decision concrete. With a 20,000-token stable prefix at 100 turns per day, MiniMax M3 costs $0.12 per day fully cached against $0.60 uncached, and Kimi K3 costs CNY 4 per day cached against CNY 40 uncached. Failing to reuse the cache on Kimi is worse than failing to reuse it on MiniMax, because the K3 write charge adds CNY 40 per day on top. OpenAI's own documentation states the same effect in general terms, with one write and nine full reads costing 2.15x ordinary input against 10x without caching [22].

So the rule is that the system prompt, tool definitions and the profile block go first, unchanged, and volatile content goes last. Nothing dynamic belongs in the prefix, including timestamps, and a memory block that mutates mid-session breaks the cache for everything after it. OpenAI's explicit mode allows up to four cache breakpoints per request and lets a developer place them, which is the right tool when the profile and the conversation history change at different rates [22]. MiniMax's threshold of 512 input tokens is low enough that even a modest profile qualifies [21].

## Local embedding and inference options

Memory that stays on the machine needs a local embedding path, because the default is the opposite: OpenClaw uses OpenAI embeddings by default, and any other provider has to be selected explicitly [35][37].

The available local options are good enough for a personal corpus. Setting `provider: "none"` selects FTS5 keyword-only search with no embeddings at all, which is a reasonable starting position for a small private corpus [35][37]. For semantic retrieval, the `ollama` and `local` adapters accept a local model, and OpenClaw's bundled local default is an `embeddinggemma-300m` quantised GGUF [36].

| Model | Dimensions | Max context | Licence | Note |
| --- | --- | --- | --- | --- |
| Qwen3-Embedding-0.6B | 1024, Matryoshka 32-1024 | 32,768 | Apache-2.0 | Multilingual mean around 64 on MMTEB, the strongest of this set |
| BAAI/bge-m3 | 1024 | 8,192 | MIT | Dense, sparse and multi-vector from one model; MIRACL 18-language focus |
| EmbeddingGemma-300m | 768, Matryoshka 128-768 | 2,048 | Gemma | The bundled local default; short context |
| nomic-embed-text | 768 | 8,192 | permissive | English-centric, unsuited to a Chinese corpus |

For a Chinese and Cantonese corpus the first two are the right picks, with Qwen3-Embedding-0.6B ahead on multilingual quality and bge-m3 ahead on hybrid retrieval and licence clarity [26]. Reported CPU throughput for models of this class is roughly 20 to 80 chunks per minute, which is fine for a personal corpus and irrelevant for bulk indexing, and the 4B and 8B Qwen variants are not practical without a GPU [27]. One configuration detail is easy to miss: OpenClaw knows the dimensions for `text-embedding-3-small` and `text-embedding-3-large` only, so any other model needs an explicit `embedding.dimensions` value or the vector column cannot be created [38].

Local inference has a second, more valuable role. The expensive part of any memory system is the extraction pass that decides what to store, and OpenClaw runs that as a dedicated background consolidation model turn rather than on the busy reply path [6]. Running that tier locally, on a small model, removes the recurring per-turn API cost that the earlier part of this discussion identified as the new bottleneck. It is also the tier that must not be run on a weak model, because a bad extractor poisons everything above it.

On the local runtime itself, both Ollama and LM Studio sit on llama.cpp, and both do have KV cache, so the question raised in the earlier discussion has a definite answer. The cache is automatic in Ollama, and the lever is `keep_alive`: the default unload after five minutes discards the cached state, `-1` keeps the model and its cache resident indefinitely, and `OLLAMA_KEEP_ALIVE` sets the default for the server [28]. The K/V cache can itself be quantised through `OLLAMA_KV_CACHE_TYPE`, with `q8_0` using roughly half the memory of the default `f16` and `q4_0` roughly a quarter, both requiring flash attention to be enabled [28]. The llama.cpp server exposes the same capability as flags, with `--cache-prompt` on by default, `-np` setting the number of parallel slots each holding its own cache, `--cache-reuse` and `--cache-idle-slots` extending reuse, and a slot save and restore API for persisting a warm cache to disk [29]. Ollama also has an experimental `OLLAMA_PREFILL_CACHE=1` mode that saves the prefill cache to disk before unload and restores it on reload, capped at 8 GiB and off by default [31].

Two operational details are easy to lose. Cache reuse is process-scoped rather than session-scoped, so a shared local server benefits every client sending the same prefix, with no per-session isolation [30]. And the context window must be set explicitly and held constant, because changing it between requests is treated as a different model configuration and forces a reload [30].

## Provenance, poisoning, and deletion limits

The risk surface of a memory system that persists is that a poisoned entry is re-injected on every future session. OpenClaw's answer, which is the pattern worth copying, is structural rather than detection-based: unforgeable provenance stored in database columns rather than parsed from prose, quarantine by tier so that untrusted content can be stored and searched but never auto-injects, taint propagation through consolidation, and a review surface in `DREAMS.md` that records what entered long-term memory and from where [6]. The platform's own stated position is that independent poisoning benchmarks score agents better the less automatically they retrieve and the more conservatively they write [6].

Deletion is where most self-built systems are quietly incomplete, and the platform documentation is explicit about its own limits. `openclaw memory forget` removes derived memory attributable to a session, a hook source or a participant, supports `--dry-run` and `--json` for previewing a selection, and purges a person or a source end to end [32]. It does not delete original session transcripts, every freeform memory edit, or every copy that was retained [32]. Session deletion is a separate lifecycle operation [32]. The practical rule follows: once a secret has entered memory, rotate it rather than relying on deletion.

## Evaluation method for a personal memory system

Published leaderboards are not a usable evaluation method, for the reasons set out above. What works for a personal system is a small, self-authored test set plus the platform's own inspection tooling.

The test set should be personal and behavioural rather than merely factual: which units are used, which language to reply in, how long a status update should be, where the staging server lives, which terms get corrected. A retrieval hit that is not applied as behaviour is a failure, which is what makes the PrefEval and HorizonBench distinction operationally important.

The inspection tooling is already there. `openclaw memory status` reports index and provider state, with `--deep` checking vector-store and embedding-provider readiness and `--index` reindexing a dirty store [33]. `openclaw memory search` runs a query against the index with `--min-score` and `--json` [33]. `openclaw memory forget --dry-run --json` previews exactly what a deletion would remove, which doubles as a leak audit [33]. The platform also ships a local QA pack for personal-assistant workflows with ten scenarios, including preference recall and a redaction check that no secret leaks, runnable against a mock provider so no live account is touched [34].

## Reference architecture for asuka-agent

The architecture that follows from the research keeps five layers, each with one owner, one budget, and one write policy.

| Layer | Content | Scope | Injection | Write policy |
| --- | --- | --- | --- | --- |
| `USER.md` | Preference directives, under 4,000 characters | Global across agents | Always, at the front of the prompt | Human edits, model proposes via review |
| `MEMORY.md` | Durable facts and decisions | Per agent | Session start, budgeted | Gated consolidation only |
| `memory/YYYY-MM-DD.md` | Episodic notes and transcripts | Per agent | On demand via search | Free-form during work |
| `agents/<id>/openclaw-agent.sqlite` | FTS5 and vector index | Per agent | Never | Derived, rebuildable |
| Embedding provider | Local model, or `none` for FTS-only | Local machine | Not applicable | Not applicable |

The ordering is the point. Preferences are global and injected first because they are small, high-value, and benefit from prefix caching. Facts are per-agent because they accumulate from that agent's conversations. Episodes are per-agent and large, so they are searched rather than injected. The index is derived and can be rebuilt at any time, which is what makes the whole arrangement safe to inspect and cheap to correct.

Three deployment choices follow from the earlier analysis. Keep embeddings local so that personal memory text does not leave the machine by default, and use `provider: "none"` until the corpus justifies semantics. Put the profile block at the front of the prompt with nothing dynamic above it, so the cache hits on the largest part of every request. And route by cost profile, with routine memory-heavy turns on MiniMax M3 at $0.30 per million input tokens and reasoning-heavy turns on a stronger model, given that the same prefix costs ten times more on Kimi K3.

The configuration in `config/config.yaml` already matches this structure: the agent token list maps to per-account bot tokens, the manager token list maps to the orchestrating account, and the allowed user ID list maps to `allowFrom`. Two adjustments are needed when it is wired to a real deployment. The allowed user IDs should be numeric, because the channel layer normalises `telegram:` and `tg:` prefixes but expects numbers otherwise, and an empty list under an `allowlist` policy is a configuration error rather than a neutral state [19]. Each named account needs an explicit token because the environment variable fallback resolves only for the default account [20].

## Limits of the evidence base

Three limitations bear on how far these conclusions travel.

The benchmark picture is contested rather than settled. A nine-point revision on one dataset, retractions of earlier published figures, and a twenty-point spread between self-reported and independently measured scores for the same system all indicate that any single number should be treated as a claim rather than a result [3][4][5]. What survives that scrutiny is the weaker and more useful claim, that retrieval sophistication alone does not reliably beat a full-context baseline for a bounded personal corpus [2][4].

The cost model is parametric rather than absolute, because message volume and profile size are properties of the deployment rather than of the research. The unit prices cited here are first-party listings, and MiniMax's own notice that rates vary by model, API and configuration applies to them [23][25][22]. Providers change prices frequently, so a rate card should be re-checked before a budget is committed.

The local-runtime description rests on Ollama's own documentation and on the llama.cpp server flags [28][29][31]. The equivalent behaviour in LM Studio is described here at the llama.cpp layer, where the keep-loaded setting and the slot cache are the same mechanisms, but LM Studio's own documentation was not consulted directly for this report. The claim that both runtimes keep a KV cache and expose a way to retain it across requests is well supported; the specific configuration path in LM Studio is the part that would need checking against its current documentation.

## References

[1] Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers (arXiv:2603.07670) - https://arxiv.org/abs/2603.07670

[2] Add Standard Memory Evaluation Benchmarks (LOCOMO, MemoryArena) - letta-ai/letta issue 3115 - https://github.com/letta-ai/letta/issues/3115

[3] Memory Atlas, LLM and agent memory catalogued: benchmarks - https://www.memoryatlas.dev/benchmarks

[4] LoCoMo, Long-Term Conversational Memory benchmark results - https://mnemoverse.com/docs/technology/benchmarks/locomo

[5] Best Evaluation Datasets and Benchmarks for Agent Memory - Cognee - https://www.cognee.ai/agent-memory-evaluation-datasets-benchmarks

[6] OpenClaw, Memory architecture - https://docs.openclaw.ai/concepts/memory-architecture

[7] PrefEval, a benchmark for evaluating preference following (arXiv:2502.09597) - https://arxiv.org/abs/2502.09597

[8] HorizonBench (arXiv:2604.17283) - https://arxiv.org/abs/2604.17283

[9] OpenClaw, Memory overview - https://docs.openclaw.ai/concepts/memory

[10] Hermes Agent, Persistent Memory - https://hermes-agent.nousresearch.com/docs/user-guide/features/memory

[11] Hermes Agent, Memory Providers - https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers

[12] How Hermes Agent Memory Actually Works, and How to Make It Better - Vectorize - https://vectorize.io/articles/hermes-agent-memory-explained

[13] MINJA, memory injection attack against LLM agents (arXiv:2503.03704) - https://arxiv.org/abs/2503.03704

[14] OpenClaw, User model - https://docs.openclaw.ai/concepts/user-model

[15] Memory FAQ - OpenAI Help Center - https://help.openai.com/en/articles/8590148-memory-faq

[16] Bringing memory to teams - Anthropic - https://claude.com/resources/articles/memory

[17] Mem0 repository and README, scoped search filters - https://github.com/mem0ai/mem0

[18] OpenClaw, Multi-agent - https://docs.openclaw.ai/concepts/multi-agent

[19] OpenClaw, Telegram access control - https://docs.openclaw.ai/channels/telegram/access-control

[20] OpenClaw, Telegram setup - https://docs.openclaw.ai/channels/telegram/setup

[21] Prompt Caching - MiniMax API Docs - https://platform.minimax.io/docs/api-reference/text-prompt-caching

[22] Prompt caching - OpenAI API documentation - https://developers.openai.com/api/docs/guides/prompt-caching

[23] Pricing Overview - MiniMax API Docs - https://platform.minimax.io/docs/pricing/overview

[24] Best Practices for context caching - Kimi API Platform - https://platform.kimi.ai/docs/guide/context-caching

[25] Model Inference Pricing - Kimi API Platform - https://platform.kimi.ai/docs/pricing/chat

[26] Local embedding models for RAG, 2026 comparison - d-central - https://d-central.tech/local-embedding-models/

[27] Local Multilingual Embedding Models, CPU reference comparison - ValRCS - https://github.com/ValRCS/local_embedding_models

[28] FAQ, keep_alive and KV cache quantisation - Ollama documentation - https://docs.ollama.com/faq

[29] Prompt Caching, llama.cpp server flags and slot cache - Ollama in Action Book - https://github.com/mark-watson/Ollama_in_Action_Book/blob/main/manuscript/PromptCaching.md

[30] Ollama and llama.cpp: Architecture and Inference - yuqiii-wang - https://yuqiii-wang.github.io/blogs/programming/python/ai/llm_server/ollama.html

[31] server: warm prefill cache across model unload/reload - ollama/ollama issue 17247 - https://github.com/ollama/ollama/issues/17247

[32] OpenClaw, Memory provenance and deletion - https://docs.openclaw.ai/concepts/memory-provenance

[33] OpenClaw, memory CLI reference - https://docs.openclaw.ai/cli/memory

[34] OpenClaw, Personal agent benchmark pack - https://docs.openclaw.ai/concepts/personal-agent-benchmark-pack

[35] OpenClaw, Memory search - https://docs.openclaw.ai/concepts/memory-search

[36] OpenClaw, Builtin memory engine - https://docs.openclaw.ai/concepts/memory-builtin

[37] OpenClaw, Memory configuration reference - https://docs.openclaw.ai/reference/memory-config

[38] OpenClaw, Memory LanceDB plugin - https://docs.openclaw.ai/plugins/memory-lancedb
