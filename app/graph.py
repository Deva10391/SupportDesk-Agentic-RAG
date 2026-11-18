import logging, os, re, time
from typing import TypedDict
from langgraph.graph import StateGraph, END
from .llm import chat, chat_json
from .pii import mask
from .schemas import Ticket
from .tools import kb_search, order_lookup

log = logging.getLogger("supportdesk")
ORDER_ID = re.compile(r"ORD-\d+", re.I)


class S(TypedDict, total=False):
    query: str
    route: str
    context: str
    answer: str
    score: float
    threshold: float
    ticket: Ticket | None


def route_node(s: S) -> S:
    r = chat_json(
        'Classify a support query as "kb" (policy/how-to), "order" (needs an order lookup '
        'with an ORD- id) or "escalate" (complaint, legal, human requested). '
        'Reply only JSON: {"route": "..."}', s["query"]).get("route", "escalate")
    if r == "order" and not ORDER_ID.search(s["query"]):
        r = "escalate"
    return {"route": r if r in ("kb", "order") else "escalate"}


def kb_node(s: S) -> S:
    return {"context": "\n".join(kb_search(s["query"]))}


def order_node(s: S) -> S:
    return {"context": order_lookup(ORDER_ID.search(s["query"]).group(0).upper())}


def draft_node(s: S) -> S:
    if not s.get("context"):
        return {"answer": "", "score": 0.0}
    a = chat("Answer the question using ONLY the context. If it is missing, say you don't know. "
             "Be brief.", f"Context:\n{s['context']}\n\nQuestion: {s['query']}")
    return {"answer": a}


def guard_node(s: S) -> S:
    if not s.get("answer"):
        return {"score": 0.0}
    j = chat_json('Rate from 0 to 1 how fully every claim in the answer is supported by the '
                  'context. Reply only JSON: {"score": 0.0}',
                  f"Context:\n{s['context']}\n\nAnswer:\n{s['answer']}")
    return {"score": float(j.get("score", 0.0))}


def escalate_node(s: S) -> S:
    reason = "routed to human" if s["route"] == "escalate" else "ungrounded answer blocked"
    return {"ticket": Ticket(query=mask(s["query"]), route=s["route"], reason=reason),
            "answer": ""}


def after_route(s: S) -> str:
    return s["route"]


def after_guard(s: S) -> str:
    return "ok" if s["score"] >= s["threshold"] else "block"


g = StateGraph(S)
for n, f in [("route", route_node), ("kb", kb_node), ("order", order_node), ("draft", draft_node),
             ("guard", guard_node), ("escalate", escalate_node)]:
    g.add_node(n, f)
g.set_entry_point("route")
g.add_conditional_edges("route", after_route, {"kb": "kb", "order": "order", "escalate": "escalate"})
g.add_edge("kb", "draft")
g.add_edge("order", "draft")
g.add_edge("draft", "guard")
g.add_conditional_edges("guard", after_guard, {"ok": END, "block": "escalate"})
g.add_edge("escalate", END)
app_graph = g.compile()


def run(query: str, threshold: float | None = None) -> dict:
    t = time.perf_counter()
    th = float(os.getenv("GUARD_THRESHOLD", "0.7")) if threshold is None else threshold
    out = app_graph.invoke({"query": query, "threshold": th})
    out["latency_s"] = round(time.perf_counter() - t, 2)
    log.info("route=%s score=%s latency=%s q=%s", out.get("route"), out.get("score"),
             out["latency_s"], mask(query))
    return out
