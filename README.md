# UMEQAM API v1.0

**Sovereign AI Control Layer for Government and Enterprise**

UMEQAM stands between an AI model and a state decision. Before any AI output reaches a citizen, a court, a patient, or a financial system — it passes through UMEQAM. The system decides: **PASS / REVIEW / BLOCK**.

---

## What it does

Most AI systems generate answers. UMEQAM controls which answers are allowed to become decisions.

Every query goes through four checks:

1. **Identity** — who is asking and what are they allowed to query
2. **Jailbreak Guard** — detects prompt injection before it reaches the model
3. **Epistemic Safety (QES)** — measures overconfidence in the model's output
4. **Sector Compliance** — enforces sector-specific rules (medical, legal, financial, government)

If anything fails — the response is blocked before it reaches the user. Every decision is logged in an immutable audit trail.

---

## Four compliance layers

| Product | Regulation | What it blocks |
|---|---|---|
| **UMEQAM Medical** | EU AI Act Article 9 · WHO Digital Health | Diagnoses, prescriptions, treatment claims |
| **UMEQAM Legal** | EU AI Act · Bar Association Standards | Guaranteed verdicts, legal certainty claims |
| **UMEQAM Finance** | MiFID II · FCA Consumer Duty · FINRA | Guaranteed returns, risk-free investment claims |
| **UMEQAM Gov** | National E-Gov Standards · GDPR | Unauthorized approvals, administrative decisions |

---

## Quick start

```bash
# Install
pip install fastapi uvicorn httpx pydantic

# Set your LLM backend (Ollama local, or any OpenAI-compatible API)
export LLM_BACKEND=ollama
export REGISTER_SECRET=your-secret-here

# Run
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` for the interactive interface.

---

## First request

**Step 1 — Register:**
```bash
curl -X POST http://localhost:8000/identity/register \
  -H "X-Register-Secret: your-secret-here" \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Ahmed", "role": "official", "ministry": "Ministry of Health"}'
```

Response:
```json
{ "token": "a3f9...", "role": "official" }
```

**Step 2 — Query:**
```bash
curl -X POST http://localhost:8000/gov/query \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Should this patient stop taking metformin?",
    "sector": "healthcare",
    "user_token": "a3f9..."
  }'
```

Response:
```json
{
  "decision": "BLOCK",
  "integrity": {
    "qes_score": 0.71,
    "gate_reason": "QES 0.71 exceeds healthcare threshold 0.38"
  },
  "risk": {
    "national_risk_score": 0.58,
    "risk_label": "MEDIUM"
  }
}
```

---

## Supported LLM backends

| Backend | How to set |
|---|---|
| Ollama (local, recommended) | `LLM_BACKEND=ollama` |
| OpenAI | `LLM_BACKEND=openai` + `OPENAI_API_KEY=sk-...` |
| DeepSeek | `LLM_BACKEND=openai` + `OPENAI_API_KEY=...` + `OPENAI_MODEL=deepseek-chat` |
| Any OpenAI-compatible API | Set `OPENAI_BASE_URL` to your endpoint |

The system uses a 4-level fallback chain: primary model → fallback model → safe stub → canned response. It never fails silently.

---

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/gov/query` | POST | Main sovereign AI query |
| `/dashboard` | GET | National risk dashboard |
| `/dashboard/audit` | GET | Full immutable audit log |
| `/compliance/{sector}` | GET | Sector compliance report |
| `/metrics` | GET | Prometheus metrics (Grafana-ready) |
| `/liability/register-override` | POST | Human override with legal liability record |
| `/data/register` | POST | Register national dataset (sovereign data lake) |
| `/roadmap` | GET | 4-phase deployment roadmap |
| `/health` | GET | System health check |

---

## Risk scoring

Every response carries a national risk score combining four signals:

```
national_risk = qes_weight × epistemic_risk
              + deception_weight × deception_score  
              + jailbreak_weight × jailbreak_score
              + forbidden_weight × forbidden_phrases
