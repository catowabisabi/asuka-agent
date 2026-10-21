# MEMORY

<!--
  Durable, non-profile facts: environment facts, conventions, decisions,
  lessons learned. Preferences and communication style belong in USER.md.

  Same entry contract as USER.md, plus two annotations that the platform
  stores as index columns and the model writes as trailing comments:

    <!-- trigger: a, b, c -->   phrases that make this entry worth injecting
    <!-- importance: 1-10 -->   how much this matters, used in ranking

  Importance is scored once, at write time, by a writer that already has a
  model in the loop. Ranking then needs no query-time model call.

  Trigger phrases drive automatic injection. Each inbound message runs a fast
  prefilter against them, and a strong match injects the entry as a compact
  hidden block. The prefilter is lexical and vector, so trigger phrases must
  be terms that actually appear in what the user writes. Under the trigram
  tokenizer, a trigger phrase needs at least three characters to match.
-->

<!-- observed: YYYY-MM-DD | status: active -->

- Accountant at a mid-sized audit firm in Central, three years in. <!-- trigger: 工作內容, 返工時間, 核數, audit --> <!-- importance: 9 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Peak season runs January to March, when month-end close and audit fieldwork overlap. <!-- trigger: 核數期, 加班時間, 趕報告, busy season --> <!-- importance: 7 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Commutes from Tin Hau to Central on the MTR, about thirty minutes each way. <!-- trigger: 返工車程, 地鐵時間, 通勤時間 --> <!-- importance: 6 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Yoga class on Monday, Wednesday and Friday at 07:00, a forty-five minute vinyasa flow in a Sheung Wan studio. <!-- trigger: 上瑜伽, 瑜伽課, yoga --> <!-- importance: 8 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Coffee order is a flat white with oat milk and no sugar. <!-- trigger: 飲咖啡, 咖啡訂單, coffee --> <!-- importance: 6 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Home is a one-bedroom flat in Tin Hau with a black cat named 阿黑. <!-- trigger: 返屋企, 貓仔, 阿黑 --> <!-- importance: 8 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Keeps one spreadsheet for monthly spending by category. <!-- trigger: 每月開支, 開支表, budget --> <!-- importance: 7 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Travels three or four times a year, usually in shoulder season, mostly Japan and South East Asia. <!-- trigger: 去旅行, 旅遊, trip --> <!-- importance: 8 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Prefers one carry-on bag and never checks luggage. <!-- trigger: 行李打包, 手提行李, packing --> <!-- importance: 6 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Keeps a paper travel journal with one page per trip. <!-- trigger: 旅行日誌, journal --> <!-- importance: 5 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Books a trip shortly after each payday. <!-- trigger: 出糧日, 訂行程, booking --> <!-- importance: 5 -->

<!-- observed: YYYY-MM-DD | status: active -->

- Went to Kyoto in April 2026 and to Chiang Mai in November 2025. <!-- trigger: 去過邊, 日本京都, 泰國清邁 --> <!-- importance: 6 -->
