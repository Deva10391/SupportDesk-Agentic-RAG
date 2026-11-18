from fastapi import FastAPI
from .graph import run
from .pii import mask
from .schemas import QueryIn, QueryOut

app = FastAPI(title="SupportDesk Agentic RAG")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/query", response_model=QueryOut)
def query(body: QueryIn):
    o = run(mask(body.query))  # PII masked before any prompt or log
    return QueryOut(answer=o.get("answer") or None, route=o["route"],
                    grounded_score=o.get("score"), ticket=o.get("ticket"),
                    latency_s=o["latency_s"])