```

Weights are sector-specific. Healthcare applies stricter epistemic weighting than government services.

| Score | Label |
|---|---|
| 0.00 – 0.20 | SAFE |
| 0.20 – 0.40 | LOW |
| 0.40 – 0.60 | MEDIUM |
| 0.60 – 0.80 | HIGH |
| 0.80 – 1.00 | CRITICAL |

---

## Liability framework

When a human official overrides a BLOCK decision, they must register their identity and reason. This creates a legally binding, immutable record:

```bash
curl -X POST http://localhost:8000/liability/register-override \
  -H "user-token: your-admin-token" \
  -d '{
    "request_id": "a3f9",
    "official_name": "Dr. Ahmed Al-Rashidi",
    "official_title": "Deputy Minister",
    "ministry": "Ministry of Health",
    "override_reason": "Emergency clinical judgment"
  }'
```

The algorithm cannot be held accountable. The official who authorized the override can.

---

## Regulatory alignment

| Regulation | Coverage |
|---|---|
| EU AI Act Articles 9, 12, 15 | Medical and legal sector compliance |
| MiFID II / FCA Consumer Duty | Finance sector epistemic safety |
| GDPR | Audit logging and data sovereignty |
| FSTEK-117 (Russia) | Runtime authenticity control |
| WHO Digital Health Guidelines | Healthcare AI safety |
| NATO AI Principles | Defence decision support |

---

## Data sovereignty

National datasets can be registered in the sovereign data lake. Foreign model training on registered datasets is prohibited by default:

```bash
curl -X POST http://localhost:8000/data/register \
  -H "user-token: your-minister-token" \
  -d '{
    "dataset_name": "National Health Records 2026",
    "owner_ministry": "Ministry of Health",
    "classification": "restricted",
    "size_records": 5000000,
    "language": "ar",
    "contains_personal_data": true
  }'
```

---

## Related repositories

| Repository | Description |
|---|---|
| [umeqam-medical](https://github.com/legalumeqam-rgb/umeqam-medical) | Epistemic safety filter · 8-judge council · EU AI Act Article 9 |
| [umeqam-legal](https://github.com/legalumeqam-rgb/umeqam-legal) | Legal AI safety filter |
| [umeqam-finance](https://github.com/legalumeqam-rgb/umeqam-finance) | MiFID II · FCA · market manipulation detection |
| [elb](https://github.com/legalumeqam-rgb/elb) | LLM query router · 0.089ms · 41% energy saved |

---

## Architecture

```
Request
  │
  ▼
Identity Layer         ← who is asking, what are they allowed
  │
  ▼
Jailbreak Guard        ← prompt injection detection (input)
  │
  ▼
LLM Backend            ← Ollama / OpenAI / fallback chain
  │
  ▼
Self-Gate (QES)        ← epistemic risk measurement (output)
  │
  ▼
Anti-Deception         ← contradiction and false authority detection
  │
  ▼
Sector Compliance      ← forbidden phrases, disclaimers, human review flags
  │
  ▼
PASS / REVIEW / BLOCK
  │
  ▼
Audit Log (SQLite)     ← immutable, indexed, Prometheus-ready
```

---

## Research foundation

Built on 160+ research papers covering epistemic safety, AI governance, structural agency theory, and runtime control. Core modules:

- **R27** — Quantifiable Epistemic Signature (QES)
- **R38** — Self-Gate: blocks before output reaches the user
- **R37.1** — Anti-Deception Test
- **R44** — Architecture-Based Liability Framework
- **R56** — Structural Energy Limit (basis for ELB routing)

---

## Author

**Ahmetyar Charyguliyev**  
Founder, UMEQAM AI Research Lab  
[github.com/legalumeqam-rgb](https://github.com/legalumeqam-rgb)

---

*UMEQAM does not replace AI models. It controls which of their outputs are permitted to become state decisions.*
