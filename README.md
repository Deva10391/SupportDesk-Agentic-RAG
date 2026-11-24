# SupportDesk Agentic RAG

Question in → route → fetch (docs or order row) → check grounding → answer or ticket.

**Proof line:** On 50 labelled queries (local LLM): 94% routed correctly, 75% of answerable queries resolved without a human at guard threshold 0.7, 9 of 50 queries blocked as ungrounded, 10.3 s average latency.

**Requirements**
- Python 3.11+, Docker, Ollama with a model pulled (name goes in `.env`).
- 36 FAQ docs, ~200 fake orders, 50 labelled queries ("kb", "order", "escalate"), all made by `scripts/seed.py`.

**Open-source utilities**
- LangGraph (agent), Qdrant + fastembed `bge-small-en-v1.5` (vectors), PostgreSQL (orders).
- FastAPI + Pydantic (API, ticket schema), Ollama via the OpenAI client (LLM), pytest, Docker, GitHub Actions.

**Working amongst components**
- FastAPI `/query` masks PII, then the LangGraph router picks KB search, SQL order lookup or escalation.
- The draft node answers from the fetched context only.
- The guard node scores the answer against that context (0–1); below `GUARD_THRESHOLD` it is blocked.
- A blocked or escalated query becomes a Pydantic ticket.

**Details to know**
- Read-only DB role, parameterized SQL, customer name and email never leave `order_lookup`.
- Threshold is set from data: `scripts/eval.py` sweeps 0.5–0.9 on the 50 queries.
- Small local models return bad JSON sometimes; that falls back safely to escalate / score 0.
- Weak spot: 3 of 50 routes were wrong (2 order queries sent to a human, 1 escalation answered from KB).

| Threshold | Resolved w/o human | Answers blocked (of 50) |
|---|---|---|
| 0.5 | 77.5% | 8 |
| 0.6 | 75.0% | 9 |
| **0.7** | **75.0%** | **9** |
| 0.8 | 72.5% | 10 |
| 0.9 | 62.5% | 14 |

0.7 gives the same resolution as 0.6 with a stricter guard; 0.9 costs 12.5 points of resolution.

**Simplified working:** question in → route → fetch → check grounding → answer or ticket.

## Run
```bash
cp .env.example .env                         # set LLM_MODEL from `ollama list`, GUARD_THRESHOLD=0.7
mkdir data
docker compose up -d db qdrant
pip install -r requirements.txt
PYTHONPATH=. python scripts/seed.py
PYTHONPATH=. python scripts/eval.py          # prints the table
docker compose up --build api
curl -XPOST localhost:8000/query -H 'content-type: application/json' -d '{"query":"Where is order ORD-1005?"}'
PYTHONPATH=. pytest -q                       # PII masking tests (also run in CI)
```

## API
| Route | Does |
|---|---|
| `POST /query` | `{"query": "..."}` → answer, route, grounded_score, ticket, latency_s |
| `GET /health` | liveness |

## Safety
Read-only DB role, parameterized SQL, PII masked before prompts and logs, fake data only.

## When NOT to use an agent
Fixed, single-source lookups (one FAQ page, one SQL report) are cheaper, faster and more predictable as plain code. Here a KB answer costs about 11 s (three LLM calls). Use an agent only when routing between tools is genuinely needed.

## Limits
- `/query` does not return `tools`, `contexts` or `cost_usd` and does not read `x-api-key`, so AgentEval cannot gate this build until those are added.
- Latency is from a local CPU model; a hosted model would be faster.

## Files
`app/graph.py` router, draft, guard · `app/tools.py` KB and order tools · `app/pii.py` masking · `app/main.py` API · `scripts/seed.py` data · `scripts/eval.py` threshold sweep