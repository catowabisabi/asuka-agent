# Personal Memory Test Set

A synthetic persona with a seeded workspace, used to check that the memory
system actually recalls and obeys, rather than appearing to.

Everything here is fictional. The persona is described in
[persona.md](persona.md).

## Layout

```
tests/personal/
├── README.md                     this file
├── persona.md                    who Ho Ka-yan is, and what the gaps are
├── testset.yaml                  retrieval cases and behavioural cases
├── verify-index.py               runs the retrieval cases, no dependencies
├── workspace/                    the orchestrator's seeded workspace
│   ├── USER.md                   the profile, 18 directives
│   ├── MEMORY.md                 12 curated facts
│   └── memory/
│       └── 2026-10-21.md         one day of activity
└── workspace-worker-research/    a second agent, isolated
    ├── USER.md
    └── MEMORY.md
```

## Running the index checks

```
python3 tests/personal/verify-index.py
```

Needs Python 3.8+ and a SQLite build with FTS5, both default in CPython. No
packages to install.

The script builds the same corpus under both FTS5 tokenizers, probes the
short-term floor, checks that the two workspaces stay isolated, and runs every
retrieval case in `testset.yaml`. It exits non-zero if an assertion fails.

## Two kinds of case

**Retrieval cases** carry `must_hit` or `must_miss` and are checked by the
script. Each fact is tested twice: once `as_written`, using a phrase the note
actually contains, and once `paraphrased`, using the wording a person would
naturally reach for.

**Behavioural cases** carry `directive`, `required` and `forbidden`, and need a
live agent session. They check whether a directive was applied to a reply,
which no index test can answer.

## The expected state of the free tier

The `as_written` cases pass. The `paraphrased` cases fail, and that is
correct, not a defect.

A trigram index matches a query only when a contiguous run of three or more
characters appears in both the query and the note. The free tier therefore
gives literal string retrieval rather than memory. The full measurement is in
[research/07-cjk-retrieval-notes.md](../../research/07-cjk-retrieval-notes.md).

When a local embedding provider is enabled, the `paraphrased` cases should
start passing. Inverting their assertions in `testset.yaml` is the measurement
that the upgrade bought something.

## Writing the notes

Three rules, all consequences of the three-character floor:

1. **Write in the user's language.** Cantonese notes, English directives. A
   Cantonese question against English notes shares almost no characters, and
   recall collapses.
2. **Never let a fact live only as a two-character term.** `佢叫阿黑`, not
   `阿黑`. `去大阪嘅機票`, not `大阪`.
3. **Trigger phrases need three or more characters, phrased the way a person
   would type them.** `上瑜伽` rather than `瑜伽`, `飲咖啡` rather than `咖啡`,
   `去京都` rather than `京都`.

## Running the behavioural cases

With an agent running against the seeded workspace:

1. Point the agent's workspace at `tests/personal/workspace`.
2. Send each `prompt` from the behavioural section.
3. Check the reply against `required` and `forbidden`.
4. For `pref-preamble-02`, read only the first line. If it restates the
   question, the profile is not being injected.
5. For `prefix-stability-14`, capture the rendered request for two consecutive
   turns and diff them. Everything above the tail must be byte identical.

Cases that need a fresh session are marked in their `notes`. A fact written
during a session is not in the prompt until the next session starts, because
the profile snapshot is frozen.
