# asuka-agent

> A personal assistant with **memory**, that **controls other agents**, and is **driven from Telegram**.

**繁體中文摘要：** 呢個 project 會建立一個個人助理 — 佢有記憶（記得你、記得偏好），
可以控制其他 agent（orchestrator），而你只需要用 Telegram 就可以遠端控制佢。

---

## What this is

`asuka-agent` is the **control plane** for a personal AI assistant.

- 🧠 **Has memory** — persists context, preferences and long-term notes across
  sessions, so the assistant actually remembers you instead of starting from
  zero every time.
- 🎛️ **Controls other agents** — acts as an orchestrator. It doesn't just
  answer; it delegates to specialised agents (or tools/skills) and merges the
  results back into one reply.
- 📱 **Controlled via Telegram** — talk to it from your phone like a chat.
  The manager bot is the remote control; the agent fleet sits behind it.

---

## Repository layout

```
asuka-agent/
├── .gitignore                 # global ignore rules (secrets, caches, venvs…)
├── README.md
├── config/
│   └── config.yaml            # runtime configuration (API keys, bot tokens)
└── private-folder/            # ⛔ PRIVATE — structure tracked, contents never
    ├── .gitignore             #    ignores everything inside this folder
    ├── skills/                #    custom skills the agent can load
    ├── tools/                 #    custom tool integrations
    └── references/            #    reference material / knowledge files
```

### `private-folder/`

This folder is **committed as a skeleton only**. Its own `.gitignore` ignores
every file inside it, so anything you drop into `skills/`, `tools/` or
`references/` stays local and is **never pushed to GitHub** — even though the
repo itself is public.

---

## Configuration

All runtime settings live in [`config/config.yaml`](config/config.yaml).

| Section | Variable | Type | Purpose |
|---|---|---|---|
| `agents` | `openai_api_key` | string | OpenAI API key |
| `agents` | `kimi_api_key` | string | Kimi (Moonshot) API key |
| `agents` | `minimax_api_key` | string | MiniMax API key |
| `agents` | `telegram_bot_token` | **list** | One bot token per agent instance — run several agents side by side |
| `telegram` | `manager_bot_token` | **list** | Manager bot token(s) that drive the control channel |
| `telegram` | `allowed_user_id` | **list** | Telegram numeric user IDs allowed to issue commands |

Values written as `${ENV_VAR}` are resolved from the environment at runtime,
so **real secrets never need to be committed**.

### Local setup

```bash
git clone https://github.com/<your-account>/asuka-agent.git
cd asuka-agent

cp config/config.yaml config/config.local.yaml   # untracked — see .gitignore
```

Then export the secrets:

```bash
export OPENAI_API_KEY="sk-..."
export KIMI_API_KEY="sk-..."
export MINIMAX_API_KEY="sk-..."
export TELEGRAM_BOT_TOKEN_1="123456:ABC..."
export TELEGRAM_MANAGER_BOT_TOKEN_1="123456:XYZ..."
```

Or skip the environment and inline the values directly in
`config/config.local.yaml` (never committed).

### Getting your Telegram user ID

Message [@userinfobot](https://t.me/userinfobot) — it replies with your
numeric ID. Add it to `allowed_user_id`. Everyone else is ignored.

---

## How the pieces fit together

```
        ┌──────────────┐
        │  Telegram    │   you chat with @your_manager_bot
        └──────┬───────┘
               │  allowed_user_id gate
               ▼
        ┌──────────────┐
        │  Manager Bot │   control plane / router
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ asuka-agent  │   memory + orchestration
        │   + skills   │   private-folder/{skills,tools,references}
        └──────┬───────┘
               │
      ┌────────┼────────┬──────────┐
      ▼        ▼        ▼          ▼
    OpenAI   Kimi    MiniMax   other agents
```

1. You send a message to the **manager bot** on Telegram.
2. The bot checks your ID against `allowed_user_id` — unknown IDs are dropped.
3. The manager routes the request to the right agent, tool or skill.
4. Results are written to **memory** and returned to you as a Telegram reply.

---

## Security checklist

- [x] The repo is **public** — no real secrets are committed.
- [x] `private-folder/` ignores its own contents.
- [x] `config/config.local.yaml` is gitignored.
- [ ] Rotate any token that was ever pasted into a public file.
- [ ] Keep `allowed_user_id` tight — it is the only thing standing between
      a stranger and your agent.

---

## License

MIT — do whatever you want with it.
