# Yassine Elkhattam

Targeting Summer 2027 internships in quantitative finance and analytics.
DU Management des Organisations (DGCI / Université de Poitiers, Cairo) and Ain Shams University, Faculty of Commerce. Expected graduation 2028.
Deep tech research intern at ARIA Ventures (agriculture & synthetic biology).

I work on measurement problems — does this actually work, by how much, and what
happens if it doesn't. I keep the receipts, including when the answer is "no".

This page is an index. Each project has its own repository, with its own
documentation, its own access rules, and its own release state.

---

## Projects

| Project | What it is | State |
|---|---|---|
| **Janus Engine** | A prediction-market measurement study: whether an LLM has a tradeable edge over market prices after fees | **Complete** — measured, then stopped before going live |
| **NFL Big Data Bowl 2027** | Analytics pipeline for 10 Hz player-tracking data (Kaggle, University Track) | In progress — competition deadline 6 Jan 2027 |
| **Zeron Core** | B2B portfolio optimisation and scenario stress-testing middleware for Egyptian and frontier markets | v6.4.0 |
| **PLE Agent Harness** | Agent harness for a long-horizon engineering benchmark (Google) | In progress — competition closes 5 Jan 2027 |
| **Qat Lab** | On-premises invoice extraction for Egyptian e-invoicing | **Alpha pilot open** — [qatlab.xyz](https://www.qatlab.xyz) |

**Janus Engine.** A prediction-market bot built to answer one question honestly:
does a model disagreeing with the market price by enough to cover fees actually
constitute an edge? It measured calibration against a base-rate baseline,
applied a pre-committed stopping rule, and **found no usable edge in the
markets it scored** — so it stopped rather than trading. Paper-trading mode
throughout; it never went live. The interesting part is not the bot, it is the
discipline of writing the stopping rule down first.

**NFL Big Data Bowl 2027.** A test-driven, local-first pipeline over 10 Hz
player-tracking data, built to surface linkages that box-score statistics miss.
It ships with an explicit limitations document listing what the measurement
cannot support — ordinal-but-not-cardinal rankings, the sampling ceiling, and
the fact that shoulder-pad tracking is a centre-of-mass proxy.

**Zeron Core.** A FastAPI service for non-discretionary portfolio optimisation
under macro stress scenarios, with a tamper-evident hash-chained audit log for
compliance and tenant isolation derived from the authenticated key rather than
the request body. Its README is explicit about the features it does *not*
implement.

**PLE Agent Harness.** A harness for Google's Physical-Engineering's Last
Exam, a benchmark of long-horizon structural, civil, electrical and mechanical
engineering tasks with a 6-hour agent time limit and no internet access beyond
model calls. In progress for the Kaggle competition; **no result claimed.**

**Qat Lab.** On-premises invoice extraction for Egyptian e-invoicing (Law 151). Documents are
parsed in volatile memory inside the client's own network perimeter, verified by deterministic
decimal arithmetic, and exported as fixed-point ledgers. Alpha pilot open.

### Also on GitHub — not part of the finance lane

- **Bermuth Vector** — An AI assurance platform in Rust: observe, attest, and underwrite the
  guardrails that autonomous agents run inside. The thesis is that liability should attach to the
  client's *deterministic guardrail architecture* — attested with a Merkle chain, so "the
  guardrails were live and unaltered" is independently verifiable — rather than to the
  non-stationary output of an LLM. The client keeps the halt switch.
- **Eigenlog** *(public)* — a local-first epistemic logging tool in Python, SQL
  and Bash, with Pydantic-validated storage, owner-only permissions, and a
  local LLM critic.
- **Oubliette CLI** *(public, Apache 2.0)* — an audit-grade local AI coding
  assistant with a hard secret-blocklist, regex redaction, and metadata-only
  logging.

---

## How I work

- **Measure before deploying.** Ship the instrument before the conclusion.
- **Negative results are deliverables.** A retracted measurement is documented,
  not quietly replaced.
- **Cut claims the code doesn't support.** Zeron removed four advertised
  features from its README rather than leave them in as aspirations.
- **Security is architecture, not a setting.** Keyring-supplied secrets,
  owner-only files, hash-chained logs, tenant-scoped queries.
- **Cost and quota are design constraints.** Janus's cycle length is derived
  from a token budget, and that budget decided the measurement plan, the
  stopping rule, and the conclusion.

---

## Skills

**Tools** — Python (Pandas, NumPy, SciPy, FastAPI, Pydantic, pytest) · SQL (SQLite, PostgreSQL) ·
Rust · Git · Linux · Docker
**Analysis** — probability & statistics · financial modelling · market microstructure · calibration
and Brier-score analysis · scenario stress-testing · time-series smoothing
**AI/ML** — llama.cpp (GGUF) · Ollama · Groq · Gemini · multi-stage agent pipelines
**Languages** — English, French, Arabic (native) · German, Spanish (intermediate)

---

## Find me

[LinkedIn](https://linkedin.com/in/yassine-elkhattam) · GitHub [@ykhattam](https://github.com/ykhattam)
