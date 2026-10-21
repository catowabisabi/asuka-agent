# Preference Storage and Scope

Deep dive into the two mechanisms that decide whether an assistant with memory
behaves correctly: how a preference is stored and updated, and how memory is
scoped when several agents share one person.

## Preferences are not memories

Conflating the two produces the characteristic failure of an assistant that
recalls correctly and still behaves wrongly. It retrieved the right fact and
then answered against it, because the fact had been superseded, or because a
preference that was merely present in the context had stopped being applied.

OpenClaw keeps `USER.md` separate from `MEMORY.md` for exactly this reason.
The stated reason is that preference adherence and fact recall fail differently:
benchmarks show that models stop applying a preference that is merely present in
context after a handful of turns, while restating the relevant directive near
the query restores adherence better than heavier retrieval or self-critique
machinery [6].

## The preference contract

`USER.md` has a fixed 4,000-character bootstrap cap, smaller than the general
per-file budget, and configuration can only lower that cap and never raise it
[14]. The intent is that profile guidance stays directive-sized so it cannot
crowd project rules or durable facts out of the shared prompt budget.

Each entry is a metadata line followed by exactly one imperative directive:

```markdown
<!-- observed: 2026-07-27 | status: active -->

- Prefer concise progress updates during implementation work.
```

The four rules are to begin with an imperative such as Always, Never or Prefer,
to record the date the preference was observed, to use only `active` or
`superseded` for status, and to keep one behavioural instruction per directive
[14]. The file is not a dossier: only details that improve assistance belong in
it [14].

A changed preference is updated in place, never appended as a second active
directive. The superseded entry stays next to its replacement so the current
directive is unambiguous [14]. This is a direct response to HorizonBench, which
found that systems often select an originally stated preference after the user
has changed it; append-only contradictory history recreates that failure mode
[8].

The full ladder for storage follows from the budget. Stable preferences and
communication style go in `USER.md`. Durable non-profile facts, decisions and
lessons go in `MEMORY.md`. Detailed observations and running context go in
daily `memory/YYYY-MM-DD.md` files, which stay reachable on demand without
spending the always-injected budget. Event-conditioned future actions become
standing intents, and exact-time or recurring actions become scheduled tasks
[14]. When the cap is reached, `openclaw doctor` names it and recommends
compacting the file [14].

## Hermes as the comparison point

Hermes enforces the same separation with character limits rather than a richer
format. `MEMORY.md` holds the agent's own notes, environment facts, conventions
and learned lessons, capped at 2,200 characters, about 800 tokens.
`USER.md` holds the user profile, preferences, communication style and
expectations, capped at 1,375 characters, about 500 tokens [10]. Typical
occupancy is 8-15 entries in the former and 5-10 in the latter [10].

Entries are separated by a section-sign delimiter, and the injected block
carries a header showing which store it came from together with the usage
percentage and character counts, so the agent can see its remaining capacity
[10]. Duplicate entries are rejected automatically, and entries are scanned for
injection and exfiltration patterns before acceptance, since they are injected
into the system prompt [10].

The two systems differ in one way that matters for cost. Hermes has no `read`
action for memory; the content is injected at session start and the agent sees
it as part of its conversation context [10]. Writes go through the `memory` tool
with `add`, `replace` and `remove`, where replace and remove match on a short
unique substring [10].

## The frozen snapshot

A fact saved during a session appears in the prompt only at the next session
start. Hermes states the reason directly, and it is not a limitation: the
freeze preserves the LLM's prefix cache for performance [10]. The memory block
is part of the cached prefix, so a memory block that mutates mid-session
invalidates the cache for everything after it.

That is the mechanism that connects memory design to token cost. It is also why
the profile belongs at the front of the prompt rather than appended near the
user's message, and why the `USER.md` budget is worth defending rather than
expanding.

## Scope as a retrieval filter

ChatGPT's project behaviour is a scoping effect, and the mechanism is
documented as a hard boundary. Chats can reference other conversations in the
same project, but they cannot reference conversations outside the project, and
chats outside the project cannot reference conversations in it [15]. Claude
implements the same model, with a separate memory space per project plus a
global memory for non-project conversations, and an incognito mode that feeds
neither [16].

