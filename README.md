# Yassine Elkhattam

Student in Cairo, targeting Summer 2027 internships in quantitative research and technical strategy.
Dual degree in management sciences and international commerce, Ain Shams University and Université de Poitiers, expected 2028.
Deep tech research intern at ARIA Ventures.

I build things where the hard part is **measuring whether they actually work** — and I keep the
receipts. Below is a detailed account of every project I've shipped, what I actually built, and
— where it matters — what the measurements said when they contradicted me.

---

## Progress Overview

| Project | Domain | Stack | Status | Commits | LOC | Period |
|---|---|---|---|---|---|---|
| [Janus Engine](#1-janus-engine--polymarket-trading-bot) | Prediction-market trading | Python, SQLite, httpx, Telegram | **Complete** — measured, then honestly stopped | 42 | 11.3k | Nov 5–16, 2026 |
| [PLE Agent Harness](#6-ple-agent-harness--google-plebench-submission) | Engineering agent benchmark | Python, uv, Gemini API | Submitted | 16 | 3.7k | Nov 12–16, 2026 |
| [Bermuth Vector](#3-bermuth-vector--guardrail-observability) | AI assurance / Insurtech | Rust, Axum, SQLite | Phase 1 active | 13 | 3.0k | Nov 5–12, 2026 |
| [Qat Lab](#5-qat-lab--zero-trust-egyptian-invoice-processing) | Govtech / accounting | Python, llama.cpp, OCR, Cloudflare | Live pilot | 109 | 1.5k | Oct 30 – Nov 15, 2026 |
| [NFL Big Data Bowl 2027](#4-nfl-big-data-bowl-2027--biomechanical-route-running-analytics) | Sports analytics | Python, Pandas, SciPy | v0.2.0, in progress | 19 | 3.4k | Nov 1–12, 2026 |
| [Eigenlog](#7-eigenlog--polyglot-epistemic-engine) | Personal knowledge | Python, SQL, Bash, NiceGUI | v1 complete | 40 | 1.4k | Nov 5–10, 2026 |
| [Oubliette CLI](#8-oubliette-cli--paranoid-ai-coding-assistant) | Dev tooling / security | Python, llama.cpp, Ollama | v1 complete, public | 17 | 953 | Nov 5–7, 2026 |
| [Zeron Core](#2-zeron-core--quantitative-stress-testing-middleware) | FinTech middleware | Python, FastAPI, Postgres, React | v6.4.0 | 17 | 1.8k | Nov 2–12, 2026 |

**273 commits · ~27,100 lines of source · 320+ automated tests · 18 days (Oct 30 – Nov 16, 2026)**

Public: [Eigenlog](https://github.com/ykhattam/eigenlog) · [Oubliette CLI](https://github.com/ykhattam/oubliette-cli) · [Qat Lab](https://github.com/qatqat4x4/qat-lab)
Private: Janus Engine · Zeron Core · Bermuth Vector · NFL BDB 2027 · PLE Harness

---

## 1. Janus Engine — Polymarket trading bot

**`ykhattam/janus-engine`** · 42 commits · 11,323 LOC · 229 tests · Nov 5–16, 2026 · **Status: COMPLETE**

> *"Does an LLM have an edge over the market price?"*
> **Answer: no, or not enough to matter — and the project stopped instead of pretending otherwise.**

A prediction-market bot built to answer one question honestly, with a signed jurisdictional
commitment that it would never go live without evidence.

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

But the sample was the **wrong population**: median total volume was **$30** (MotoGP and corner-prop
dust that production would never trade). The run was **retracted** and the harness gained
`--min-volume`. The production-like slice (volume ≥ $10k) contains 88 scorable markets and was
**never scored** — the daily token budget ran out first. That gap is recorded, not hidden.

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

The README documents exactly what would have to change: a model whose probability is *calibrated*
(Brier skill > 0), a *stable* number (reliability σ small enough that the gate isn't a coin flip),
and a gap large enough to clear `fee_per_share + margin` after the round trip.

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
- **Security** — real keys were found in committed git history (`data/janus.log`) and purged with
  `git filter-branch`; console-side rotation of the Telegram token and Gemini key is owed
  independently of any journal scan. `httpx` keys were moved out of URLs, and fabricated calibration
  rows were quarantined.

---

## 2. Zeron Core — Quantitative stress-testing middleware

**`ykhattam/zeron-core`** · 17 commits · 1,786 LOC · 21 tests · Nov 2–12, 2026 · **v6.4.0**

B2B quantitative analytics and scenario stress-testing middleware for Egyptian and frontier markets,
positioned as a **technology vendor** tool for brokerages, fund managers, and family offices.

- **Fail-closed quant engine** — strict validation of solver convergence, non-negativity, and
  full-investment constraints. Degenerate or non-converging inputs raise explicit errors rather than
  returning silent fallback weights. SLSQP-optimised portfolio weights under injected macro shocks,
  with invariant tests for weight sum/bounds, determinism, and degenerate-input fail-closed behaviour.
- **A README rewritten for truth** — the v6.1 commit message is explicit: *"Remove all false claims
  (no WORM, no HMM, no Ledoit-Wolf, no turnover slider). Document actual v6.1 capabilities."*
  Earlier drafts had claimed MCDR settlement constraints, HMM regime detection and a
  de-crowding jitter; because the code did not implement them, they were **cut from the README**
  rather than left in as aspirations. (The repository *description* on GitHub still mentions HMM
  and MCDR — a description/README mismatch worth correcting.)
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

---

## 3. Bermuth Vector — Guardrail observability

**`ykhattam/bermuth-vector`** · 13 commits · 2,979 LOC (Rust) · Nov 5–12, 2026 · **Phase 1 active**

> *"We do not build magical real-time LLM mind-readers; we build a cryptographically verified
> guardrail observability platform that evolves into a specialized Managing General Agent (MGA)."*

A deep-tech SaaS and Insurtech platform solving the **"liability void"** of autonomous AI agents —
the gap where an agent causes a loss and nobody can prove the guardrails were live.

### The four non-negotiable directives

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

### What's built (Rust / Axum)

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

### The 36-month plan (`docs/MASTER_PLAN.md`)

| Phase | Window | Goal | Monetization |
|---|---|---|---|
| 1 — SaaS & observability | Months 0–12 | Telemetry, schema validation, Merkle proofs | $10k–15k/month per enterprise pilot |
| 2 — MGA partnership | Months 12–18 | Reinsurance capacity via proven telemetry | Premium participation |
| 3 — Parametric underwriting | Months 18–24 | Flip on liability coverage | Reduced SaaS fee + 15–20% commission |
| 4 — Capital markets | Months 24–36+ | ILS/CAT bond tranches, regulatory safe harbour | Standards-setting |

---

## 4. NFL Big Data Bowl 2027 — Biomechanical route-running analytics

**`ykhattam/nfl-bdb-2027`** · 19 commits · 3,407 LOC · 63 test functions (67 passed, 1 skipped) ·
Nov 1–12, 2026 · **v0.2.0**

A test-driven, local-first analytics pipeline for 10 Hz NFL player-tracking data, built for the
Kaggle University Track to surface hidden draft value through biomechanical route-running metrics —
**Plant Foot Deceleration** and **Elasticity**.

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
- Entry points take `--data-dir` / `--speed-unit` / `--top`; `src/` is packaged (`pyproject.toml`,
  v0.2.0) with a `py.typed`-style source distribution.
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

## 5. Qat Lab — Zero-Trust Egyptian invoice processing

**`qatqat4x4/qat-lab`** · 109 commits · 1,509 LOC · 28 test functions · Oct 30 – Nov 15, 2026 · **Live pilot**

An on-premises invoice extraction and validation service for Egyptian e-invoicing (ETA), designed
against **Law 151 of 2020** and its executive regulations (Decree 816 of 2025, issued 1 Nov 2025).

### Core guarantees

- **Zero persistence** — invoice data is processed in volatile memory only. No logs, no cloud
  storage, no telemetry. The OCR path renders PDF pages to 300 DPI PNGs inside a **tmpfs RAM disk**
  (`/dev/shm/qatlab`, mode `0o700`) and purges them afterwards, so extracted pixels never touch a
  physical disk.
- **On-premises processing** — no outbound internet access is required; the pipeline runs locally
  via llama.cpp. This *removes* the data-transfer licensing question rather than merely mitigating it.
- **Deterministic math** — LLM extraction is validated by **Decimal-based** audit guardrails with
  strict `ROUND_HALF_UP` and exact-equality checks. No floating-point errors.
- **Neuro-symbolic math auditor** — including Arabic text sanitization and ISO date validation.
- **Anti-injection guards** in the extraction prompt and pipeline wiring.
- **ETA-native JSON/XML priority**, with OCR (tesseract + poppler, CLAHE-enhanced renders) as a
  *tertiary* fallback.
- **Signed 90-day Alpha Pilot time-check** — enforces Clause 5 of the signed pilot waiver. The
  install timestamp is written to **redundant locations with the earliest winning**, so deleting one
  copy cannot reset the clock, and the stored record is **HMAC-SHA256 signed** so a hand-edited
  timestamp is detected.

### Security and operations

- **Pre-commit secret detection** and agent governance rules; a compromised Resend API key file was
  removed from the working tree.
- **Cloudflare Pages** site with a **Pages Function** at the repo root (Cloudflare resolves Functions
  from the project root, never the output dir) — the build command `bash bin/check-pages-functions.sh`
  **fails the deployment** if `functions/` is missing or empty.
- **The Function does not persist submissions** — it sends a team notification and a requester
  confirmation through Resend, storing nothing.
- Deployed at **www.qatlab.xyz** — live at [qatqat4x4/qat-lab](https://github.com/qatqat4x4/qat-lab).

### The decision record

The `project_blueprint/` directory holds a full technical and legal evaluation that changed the
product. Notable conclusions: Egypt's data-protection grace period ends 31 Oct / 1 Nov 2026 and
creates a licensing regime reaching foreign processors; **Law 194 of 2020, Article 206** bars
issuing, trading or promoting crypto without prior CBE approval (fines cited up to EGP 10M), so the
crypto workspaces and the Binance P2P feed were **removed from the MVP rather than flagged**; and
the six-month revenue target was demoted to a **ceiling** pending measurement.

---

## 6. PLE Agent Harness — Google PLEBench submission

**`ykhattam/ple-agent-harness`** · 16 commits · 3,701 LOC · Nov 12–16, 2026

A harness for **PLEBench** (Google's Process Learning Environment benchmark), whose dev set is **29
real engineering design tasks** — data-hall MEP routing, seismic diaphragm shear, LV cable sizing,
emergency spillway checks, foundation strategy, roof-deck design, landscape sheet revision, and more.
The benchmark — *"Physical-Engineering's Last Exam"* — runs each task in an **isolated Harbor
container** and grades the deliverables with automated checks, an expert rubric judged by Claude Opus,
or both. A model's score is its mean reward across the dev tasks.

### What's built

- **`submission.yaml`** — `model_api: google-cloud/gemini-3.8-flash`, `uv venv --python 3.12`, and a
  `serve.py` entrypoint that implements the official protocol (`type: done` / `type: error`).
- **`taskbridge.py` (1,528 lines)** — the IFC/BIM bridge: a **memory-mapped IFC parser** on the
  runtime path, plus a lazy CAD layer, document reader, and temp manager.
- **`harness.py` (834 lines)** — the agent loop, wired to the serve protocol so deliverables are
  actually produced.
- **`src/verifiers/ast_verifier.py`** — an AST verifier for unit coercion and registry alias
  handling, with dedicated unit tests.
- **`src/tools/isolated_runner.py`** — isolated process execution with **RSS monitoring** and
  error handling.
- **Telemetry**, an LLM client, and a profiler under `eval/`.

The final commit is a discipline fix worth naming: **"verify the declared deliverable exists before
finishing"** — the harness now checks its own output rather than assuming success.

---

## 7. Eigenlog — Polyglot epistemic engine

**`ykhattam/eigenlog`** (public) · 40 commits · 1,424 LOC · Nov 5–10, 2026

> *Eigenlog, from the German **eigen** ("own"): a map of my own categories.*
> *"It will not tell me why we exist. It is meant to help me navigate."*

A local, private reflection tool in Python, SQL, and Bash that records what I know, what I doubt, and
what does not fit. Twenty-nine of its forty commits landed in a single day (Nov 7) — a deep vertical sprint.

### The design problem it solves

An AI critic can easily turn reflection into a *performance*, or atrophy unassisted thinking. So the
tool enforces deliberate guardrails:

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
- **Local LLM integration** — a local model (Qwen 2.5 Coder via llama-server) with a **configurable
  model path**, bound strictly to **127.0.0.1** so there is no external network exposure, and
  stateful multi-turn dialogue with **explicit context-truncation warnings**.

### Data sovereignty

- **SQLite storage with a Pydantic `LogEntry` schema** — every row validated on read and write, so
  columns cannot silently drift. Legacy `log.csv` files are auto-imported on first run and renamed
  to `log.csv.migrated`.
- **`0o600` owner-only permissions** on the database and `.eigenlog_config`; both gitignored, so a
  clone never carries anyone's entries.
- **Direct SQL access** — `sqlite3 eigenlog.db "SELECT * FROM entries WHERE subject='emotions'"`.
- **Cold Mode precedence** over sensitive gating, and graceful Ctrl-C handling.
- A **NiceGUI glass-morphism web UI** (localhost-only) replaced an earlier Flask app, with form
  submission fixed, deletion added, and robust error handling.

The public README states the risk plainly: *"This tool logs highly sensitive, unfiltered personal
data. Ensure your disk is fully encrypted."* The code is public; the reflections stay mine.

---

## 8. Oubliette CLI — Paranoid AI coding assistant

**`ykhattam/oubliette-cli`** (public) · 17 commits · 953 LOC · 39 test functions · Nov 5–7, 2026

> *An oubliette is a secret dungeon with access only through a trapdoor.*
> ***Secrets go in. Nothing leaks out.***

A local-first AI coding assistant with hard secret boundaries and audit-grade logging. Apache 2.0.

### Six security invariants

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

### Architecture

- **Gate layer** — path resolution + regex redaction, with **path traversal explicitly blocked**
  (a fix that arrived after an audit pass).
- **Audit logger** — metadata-only, stable audit directory.
- **Dual LLM routers** — a native **llama.cpp subprocess runner** and an **Ollama router** with
  streaming.
- **Atomic file writer** with diff preview, code-fence stripping, and a warning before writing
  `[REDACTED]` placeholders.
- **Lazy-start** of llama-server, with a configurable model path and ready timeout.
- **`run.sh` launcher** that activates the venv itself, pins an absolute model path, and keeps one
  audit trail in a fixed state directory regardless of the invoking directory.

The README documents the environmental override surface (`OUBLIETTE_LLM_ENDPOINT`, `OUBLIETTE_MODEL_PATH`,
`OUBLIETTE_MODEL`, `OUBLIETTE_AUDIT_DIR`, `OUBLIETTE_READY_TIMEOUT`) and CLI arguments
(`--file`, `--prompt`, `--write`, `--no-approval`).

---

## Cross-cutting themes

Looking back across all eight projects, the same engineering instincts recur:

1. **Measurement before deployment.** Janus stopped because the data said there was no edge; Zeron
   ships a verifiable audit chain; NFL publishes its limitations before publishing its numbers.
2. **Negative results are deliverables.** The Janus README's most valuable section is the one that
   explains why the project ended. The retraction of the first 88-market measurement is documented
   rather than quietly replaced.
3. **Security as architecture, not as a feature.** Oubliette's six invariants, Eigenlog's `0o600`
   SQLite, Qat Lab's zero-persistence pipeline, Zeron's tenant isolation, and Bermuth's liability
   isolation are all structural choices, not settings.
4. **Deterministic guards around probabilistic systems.** Decimal math in Qat Lab, the edge gate in
   Janus, AST verification in PLE, hash chaining in Zeron, and the Merkle chain in Bermuth all do the
   same thing: never let a probabilistic output into a critical path unverified.
5. **Regulatory grounding.** Egypt's Law 151 and Article 206, the *Technology Vendor* disclaimer in
   Zeron's API terms, and the liability-isolation thesis in Bermuth are treated as design inputs,
   not afterthoughts.
6. **Cost and quota as architectural constraints.** Janus's 4-hour cycle is derived from a token
   budget, and the budget dictated the measurement plan, the stopping rule, and the conclusion.
7. **The repository as the database.** Janus commits its forward log back to itself through GitHub
   Actions; Zeron makes its audit chain queryable in SQL.

---

## What I use

**Languages:** Python · Rust · TypeScript/JSX · SQL · Bash
**Backend & frameworks:** FastAPI · Axum · Pydantic · httpx · SQLite · PostgreSQL · Alembic
**Data & math:** Pandas · NumPy · SciPy · Savitzky-Golay filtering · SLSQP portfolio optimisation · Decimal arithmetic · SHA-256 hash chaining · Merkle trees · Higham PSD repair · Brier score & calibration curves · volatility & stress-testing operators
**AI/ML:** llama.cpp (GGUF) · Ollama · Groq · Gemini · agent pipelines with research/analysis/validation stages
**Frontend & web:** React · Chart.js · NiceGUI · Cloudflare Pages Functions · Streamlit
**Infrastructure:** Linux · systemd · Git · GitHub Actions · Docker · uv · pytest · Playwright-ready CI

**Domain:** Financial modelling and market research · Predictive-market microstructure · Regulatory/compliance research (Egypt/EU) · BIM/IFC engineering workflows

**Languages I work in:** English, French, Arabic (native). German and Spanish at intermediate level.

---

## Find me

[LinkedIn](https://linkedin.com/in/yassine-elkhattam) · GitHub [@ykhattam](https://github.com/ykhattam)
