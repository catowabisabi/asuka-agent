# Skills

Skills the agents in this project can load. The source of truth is this
repository; what runs is a copy or a link to it, so a skill that was reviewed
is the skill that runs.

## Contents

| Skill | What it does |
| --- | --- |
| `memory-commands/` | Store, recall, forget and review memories on request |

## Installing

### From a repository checkout

Add the repository's `skills` directory to the extra search roots:

```json5
{
  skills: {
    load: {
      extraDirs: ["/absolute/path/to/asuka-agent/skills"],
    },
  },
}
```

This is what `config/openclaw.json5` does. The path has to be absolute, and
it has to be the `skills` directory itself, not the repository root.

### Into a single agent's workspace

Copy or symlink the skill directory into the agent's workspace:

```
<workspace>/skills/memory-commands/SKILL.md
```

Workspace skills have the highest precedence and are visible only to that
agent. Symlinked skill folders work, but every `SKILL.md` realpath has to stay
inside the allowed roots.

### Shared across every agent

```
<state-dir>/skills/memory-commands/SKILL.md
```

Shared managed skills are visible to all agents using that state directory.
This is the right place for a command the manager and the workers both need.

### Per-agent allowlists

Discovery and visibility are separate. A skill in a configured root is in the
inventory, but an agent only sees it if the allowlist includes it:

```json5
{
  agents: {
    defaults: { skills: ["memory-commands"] },
    entries: {
      asuka: { skills: ["memory-commands"] },
    },
  },
}
```

A per-agent list replaces the default list rather than merging with it, so a
per-agent entry must name everything that agent needs. Omitting the key
entirely leaves the agent unrestricted.

## Verifying the install

```bash
openclaw skills check          # discovery, readiness and visibility
openclaw skills list           # what each agent can see
```

A skill can be present in the inventory and still not be visible, because
readiness failed (a missing binary, an unset environment variable, a config
path that does not exist) or because an allowlist excluded it. `skills check`
reports which of the three it is.

## Token cost

An eligible skill is injected into the system prompt as a compact XML entry,
at roughly 97 characters plus the name, the description and the location.
That block sits in the system prompt, so it is part of the cacheable prefix
described in [../config/system-prompt.md](../config/system-prompt.md).

Keep `description` short. It is the only part the model sees before it
decides whether to load the skill, and it is billed on every turn.

## The memory-commands skill

Four commands, triggered by their Cantonese phrases or by the slash form
`/memory_commands`.

| Trigger | Action |
| --- | --- |
| 記住, 記低, 記埋 | Write one entry |
| 搵返, 搵, 查下 | Recall and report |
| 唔好記, 刪除, 唔好記低 | Forget one entry |
| 記憶摘要, 睇下記憶, 記憶總覽 | Review current state |

The skill is user-invocable, so OpenClaw registers it as a slash command
under the sanitised skill name, `memory_commands`, and it appears in the
Telegram command menu on its own. Do not add a matching entry to
`channels.telegram.customCommands`: a custom entry is a menu row that
implements nothing, and a row that does nothing when tapped is worse than no
row.

The full entry contract, the budget rules, the platform write paths and the
failure cases are in
[memory-commands/references/contract.md](memory-commands/references/contract.md).
The skill reads it on demand, so the part that sits in the prompt stays small.