OpenClaw implements the same boundary as a filter rather than a partition, and
the difference is instructive. Repository work adds a trailing project
annotation to the memory entry, derived from the normalised `origin` remote, so
ordinary clones and linked worktrees of one repository converge on a key while
forks stay separate [6]. Project scope changes ranking and automatic injection
without partitioning the files [6].

The mechanics are specific. Each session keeps up to four recently active
repository keys in most-recent-first order, and that set is ephemeral runtime
state that is neither persisted nor restored [6]. Ranked search boosts entries
from any active repository, mildly demotes entries from another repository, and
leaves untagged memory neutral. Trigger injection is stricter: a tagged entry
is eligible only while every project key on it is in the active set. A compact,
separately budgeted project-memory block is built for the active repositories
each turn [6]. `USER.md` and standing intents remain user-level and are never
project-scoped [6].

The shape to copy for a personal assistant is therefore one store, one filter
column, multiple scopes. A separate database per scope multiplies the write path
and makes cross-scope recall impossible. Mem0 exposes the same primitive at the
API level, where a search takes a filter on the owner identifier [17].

Scope also has to be attached to the write, not only the read. A memory written
inside one project but not tagged leaks into every other project on the next
retrieval. OpenClaw solves this by having the runtime pass the resolved project
key into the memory prompt sections and instructing the agent to annotate new
repository-specific entries with it [6].

## Per-agent isolation and Telegram routing

The project configuration already has the right shape: a list of agent bot
tokens, a list of manager bot tokens, and a list of allowed user IDs.

On the OpenClaw side, each agent is one brain with its own workspace, its own
state directory, its own SQLite-backed session history, and its own memory index
at `~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite` [18]. Routing is
by binding with a fixed precedence order: exact peer, parent peer, peer
wildcard, guild plus roles, guild, team, account, channel, then fallback owner
[18]. Multiple bindings matching at the same tier resolve to the first in
configuration order, and traffic that matches no binding is not handed to an
arbitrary first-listed agent but requires an explicit owner [18].

Telegram is one of the channels that supports multiple accounts, each
identified by `accountId` and routed to its own agent [18]. A manager bot is
therefore an account bound to the orchestrating agent, and each worker bot is
an account bound to its own agent with an isolated memory index.

One consequence deserves attention. Since v2026.8.1 the QMD backend was retired
and built-in memory no longer searches another agent's transcript corpus; shared
reference material is placed in an explicit shared directory via
`memory.search.extraPaths`, and each agent indexes it independently [18]. The
global user profile is the one thing that should cross agent boundaries, and in
OpenClaw that role belongs to the shared workspace `USER.md` or to the
per-person file under `users/<canonical-profile-id>/USER.md` on a shared
Gateway [14]. The per-agent `MEMORY.md` stays private to that agent.

## Access control in the Telegram layer

The direct-message policy has three values. `pairing` is the default and lets a
user approve the bot through a pairing code. `allowlist` requires at least one
sender ID in `allowFrom`. `open` requires `allowFrom` to include a wildcard
[19].

The allowed-ID list takes numeric Telegram user IDs, and `telegram:` and `tg:`
prefixes are accepted and normalised [19]. Two failure modes are worth
designing against.

An `allowlist` policy with an empty `allowFrom` blocks all direct messages and
is rejected by configuration validation [19]. An empty list in the YAML is
therefore a startup failure rather than a silent open door, which is the safe
direction but should still be caught in configuration review.

A restrictive top-level `allowFrom` is a safety boundary in its own right. An
account-level `allowFrom: ["*"]` does not make that account public unless the
merged effective allowlist still contains an explicit wildcard [19]. For a
deployment with one manager bot and several worker bots, the correct shape is a
top-level list holding the real numeric IDs, with each account inheriting it,
rather than each account carrying its own wildcard. Separately,
`groupAllowFrom` falls back to `allowFrom` when unset, and group sender
authorisation never inherits DM pairing approvals [19].

Token resolution follows a different precedence from the access list. `tokenFile`
beats `botToken`, `botToken` beats the environment, and the
`TELEGRAM_BOT_TOKEN` environment variable resolves only for the default account
[20]. Named accounts therefore need an explicit `botToken` or `tokenFile`, which
suits the list-of-tokens structure in `config/config.yaml` far better than a
single environment variable would.

The two practical adjustments to the existing configuration are therefore
numeric allowed user IDs, and an explicit token per named account.

Full reference list: [05-sources.md](05-sources.md)
