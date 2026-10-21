# Memory Architecture

Deep dive behind the first half of the recommendation in [report.md](report.md):
which memory architecture to run, and why the retrieval stack is the smaller
half of the problem.

## Benchmark reliability as a design input

LoCoMo is the standard reference for long-term conversational recall: roughly
1,986 questions across single-hop, multi-hop, temporal and open-domain
categories, of which 446 are adversarial [2][5]. Recent comparisons have begun
omitting the adversarial subset, which inflates headline accuracy precisely
because those items are designed to catch over-confident answers [5].

The usable signal is the spread between how the same system scores when
different parties run it:

| System | Self-reported | Independent run | Source |
| --- | --- | --- | --- |
| Mem0 on LongMemEval | 94.4 | 49 | [3][6] |
| Zep / Graphiti on LongMemEval | 90.2 | 58.6 | [3] |
| Naive cosine floor against a tuned system, recall at 10 | 0.7138 | 0.6939 | [4] |

A nine-point revision on one dataset arose when Zep's original 84% was
challenged as 58.44% and then revised to 75.14% [5]. Earlier published Zep and
Mem0 figures have been retracted outright [4]. A benchmark score produced by
one party about one system is a claim, not a result.

The figures that matter for a decision are the ones that hold regardless of who
ran them. A 2026 survey of agent memory reports that systems scoring
near-perfectly on LoCoMo fall to 40-60% on MemoryArena, which interleaves memory
with decision-making [1]. The numbers quoted there put Mem0 at 37.09%, MemOS at
42.55% and Zep at 39.97%, all below a Gemini-3-Flash full-context baseline at
72.61% [2]. The survey's own framing is that memory is a write-manage-read loop
coupled to perception and action, with continual consolidation, causally
grounded retrieval, trustworthy reflection and learned forgetting still open as
research problems [1].

For a single-user assistant whose entire corpus is one person's preferences and
projects, the full-context baseline is not a strawman. It is the bar.

## Three memory shapes

| Shape | Examples | What it optimises | Fit for this stack |
| --- | --- | --- | --- |
| Memory layer or API | Mem0, Graphiti and Zep, Supermemory | Extraction quality, multi-backend storage, managed hosting | High integration cost; the benchmark spread does not justify it |
| Agent runtime with built-in memory | Letta, the ex-MemGPT lineage | Long-horizon autonomous agents that edit their own memory | Overkill; requires moving the agent into the runtime |
| Local-first file and index layer | OpenClaw built-in, Hermes built-in, Holographic, LanceDB plugin | Inspectable files, bounded injection, no cloud dependency | Already installed; the layer to build on |

The third row matches the constraint set, for one reason: the file is the source
of truth and the index is derived. OpenClaw's memory is plain Markdown in the
agent workspace with no hidden state [9]. Hermes stores `MEMORY.md` and
`USER.md` under `~/.hermes/memories/` and injects them as a frozen snapshot at
session start [10]. Both are inspectable and editable with a text editor, and
both can have their index rebuilt without loss.

Hermes ships eight external providers, of which only one preserves that
property. Holographic is a local SQLite fact store with FTS5, trust scoring and
algebraic queries, needs no external dependencies and costs nothing [11]. The
other frequently discussed option, Hindsight, is described as fully local with
Ollama but still relies on a bundled PostgreSQL, embedder and reranker [12].
Honcho, the deepest user-modelling option, is AGPL-3.0, which matters if it is
self-hosted and linked into a networked service [12].

## The five-tier model

OpenClaw's architecture documents memory as five tiers, and this is the most
transferable design idea in either platform [6].

**Instructions** are the human-authored `AGENTS.md` and workspace instruction
files. Always injected, never written by the model.

**The curated core** is `MEMORY.md` and `USER.md`. Written only through gated
consolidation, injected at session start under a budget.

**The episodic tier** is `memory/YYYY-MM-DD.md` daily notes plus session
transcripts. Written freely during work, retrieved on demand rather than at
session start.

**Prospective memory** is standing intents in SQLite plus cron jobs. Injected
only when a trigger fires.

**Review material** is `DREAMS.md` and the dreaming reports. Never injected;
exists for human reading.

The boundary between the curated core and the episodic tier is the one that
matters. Curated files are small, normally in context, and written only through
gated consolidation. Episodic files are large, append-friendly, and reached
through search rather than loaded at startup. Nothing crosses from episodic into
curated without passing the promotion gates [6].

## Write-path curation

The consolidation model turn is the single primary writer to the curated tier.
It is allowed to merge duplicates, supersede entries using supersession keys,
and keep entries compact, and the previous version of the file is stored as a
pre-image with a human-readable summary of what changed appended to
`DREAMS.md` [6]. A rewrite is accepted only if it passes structural validation,
stays within the bootstrap budget, and does not lose more than a bounded
fraction of existing entries; a rejected rewrite falls back to append-only for
that sweep. Replacing the file uses optimistic concurrency, with the content
hash re-checked immediately before an atomic rename, so an edit made in an
editor during the consolidation turn aborts the rewrite rather than losing the
human's change [6].

This is the design's load-bearing idea, and it rests on the finding that
retrieval over notes files is competitive with far heavier designs, while
unreliable write-time curation is what degrades memory systems. Long-horizon
evaluations consistently show that what was written matters more than how it is
indexed [6]. A single writer also removes the failure mode where a model
accumulates contradictory entries indefinitely, which is the same failure
documented for preferences [8].

The write path is also the security boundary, and it is enforced structurally
rather than by detection. Every memory carries a provenance class from a closed
set of `owner`, `agent`, `untrusted` and `system`, stored in SQLite columns the
model cannot write through prose; content whose provenance cannot be determined
is treated as untrusted if externally derived [6]. Content recalled from memory
is marked so it is never re-extracted as a new fact, so a fact recalled a
hundred times stays one fact [6]. A tool that declares its output as
network-sourced taints the rest of that turn, so untrusted content cannot ride
into the curated core inside an otherwise trusted turn [6].

The platform's own worked example of a poisoning attempt shows where each
defence lands: a web page instructing the agent to always pipe a shell command
lands in the episodic tier labelled untrusted, never auto-injects, cannot be
promoted by recall frequency, and if explicitly searched arrives wrapped as
untrusted context [6]. The memory-poisoning literature reaches the same
conclusion, and detection-based defences measure poorly [6][13].

## What this implies for asuka-agent

Do not adopt a memory framework. Adopt the file-first shape that the installed
platform already provides, keep a single writer to the curated tier, and spend
the effort on two things a framework would not give: a bounded, hand-edited
preference file (covered in [02-preference-and-scope.md](02-preference-and-scope.md))
and a stable prompt prefix that makes the whole thing cheap
([03-cost-and-caching.md](03-cost-and-caching.md)).

Full reference list: [05-sources.md](05-sources.md)
