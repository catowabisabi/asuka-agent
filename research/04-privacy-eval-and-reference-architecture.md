# Privacy, Evaluation, and the Reference Architecture

Deep dive into the risk surface of a persistent memory system, the method for
measuring whether it works, and the concrete architecture that follows.

## Provenance as a structural defence

The risk surface of a memory system that persists is that a poisoned entry is
re-injected on every future session. A single successful injection therefore
persists indefinitely, which is what makes memory poisoning a distinct attack
class rather than a variant of prompt injection [13].

OpenClaw's answer is structural rather than detection-based, and the pattern is
the part worth copying:

- **Unforgeable provenance.** Origin labels live in SQLite columns written by
  classification code, never parsed out of memory text. Prose claiming to be
  from the owner does not make it owner content [6].
- **Quarantine by tier.** Untrusted-origin content can be stored, indexed and
  explicitly searched, but is structurally barred from the curated core and
  from auto-injection. The only paths into the prompt are explicit tool calls
  and the escalation lane, both of which wrap results in untrusted-content
  framing [6].
- **Taint through consolidation.** The promotion gates check the provenance of
  candidates, not just their scores, so untrusted content cannot launder itself
  into `MEMORY.md` through a daily note and a theme reflection [6].
- **Review surfaces.** Every consolidation writes its summary and pre-image
  trail to `DREAMS.md`, so what entered long-term memory and from where is
  always reviewable after the fact [6].

The platform's own stated position is that independent poisoning benchmarks
score agents better the less automatically they retrieve and the more
conservatively they write [6]. The broader literature agrees that
detection-based defences measure poorly [6][13].

The practical implication for a system built on top of an existing platform is
to keep the default behaviour and resist loosening it. Auto-injection of
unreviewed content is the setting most worth leaving off.

## Deletion limits

Deletion is where most self-built systems are quietly incomplete, and the
platform documentation is explicit about its own limits.

`openclaw memory forget` removes derived memory attributable to a session, a
hook source or a participant, supports `--dry-run` and `--json` for previewing a
selection, and can purge a person or a source end to end [32]. It does not
delete original session transcripts, every freeform memory edit, or every copy
that was retained [32]. Session deletion is a separate lifecycle operation [32].

The rule that follows is simple: once a secret has entered memory, rotate it
rather than relying on deletion. Deletion is for tidiness and for removing
memories that are wrong or superseded, not for un-leaking a credential.

Because this repository is public, the memory store itself must live outside
the tracked tree. The `private-folder/` directory ignores its own contents and
`config/config.local.yaml` is already excluded by the root `.gitignore`.

## Evaluation method

Published leaderboards are not a usable evaluation method, for the reasons set
out in [01-memory-architecture.md](01-memory-architecture.md). What works for a
personal system is a small, self-authored test set plus the platform's own
inspection tooling.

The test set should be personal and behavioural rather than merely factual.
Useful items are which units are used, which language to reply in, how long a
status update should be, where the staging server lives, which terms get
corrected, and which tools must never be run without approval. A retrieval hit
that is not applied as behaviour is a failure, which is what makes the PrefEval
and HorizonBench distinction operationally important rather than academic [7][8].

Each item should be testable in two states. Ask the question in a fresh
session, and ask it again after the relevant file has changed, because the
supersede-in-place rule only proves itself on the second pass.

The inspection tooling is already present:

| Command | Purpose |
| --- | --- |
| `openclaw memory status` | Index and provider state |
| `openclaw memory status --deep` | Vector store and embedding provider readiness |
| `openclaw memory index --force --agent <id>` | Rebuild after an embedding or chunking change |
| `openclaw memory search "<query>" --json` | Confirm a specific memory is retrievable |
| `openclaw memory forget --dry-run --json` | Preview a deletion, and audit what would be removed |

The platform also ships a local QA pack for personal-assistant workflows with
ten scenarios, including preference recall and a redaction check that no secret
leaks, runnable against a mock provider so no live account is touched [34].

## Reference architecture

The architecture that follows from the research keeps five layers, each with one
owner, one budget, and one write policy.

| Layer | Content | Scope | Injection | Write policy |
| --- | --- | --- | --- | --- |
| `USER.md` | Preference directives, under 4,000 characters | Global across agents | Always, at the front of the prompt | Human edits, model proposes via review |
| `MEMORY.md` | Durable facts and decisions | Per agent | Session start, budgeted | Gated consolidation only |
| `memory/YYYY-MM-DD.md` | Episodic notes and transcripts | Per agent | On demand via search | Free-form during work |
| `agents/<id>/openclaw-agent.sqlite` | FTS5 and vector index | Per agent | Never | Derived, rebuildable |
| Embedding provider | Local model, or `none` for FTS-only | Local machine | Not applicable | Not applicable |

The ordering is the point. Preferences are global and injected first because
they are small, high-value, and benefit from prefix caching. Facts are per-agent
because they accumulate from that agent's conversations. Episodes are per-agent
and large, so they are searched rather than injected. The index is derived and
can be rebuilt at any time, which is what makes the whole arrangement safe to
inspect and cheap to correct.

Three deployment choices follow:

1. Keep embeddings local, so personal memory text does not leave the machine by
   default, and use `provider: "none"` until the corpus justifies semantics.
2. Put the profile block at the front of the prompt with nothing dynamic above
   it, so the cache hits on the largest part of every request.
3. Route by cost profile, with routine memory-heavy turns on MiniMax M3 at
   $0.30 per million input tokens and reasoning-heavy turns on a stronger
   model, given that the same prefix costs ten times more on Kimi K3.

## Mapping to the existing configuration

`config/config.yaml` already matches this structure. The agent token list maps
to per-account bot tokens, the manager token list maps to the orchestrating
account, and the allowed user ID list maps to `allowFrom`.

Two adjustments are needed when it is wired to a real deployment. The allowed
user IDs should be numeric, because the channel layer normalises `telegram:`
and `tg:` prefixes but expects numbers otherwise, and an empty list under an
`allowlist` policy is a configuration error rather than a neutral state [19].
Each named account needs an explicit token, because the environment variable
fallback resolves only for the default account [20].

A third, smaller one: the allowed user ID list should be expressed once at the
top level rather than repeated per account, since a restrictive top-level
`allowFrom` acts as a safety boundary that an account-level wildcard cannot
override [19].

## What to do first

In order, and the order matters:

1. Set up the `USER.md` contract with the four rules, and write the current
   preferences into it by hand.
2. Set `memory.search.provider` to `"none"` and confirm keyword search works
   before adding any embedding dependency.
3. Pin the prompt layout so the prefix is byte-identical across turns, and
   measure the cache hit rate before and after.
4. Build the small personal test set and run it against a fresh session.
5. Only then consider a local embedding model, and re-run the index afterwards.

Full reference list: [05-sources.md](05-sources.md)
