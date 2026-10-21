# Research Index

Research notes behind the memory layer of `asuka-agent`: what a personal assistant
with memory should actually run, on top of OpenClaw or Hermes, using MiniMax, Kimi
or OpenAI APIs, controlled from Telegram.

Every claim here is traced to a source. The full list of URLs is in
[05-sources.md](05-sources.md); the `[N]` markers used across these documents
index that list.

## Reading order

| Document | What it settles |
| --- | --- |
| [report.md](report.md) | The full synthesis: recommendation, evidence, cost model, reference architecture |
| [01-memory-architecture.md](01-memory-architecture.md) | Memory shapes, the five-tier model, the write path as the quality bottleneck |
| [02-preference-and-scope.md](02-preference-and-scope.md) | Preference storage as a distinct artifact, scope as a retrieval filter, per-agent memory under Telegram routing |
| [03-cost-and-caching.md](03-cost-and-caching.md) | Prompt-cache economics for the three providers, prefix layout, local inference and embeddings |
| [04-privacy-eval-and-reference-architecture.md](04-privacy-eval-and-reference-architecture.md) | Provenance, poisoning, deletion limits, evaluation method, the concrete architecture |

## Recommendation in brief

Build the memory layer as **files first, bounded, and scope-filtered**. A small
human-editable preference file injected at the front of the prompt, over a
per-agent searchable archive, with a local embedding provider. Three reasons:

1. **Retrieval sophistication does not reliably beat a full-context baseline for a
   bounded personal corpus.** On MemoryArena, systems that score near-perfectly on
   LoCoMo fall to 40-60%, and a naive cosine baseline has outscored a tuned system
   on recall@k. A vendor ranking is marketing, not measurement.
2. **The write path dominates quality.** What gets written matters more than how it
   is indexed. A single gated writer to the curated tier beats many writers.
3. **Preference adherence and fact recall fail differently.** A preference needs a
   directive with a status and an in-place update, not a vector row.

The vector store is the archive underneath, not the brain of the system.

## 摘要（繁體中文）

呢個 folder 係 `asuka-agent` 記憶層嘅研究筆記。目標係一個**有記憶**嘅個人助理：
用 OpenClaw 或者 Hermes 做 agent 框架，用 MiniMax / Kimi / OpenAI API 做推理，
用 Telegram 做控制介面。

**核心結論：記憶層應該“檔案先行、有上限、有 scope 過濾”。**

- 一個細嘅、可以直接人手改嘅 preference 檔案（`USER.md`），永遠放喺 prompt 最前面
- 底下先係每個 agent 自己嘅可搜尋 archive（daily notes + SQLite index）
- Embedding 預設行本地，唔好預設將個人記憶送去雲端

點解唔係直接用 mem0 或者 Zep？因為 benchmark 已經唔可信：
同一個 system 由唔同人跑，可以相差幾十分；LoCoMo 上面近乎滿分嘅系統，
喺 MemoryArena 跌到 40-60%，仲輸畀一個“將全部 context 塞入 prompt”嘅 baseline。
對一個單一用戶、資料量有限嘅助理嚟講，**記憶系統嘅真正價值係“可管理”**——
睇得到、改得到、刪得走、仲有硬上限——而唔係 recall 分數高。

另外三個重點：

- **Prompt 擺法就係成本架構。** System prompt、tools、`USER.md` 放最前不變，
  動態內容放最後。咁 cache 先會 hit。MiniMax M3 每次 replay 20k token 前綴
  每日約 US$0.12，唔 hit 就係 US$0.60；Kimi K3 同一個前綴貴十倍。
- **Scope 係檢索條件，唔係分開嘅資料庫。** 一個 store、一個 filter column，
  多個 scope。ChatGPT Projects 同 Claude Projects 都係咁做。
- **Preferences 同 memories 係唔同嘅嘢。** 用 `<!-- observed: DATE | status: active -->`
  格式寫成祈使句，改用時原地 supersede，唔好 append。
  否則模型會繼續用舊嗰個值答你。

## Status

Research complete. Sources verified against first-party documentation on
2026-10-21. Prices and version-specific behaviour should be re-checked before a
budget or a deployment decision is committed.
