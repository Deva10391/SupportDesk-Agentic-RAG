import os
import psycopg
from qdrant_client import QdrantClient
from .embed import embed
from .pii import mask

COLLECTION = "faq"
_q = None


def kb_search(query: str, k: int = 3) -> list[str]:
    global _q
    _q = _q or QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    hits = _q.query_points(COLLECTION, query=embed([query])[0], limit=k).points
    return [h.payload["text"] for h in hits]


def order_lookup(order_id: str) -> str:
    dsn = os.getenv("READ_DSN", "postgresql://reader:reader@localhost:5432/support")
    with psycopg.connect(dsn) as conn:  # read-only role, parameterized query
        row = conn.execute(
            "SELECT order_id, status, item, total, eta, customer_name, customer_email "
            "FROM orders WHERE order_id = %s", (order_id,)).fetchone()
    if not row:
        return ""
    oid, status, item, total, eta, _name, _email = row  # PII never leaves this function
    return mask(f"Order {oid}: item={item}, status={status}, total={total}, eta={eta}")
