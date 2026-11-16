# Yassine Elkhattam

Targeting Summer 2027 internships in quantitative finance and analytics.
DU Management des Organisations (DGCI / Université de Poitiers, Cairo) and Ain Shams University, Faculty of Commerce. Expected graduation 2028.
Deep tech research intern at ARIA Ventures (agriculture & synthetic biology).

I build things where the hard part is **measuring whether they actually work** — and I keep the
receipts, including when the answer is "no". Below is what I have been working on, what is actually
finished, and what is still in progress.

---

## Where the work stands

| Project | Domain | Status |
|---|---|---|
| [Janus Engine](#janus-engine--a-measurement-study-in-prediction-market-pricing) | Prediction-market measurement study | **Complete** — measured, then stopped |
| [NFL Big Data Bowl 2027](#nfl-big-data-bowl-2027--biomechanical-route-running-analytics) | Sports analytics | In progress — submission deadline 6 Jan 2027 |
| [Zeron Core](#zeron-core--portfolio-stress-testing-middleware) | FinTech middleware | v6.4.0, in progress |
| [PLE Agent Harness](#ple-agent-harness--engineering-agent-harness) | Engineering agent harness | In progress — competition closes 5 Jan 2027 |
| [Bermuth Vector](#bermuth-vector--guardrail-observability) | AI assurance / Insurtech | Phase 1 active — not a finance lane |
| [Eigenlog](#eigenlog--polyglot-epistemic-engine) | Personal knowledge tooling | v1 complete — not a finance lane |
| [Oubliette CLI](#oubliette-cli--paranoid-ai-coding-assistant) | Dev tooling / security | v1 complete — not a finance lane |

Everything below was verified by running the test suites from fresh clones — Janus 229 passing,
Zeron 21, NFL Big Data Bowl 70 — not by reading the project READMEs.

---

## Janus Engine — a measurement study in prediction-market pricing

> *"Does an LLM have an edge over the market price?"*
> **Answer: no usable edge in the markets scored — and the project stopped instead of pretending otherwise.**

A prediction-market bot built to answer one question honestly, with a signed jurisdictional
commitment that it would never go live without evidence. Paper-trading mode throughout; it never
traded live.

### The one idea everything is built on

In a prediction market **the price *is* the crowd's probability estimate**. A market quoting `$0.55`
says "the crowd thinks this resolves YES 55% of the time". So *"the model said 60%"* is **not** an edge —
it's a second opinion. An edge exists only if the disagreement is large enough to pay for being wrong:

```
p_model − ask  ≥  fee_per_share  +  margin
```

Every module is either machinery to make that comparison **honest**, or machinery to measure
**whether the gap is real**.

### The cycle, stage by stage

```
Gamma API (50 markets, volume-sorted)
   → [0] Zero-LLM pre-filter      deterministic gates, kills ~95% before any token is spent
   → [1] LLM pipeline (3 agents)  Research → Analysis → Validation (Groq primary, Gemini fallback)
   → [2] Reliability gate          has this market's probability been stable across repeated draws?
   → [3] THE EDGE GATE             p_model − ask ≥ fee + margin
   → [4] Order construction       15 named execution guards, FOK crossing, sizing
   → [5] Paper fill / CLOB         ledger + forward price log
   → [6] Settlement & breaker      realized P&L → daily loss breaker
   → Telegram per-cycle digest     every market, its fate, and why
```

**Stage 0 — Zero-LLM pre-filter.** Four deterministic gates, each with a stated economic reason:
`LOW_LIQUIDITY` (`volume_24h < 1000` — the ask you see is not the ask you get); `NON_BINARY`
(a two-team esports market has the same shape as a yes/no market but `token[0]` is *not* YES — trading
it buys the wrong outcome); `PRICE_OUT_OF_BAND` (buying `$0.999` risks `$10.00` to make `$0.01` — a
1000:1 payoff *against*, applied **per side** because the interesting side may be either);
`COARSE_TICK` (a limit can only be expressed on the market's price grid — `tick=0.001, p=0.0145`
→ 690 bps, reject; `tick=0.001, p=0.845` → 12 bps, ok). Measured pass rates at 50 bps were
**0/5, 2/10, 13/25, 29/50, 60/100** — which is exactly why `MARKET_FETCH_LIMIT=50` and not 5.

**Stage 1 — Three-agent LLM pipeline.** Each agent returns strict JSON: *Research* (facts, source
reliability, missing info) → *Analysis* (`predicted_probability_yes`, confidence, rationale) →
*Validation* (red-teams the analysis → `is_valid`, `risk_flags`, `final_recommendation`).
Provider order is Groq → Gemini, and Gemini models are *chained* so a single 503 can't kill the
fallback. The **800-token ceiling is load-bearing**: `gpt-oss` models emit ~90–135 *reasoning* tokens
per call that count against `max_tokens`; set it too low and the completion truncates mid-string,
the JSON fails to parse, and the old code silently substituted a fabricated `0.50`. The fabrication is
now detected and excluded rather than traded on.

**Stage 2 — Calibration ≠ reliability.** *Calibration* asks "is 70% right on average?" (correctable).
*Reliability* asks "**how much does the number move when you ask the same question twice?**" If a
market's draws straddle the edge hurdle, one draw passes and another rejects **on identical
information** — the gate decision is a coin flip, and no monotone transform fixes that. The engine
**fails closed**: no measurement → rejected (`NO_RELIABILITY_DATA`).

**Stage 3 — The edge gate, and why a lower bound is dangerous.** The gate rejects two ways:
`EDGE_TOO_SMALL` (gap < fee + margin) and `EDGE_IMPLAUSIBLE` (gap > `MAX_CLAIMED_EDGE` = 0.15).
The upper bound deserves its own paragraph: when a model is miscalibrated, its **largest** claimed
edges occur exactly where it is **most wrong**, so gating only on `gap ≥ hurdle` concentrates capital
on the model's biggest errors. Measured on a simulated overconfident model:
`corr(edge, overconfidence) = +0.93`, and gate-selected markets carried mean overconfidence of
**+0.18** versus **+0.02** for rejected ones. A **live-trading interlock** refuses to start with
`PAPER_TRADING_MODE=False` unless the edge gate is enabled *and* `MIN_EDGE_MARGIN > 0` — a calendar
date cannot authorise a strategy that has never had an economic filter.

**Stage 4 — Order construction (15 self-naming guards).**
`CIRCUIT_BREAKER` · `LLM_PASS` · `SIZE_CAP` · `CANARY_CAP` · `UNKNOWN_RECOMMENDATION` ·
`MISSING_TICK_SIZE` · `TICK_RATIO` · `NO_LIMIT_IN_BUDGET` · `SLIPPAGE_GUARD` · `NO_LIVE_ASK` ·
`LIMIT_DOES_NOT_CROSS` · `TOKEN_ID_UNRESOLVED` · `SIZE_CONVERSION` · `MIN_SIZE_EXCEEDS_MAX` ·
`MIN_SIZE_EXCEEDS_CANARY`. Two subtleties that cost real money:
- **The limit must cross the ask.** A FOK order priced below the ask is *killed*, not filled. The
  limit is derived from the **live best ask**, quantized *up* so it never lands below.
- **Order size is in SHARES, not USD.** The exchange error is literally `Size (5) lower than the
  minimum: 5` and live books show resting orders of 5 shares with sub-$1 notional — so the caps are
  re-checked after bumping to the minimum.

### The economics, in depth

```
fee = C · rate · p^exponent · (1 − p)        [USD, total]
```

| Quantity | Formula | Note |
|---|---|---|
| Total fee | `C · rate · p^exp · (1−p)` | Politics: `rate=0.04`, `exp=1`, taker-only |
| **Fee per share** | `rate · p^exp · (1−p)` | Dimensionless — the only form comparable to a probability gap |
| Fee as % of notional | `rate · p^(exp−1) · (1−p)` | Only for *notional* questions; **wrong** for the edge gate |

> Comparing the gap to the fee as a fraction of notional drops a factor of `ask` and is over-strict by
> exactly `1/ask` — **10× at p = 0.10**. This was the single most important dimensional-correctness
> fix in the codebase.

Three fee facts that are easy to get wrong: makers pay nothing under `takerOnly` (the `rebateRate` is
redistributed *to* makers; a taker receives none of it, and the separate Taker Rebate Program is
tiered by 30-day weighted volume and is **not backfilled**); the fee **vanishes at the price
extremes** because `p(1−p) → 0`, which is why holding to settlement pays no exit fee; and
`EXIT_MODE` changes the hurdle — `sell_to_book` doubles it, `hold_to_settle` doesn't.

### The quota math — why the cycle is 4 hours

The budget is a *token* budget, so it must be converted into a count of markets:

```
tokens_per_market = 3 calls × (800 + 500)          = 3,900
markets_per_cycle = 150,000 // (3,900 × 6 cycles)  = 6
```

That's the whole reason `CYCLE_INTERVAL_SECONDS = 14400`. At a 1 h cycle only **2** markets/cycle
fit, but 5–6 survive selection — most cycles would evaluate nothing. `max_llm_markets_per_cycle` is
allowed to be **0**: at a 5-minute cycle the arithmetic genuinely doesn't afford a single market, and
the engine says so rather than clamping to 1 and silently overspending. Groq's free tier enforces a
**200,000 tokens-per-day** ceiling (the 429 body literally reads *"Rate limit reached … on tokens per
day (TPD): Limit 200000, Used 199645"*) — tokens, not requests, are the binding constraint.

### How "is there an edge?" was actually answered

**The first measurement, and why it was retracted.** An 88-market retrospective run produced:

| metric | value |
|---|---|
| corr(model probability, quoted price) | **+0.9995** |
| mean absolute deviation from price | 0.00076 |
| Brier score | 0.2397 (vs. base-rate baseline ≈ 0.054) |
| markets clearing a 0.015 edge hurdle | **1 of 88** |

The *shape* of that result is the finding: given a market and its price, the model returns the price.
It isn't overconfident — it has **no independent signal at all**, and noise is exactly the
population a lower-bound edge gate selects.

But the sample was the **wrong population**: median total volume was **$30** (dust markets that
production would never trade). The run was **retracted** and the harness gained `--min-volume`. The
production-like slice (volume ≥ $10k) contains 88 scorable markets and was **never scored** — the
daily token budget ran out first. That gap is recorded, not hidden.

**The calibration harness** (`scripts/calibrate.py`) has three design decisions that make the
measurement valid:
- **Retrospective, not prospective** — logging only gate-passing predictions samples where the model
  claimed an edge (~1/day, resolving weeks out), so a usable curve needs 100+ days.
- **The price comes from history** — scoring a resolved market with its *final* price (1.0 or 0.0)
  would leak the answer. The harness substitutes the price quoted at a fixed lookback (default 30
  days) before resolution, so the prompt is identical in form to production.
- **`--cutoff` is mandatory, never guessed** — markets that resolved before the model's training
  cutoff are excluded.

Outputs are a **calibration curve** ("does 70% mean 70%?"), a **Brier score** with a baseline
`base_rate·(1−base_rate)` and a **skill score** `1 − Brier/baseline` — because a bare Brier number
has no reference class (0.24 looks moderate, but with a 5.7% base rate the constant predictor scores 0.054).

**The rules A/B** (`--compare-rules`) asks: does adding the market's resolution criteria change the
decision *at the economic hurdle*? Measured as **paired decision flips**. An early n=3 run found one
shift 3.2× the hurdle — but `P(0 shifts in 3 draws) = 0.85³ = 0.61` under a 15% shift-rate
hypothesis, so **n=3 cannot conclude anything**; excluding a 15% effect at 95% confidence needs n ≥ 19.

**The stopping rule was pre-committed** (§9 of `PRE_LIVE_CHECKLIST.md`): stop and declare no edge
when the A/B reaches n=30 paired markets × k=5 draws *and* the flip rate is ≤ 2. The run was
quota-bound and reached ~18 markets (86 paired draws) with **6 flips across 5 markets** — *more* than
the ceiling, with n=30 never reached, so the rule did not fire cleanly. The decision to stop rested on
the stronger evidence (the echo finding means there is no independent signal for an A/B to amplify)
together with the signed jurisdiction commitment. **A larger A/B would not have changed the conclusion;
it would only have consumed quota to measure noise.**

### The honest result

> On the one population that was scored, `corr(p, price) = +0.9995` and Brier = 0.2397 against a
> baseline of ≈ 0.054 — a strongly negative skill score. On tradeable markets (n=4), mean |Δ| =
> **0.00675** (~0.7pp of disagreement with the market). The bot therefore **never went live** — a
> signed jurisdictional commitment, not a technical accident.

**This is a statement about the markets that were scored, not a proof that no edge exists.** The
production-like slice was never scored because the token budget ran out, and the tradeable sample was
n=4. What the study does establish is that the edge gate works as designed: it rejects an echoing
model rather than trading on it.

The README documents exactly what would have to change for a different answer: a model whose
probability is *calibrated* (Brier skill > 0), a *stable* number (reliability σ small enough that the
gate isn't a coin flip), and a gap large enough to clear `fee_per_share + margin` after the round trip.

### Engineering, operations, and security

- **Data model** — 5 SQLite tables: `trade_ledger`, `engine_state`, `forward_prices`, `predictions`
  (**one table, two consumers**: calibration *and* realized P&L), `market_reliability`.
- **Telegram surface** — `/start` `/status` `/pause` `/resume` `/shutdown` `/help`, plus a **per-cycle
  digest** listing *every* market scanned with a distinct, explainable outcome — `REJECTED_PREFILTER`,
  `SKIPPED_LLM_QUOTA`, `REJECTED_RELIABILITY`, `REJECTED_EDGE`, `NO_ASK`, `NO_TOKEN_ID`,
  `ABORTED_RISK`, `DUPLICATE`, `LLM_ERROR`, `LLM_INVALID`, `LLM_PASS`, `TRADE`, `NOT_TRADED`. The
  digest was specifically audited so that **nothing disappears silently**.
- **Deployment** — `scripts/deploy.py` → systemd unit + health check (active state + crash indicators).
- **Forward log** — a GitHub Actions workflow runs daily at 00:00 UTC, snapshots prices from the
  tracked-token registry, appends to `data/forward_log.json` and commits it back. *The repository
  becomes the database* — free, permanent, version-controlled history.
- **Secrets** — no credentials in the working tree, and the reachable git history is verified clean of
  credential material. Provider keys are supplied through the OS keyring and environment, never the
  repository.
- **Tests** — 229 tests, verified passing from a fresh clone.

---

## NFL Big Data Bowl 2027 — Biomechanical route-running analytics

**Kaggle University Track · competition deadline 6 January 2027 · in progress**

A test-driven, local-first analytics pipeline for 10 Hz NFL player-tracking data, built to surface
non-obvious linkages between tracking data and game performance through biomechanical route-running
metrics — **Plant Foot Deceleration** and **Elasticity**.

### The P0 correctness pass

The most important entry in `LOG.md` is the one that throws away earlier numbers:

> Numbers produced before this entry were not valid; the smoothing output was never consumed and the
> derivative assumed a fixed 0.1 s timestep.

What changed:
- `s` is now the **conditioned** signal (Savitzky-Golay 5/2); `s_raw` is retained for audit.
- `dt` is **derived from `t_sec`**; steps spanning more than 2 s are not trusted.
- Attempts without a deceleration above the **1.0 yd/s² noise floor are excluded, not zero-filled**.
- Elasticity ranks on `speed_delta` (exit − plant, yd/s); `retention_ratio` (clamped to 1.0) is
  **display only**.
- Unit and timestamp format are **inferred, validated and logged** by the loader.
- `TWENTY_YARD_SHUTTLE` is classified as AGILITY.
- Leaderboards require **≥ 10 attempts per group** and exactly one row per player.

### Engineering discipline

- **Pinned dependencies with a stated reason** — `pandas==2.3.3`, `numpy==2.3.5`, `scipy==1.16.3`,
  `matplotlib==3.10.7`, `seaborn>=0.13.2,<0.14` — because the whole analysis is a derivative of
  floating-point orders of magnitude, and a silent patch-level drift invalidates prior numbers.
- **Synthetic fixtures** for clean-clone reproducibility and regression guards; the test suite is
  fixture-based so it runs with no raw data present.
- **Tests** — 70 tests, verified passing from a fresh clone.
- Entry points take `--data-dir` / `--speed-unit` / `--top`; `src/` is packaged (`pyproject.toml`,
  v0.2.0) with a source distribution.
- `SOE` (**Separation Over Expected**) baseline, drill-categorization config, Sunday-linkage and
  film-strip export scripts, and a standalone `validate_rankings.py` auditor.

### `KNOWN_LIMITATIONS.md` — a deliberate, documented trade-off list

1. **The leaderboard is ordinal, not cardinal** — a max-of-finite-difference over ~20–40 samples is
   an extreme-value statistic, suitable for *ranking* within a drill but not a calibrated physical
   measurement; must not be reported to three decimals or compared across drills.
2. **Nyquist limit** — 10 Hz gives a 5 Hz detectable ceiling; anything above is aliased, not measured.
   Savitzky-Golay suppresses GPS noise but also attenuates the sharpest real transients.
3. **Shoulder-pad tracking is a centre-of-mass proxy** — rotational variance is unmodelled.
4. **The physical ceilings are artefact guards, not physiology** — speed > 12 yd/s is treated as
   missing and interpolated; deceleration > 25 yd/s² is clipped and flagged.
5. **Speed-unit inference assumes spikes are rare** — if >1% of frames are spikes the loader raises
   `SchemaError` rather than guessing.
6. **No confidence intervals** — attempt-level maxima are reported without uncertainty, and repeat
   attempts are collapsed to the best one rather than modelled hierarchically.
7. **Small-sample baselines** — SOE is mean-centred by construction, so groups below
   `MIN_ATTEMPTS_PER_GROUP = 10` are excluded from leaderboards.

The document also lists engineering debt explicitly (no CI workflow, relative `data/raw/...` paths,
`print` instead of `logging`, deferred visualisation cleanup) and states plainly which results are
**not reproducible from the repository** because the raw CSVs are gitignored.

---

## Zeron Core — Portfolio stress-testing middleware

**v6.4.0 · in progress**

B2B quantitative analytics and scenario stress-testing middleware for Egyptian and frontier markets,
positioned as a **technology vendor** tool for brokerages, fund managers, and family offices.

- **Fail-closed quant engine** — strict validation of solver convergence, non-negativity, and
  full-investment constraints. Degenerate or non-converging inputs raise explicit errors rather than
  returning silent fallback weights. SLSQP-optimised portfolio weights under injected macro shocks,
  with invariant tests for weight sum/bounds, determinism, and degenerate-input fail-closed behaviour.
- **A README rewritten for truth** — the v6.1 commit message is explicit: *"Remove all false claims
  (no WORM, no HMM, no Ledoit-Wolf, no turnover slider). Document actual v6.1 capabilities."*
  Earlier drafts had claimed MCDR settlement constraints, HMM regime detection and a de-crowding
  jitter; because the code did not implement them, they were **cut from the README** rather than left
  in as aspirations. The repository description has since been corrected to match the code.
- **Tamper-evident append-only audit log** — every optimisation run persisted to PostgreSQL with
  SHA-256 hash chaining. **Database triggers block UPDATE/DELETE**; per-tenant advisory locks
  serialize concurrent inserts so the chain can't branch; the hash binds tenant, model version,
  scenario, dataset hash, and market inputs, so it is **reproducible externally**.
- **Localized macro shocks** — purpose-built operators for emerging-market dynamics: FX-hedge
  devaluation benefit and correlation decay under stress, with **Higham PSD repair** for numerical
  stability. Fixed along the way: incorrect `EGP=X` classification and non-deterministic audit hashing.
- **Auth & tenant isolation** — `X-API-Key` header validation, fail-closed. **The tenant ID is
  derived from the authenticated key, never the request body**, which prevents tenant spoofing.
  Per-tenant rate limiting.
- **Pluggable data architecture** — sandbox uses synthetic fixtures or public demo feeds;
  production integrates client-supplied licensed feeds via a `MarketDataProvider` protocol, with a
  content-based `dataset_hash` for provenance.
- **React + Chart.js dashboard** — baseline vs. stressed weights, interactive shock sliders, weight
  comparison tables.
- **Regulatory grounding** — `API_TERMS.md` establishes explicit *Technology Vendor* status: no
  financial advice, no portfolio management, no execution. Commercial deployments require the client
  to warrant its right to use the underlying data.
- **Tests** — 21 tests, verified passing from a fresh clone.

---

## PLE Agent Harness — Engineering agent harness

**In progress · Kaggle competition closes 5 January 2027 · no result claimed**

A harness for **PLE** (Physical-Engineering's Last Exam), Google's benchmark of long-horizon
engineering tasks. Each task runs in an isolated container with the project's drawings, specifications,
spreadsheets, solver scripts, and CAD/BIM or simulation tools; the agent must produce engineering
deliverables — code, calculations, models, schedules, and technical reports.

The benchmark is 85 expert-reviewed tasks across four disciplines (structural, civil, electrical,
mechanical), with a 29-task public development set, a uniform 6-hour agent time limit, and no internet
access beyond model API calls. Grading combines automated scripts for quantitative outputs with an
LLM judge on an expert rubric for open-ended work.

### What's built

- **`submission.yaml`** — model binding, `uv venv --python 3.12`, and a `serve.py` entrypoint that
  implements the official protocol (`type: done` / `type: error`).
- **`taskbridge.py`** — the IFC/BIM bridge: a **memory-mapped IFC parser** on the runtime path, plus
  a lazy CAD layer, document reader, and temp manager.
- **`harness.py`** — the agent loop, wired to the serve protocol so deliverables are actually produced.
- **`src/verifiers/ast_verifier.py`** — an AST verifier for unit coercion and registry alias
  handling, with dedicated unit tests.
- **`src/tools/isolated_runner.py`** — isolated process execution with **RSS monitoring** and
  error handling.
- **Telemetry**, an LLM client, and a profiler under `eval/`.

The last commit is a discipline fix worth naming: **"verify the declared deliverable exists before
finishing"** — the harness now checks its own output rather than assuming success.

---

## Also on GitHub

Not part of the finance lane, but real work.

### Bermuth Vector — Guardrail observability

**Phase 1 active**

A deep-tech SaaS and Insurtech platform solving the **"liability void"** of autonomous AI agents —
the gap where an agent causes a loss and nobody can prove the guardrails were live. The premise is
explicit: *"We do not build magical real-time LLM mind-readers; we build a cryptographically verified
guardrail observability platform that evolves into a specialized Managing General Agent (MGA)."*

**The four non-negotiable directives**

1. **Liability isolation (client-side halt)** — Bermuth provides observability and guardrail
   *recommendations*; the **client's** infrastructure retains final execution authority. This
   eliminates vendor-side business-interruption liability.
2. **Feasible cryptography** — attest to the **integrity of the guardrail configuration and
   API-gateway constraints**, not to the real-time, token-by-token LLM state. Claiming more would be
   unfalsifiable.
3. **Dynamic posture underwriting** — underwrite the robustness of the client's *deterministic
   guardrail architecture*, not the non-stationary probabilistic output of an LLM.
4. **Strict risk segmentation** — risk tranches segmented by foundation-model provider to prevent
   correlated ruin.

**Built (Rust / Axum)**

- **Anthropic ↔ OpenAI protocol translation** — SSE and JSON response translation, plus Claude
  `tool_use` blocks → OpenAI `tool_calls` frames.
- **Cryptographic attestation** — a **Merkle chain** over the guardrail policy state, so "the
  guardrails were active and unaltered" is independently verifiable.
- **SQLite persistence** with a non-blocking event queue and durable attestation.
- **Dynamic per-policy tool allowlist** with a **dual-schema** guardrail model.
- **Header sanitization** (with unit tests), **execution velocity tracking**, **rolling error rate**
  computed over a DB-backed sliding window, and **lightweight model extraction**.
- **Graceful shutdown + breach backpressure** so a flood of violations can't exhaust memory.
- `demo.sh` for a live end-to-end proxy demo; CI runs on `--all-targets` with a **fail-loud**
  `BERMUTH_API_KEY` startup check.

A 36-month plan covers SaaS and observability, MGA partnership, parametric underwriting, and
capital-markets tranches, with the commercial model documented in the repository's `MASTER_PLAN.md`.

### Eigenlog — Polyglot epistemic engine

**v1 complete · public**

> *Eigenlog, from the German **eigen** ("own"): a map of my own categories.*
> *"It will not tell me why we exist. It is meant to help me navigate."*

A local, private reflection tool in Python, SQL, and Bash that records what I know, what I doubt, and
what does not fit. Twenty-nine of its forty commits landed in a single day — a deep vertical sprint.

The design problem it solves: an AI critic can easily turn reflection into a *performance*, or atrophy
unassisted thinking. So the tool enforces deliberate guardrails:

- **Epistemic tagging** — `[Subjective Truth]` (axiomatic feelings shielded from logical
  deconstruction) vs `[Hypothesis]` (subject to rigorous dialectical friction), with **prompt
  category gating** and strict Socratic constraints.
- **Heat Dial** — from gentle grammar-and-coherence review up to forensic adversarial challenge.
  **Heat Level 0 (Cold Mode)** is a dedicated mode for raw, unchallenged logging with a local
  grammar/logic/open-unknown checker, preserving the baseline of unassisted thought.
- **Semantic Delta** — logging a subject you've recorded before surfaces your last entry and asks how
  your understanding has evolved, tracking dynamic progression instead of static categorization.
- **7-macro-category taxonomy** with delta tracking and frictionless micro-logging.
- **Multilingual by design** — explicit support for English, Arabic, French, German, and Spanish, in
  both the dialogue system prompt and the response instructions.
- **Local LLM integration** — a local model via llama-server with a **configurable model path**, bound
  strictly to **127.0.0.1** so there is no external network exposure, and stateful multi-turn dialogue
  with **explicit context-truncation warnings**.

**Data sovereignty** — SQLite storage with a Pydantic `LogEntry` schema, every row validated on read
and write so columns cannot silently drift; legacy `log.csv` files are auto-imported on first run;
the database and config are written **`0o600`** and gitignored, so a clone never carries anyone's
entries; direct SQL access is supported. A NiceGUI glass-morphism web UI (localhost-only) replaced an
earlier Flask app.

### Oubliette CLI — Paranoid AI coding assistant

**v1 complete · public · Apache 2.0**

> *An oubliette is a secret dungeon with access only through a trapdoor.*
> ***Secrets go in. Nothing leaks out.***

A local-first AI coding assistant with hard secret boundaries and audit-grade logging.

**Six security invariants**

1. **No cloud endpoints** — localhost only.
2. **No telemetry** — zero phone-home.
3. **Hard secret blocking** — a *non-configurable* blocklist: names (`.env`, `.env.local`,
   `git/config`, `credentials`, `service_account.json`), suffixes (`.pem`, `.key`, `.p12`, `.pfx`,
   `.jks`, `.keystore`), prefixes (`id_rsa`, `id_ed25519`, `id_ecdsa`, `id_dsa`) and substrings
   (`credentials`, `service_account`, `private_key`, `secret_key`).
4. **Regex-only redaction** — AWS `AKIA…` keys, GitHub tokens (`ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_`),
   Stripe `sk_live_`/`sk_test_`, generic `sk-…`, Slack `xoxb-`, and PEM private-key blocks. The AWS
   secret pattern uses boundary lookarounds so it matches a **40-char** key without destroying longer
   Base64 blobs or UUIDs.
5. **Metadata-only audit log** — the audit record stores the action, path, redaction count and a
   **SHA-256 hash of the prompt**, never the raw text. The log rotates at 10 MB, keeping the newest half.
6. **Strict permissions** — directory `0o700`, log `0o600`.

**Architecture** — a gate layer with **path traversal explicitly blocked**; the metadata-only audit
logger; dual LLM routers (a native **llama.cpp subprocess runner** and an **Ollama router** with
streaming); an atomic file writer with diff preview, code-fence stripping, and a warning before
writing `[REDACTED]` placeholders; lazy-start of llama-server with a configurable model path and ready
timeout; and a `run.sh` launcher that activates the venv itself and keeps one audit trail in a fixed
state directory regardless of the invoking directory.

---

## Cross-cutting themes

Looking back across this work, the same engineering instincts recur:

1. **Measurement before deployment.** Janus stopped because the data said there was no edge in the
   markets scored; Zeron ships a verifiable audit chain; NFL publishes its limitations before
   publishing its numbers.
2. **Negative results are deliverables.** The Janus README's most valuable section is the one that
   explains why the project ended. The retraction of the first 88-market measurement is documented
   rather than quietly replaced.
3. **Claims are cut when the code doesn't support them.** Zeron removed four advertised features from
   its README rather than leave them in as aspirations.
4. **Security as architecture, not as a feature.** Oubliette's six invariants, Eigenlog's `0o600`
   SQLite, Zeron's tenant isolation, and Bermuth's liability isolation are structural choices, not
   settings.
5. **Deterministic guards around probabilistic systems.** Decimal math in the invoice pipeline, the
   edge gate in Janus, AST verification in PLE, hash chaining in Zeron, and the Merkle chain in
   Bermuth all do the same thing: never let a probabilistic output into a critical path unverified.
6. **Cost and quota as architectural constraints.** Janus's 4-hour cycle is derived from a token
   budget, and the budget dictated the measurement plan, the stopping rule, and the conclusion.

---

## What I use

**Languages:** Python · Rust · TypeScript/JSX · SQL · Bash
**Backend & frameworks:** FastAPI · Axum · Pydantic · httpx · SQLite · PostgreSQL · Alembic
**Data & math:** Pandas · NumPy · SciPy · Savitzky-Golay filtering · SLSQP portfolio optimisation · Decimal arithmetic · SHA-256 hash chaining · Merkle trees · Higham PSD repair · Brier score & calibration curves · volatility & stress-testing operators
**AI/ML:** llama.cpp (GGUF) · Ollama · Groq · Gemini · agent pipelines with research/analysis/validation stages
**Frontend & web:** React · Chart.js · NiceGUI · Cloudflare Pages Functions
**Infrastructure:** Linux · systemd · Git · GitHub Actions · Docker · uv · pytest

**Domain:** Financial modelling and market research · Predictive-market microstructure · Regulatory/compliance research (Egypt/EU) · BIM/IFC engineering workflows

**Languages I work in:** English, French, Arabic (native). German and Spanish at intermediate level.

---

## Find me

[LinkedIn](https://linkedin.com/in/yassine-elkhattam) · GitHub [@ykhattam](https://github.com/ykhattam)
