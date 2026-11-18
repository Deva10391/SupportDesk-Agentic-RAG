"""Seeds 36 FAQ docs -> Qdrant, 200 fake orders -> Postgres, 50 labelled queries -> JSON."""
import json, os, random
import psycopg
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from app.embed import DIM, embed

random.seed(7)
TIERS = {"Standard": (30, 5, 7), "Premium": (60, 3, 3), "Business": (90, 2, 1)}  # return days, refund days, ship days
TOPICS = {
    "returns": "{t} plan: items can be returned within {r} days of delivery.",
    "refunds": "{t} plan: refunds reach your account within {f} business days of approval.",
    "shipping": "{t} plan: orders ship within {s} business days.",
    "cancellation": "{t} plan: an order can be cancelled before it ships, from the Orders page.",
    "warranty": "{t} plan: hardware carries a {r}-day replacement warranty.",
    "password": "{t} plan: reset your password via Settings > Security > Reset password.",
    "invoice": "{t} plan: invoices are emailed after shipment and listed under Billing.",
    "address": "{t} plan: the delivery address can be changed until the order ships.",
    "damaged": "{t} plan: report damaged items within 7 days with a photo to get a replacement.",
    "payment": "{t} plan: we accept cards, UPI and bank transfer.",
    "support": "{t} plan: support is available on chat, 9am-6pm on weekdays.",
    "gift": "{t} plan: gift cards never expire and cannot be refunded to cash.",
}
docs = [{"topic": k, "tier": t, "text": v.format(t=t, r=a, f=b, s=c)}
        for k, v in TOPICS.items() for t, (a, b, c) in TIERS.items()]

qc = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
if qc.collection_exists("faq"):
    qc.delete_collection("faq")
qc.create_collection("faq", vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))
vecs = embed([d["text"] for d in docs])
qc.upsert("faq", [PointStruct(id=i, vector=v, payload=d) for i, (v, d) in enumerate(zip(vecs, docs))])

STATUS = ["processing", "shipped", "delivered", "delayed"]
ITEMS = ["Laptop", "Headphones", "Keyboard", "Monitor", "Webcam", "Dock"]
with psycopg.connect(os.getenv("ADMIN_DSN", "postgresql://admin:admin@localhost:5432/support")) as c:
    c.execute("TRUNCATE orders")
    for i in range(1, 201):
        c.execute("INSERT INTO orders VALUES (%s,%s,%s,%s,CURRENT_DATE + %s,%s,%s)",
                  (f"ORD-{1000+i}", random.choice(STATUS), random.choice(ITEMS),
                   round(random.uniform(20, 900), 2), random.randint(-5, 10),
                   f"Customer {i}", f"user{i}@example.com"))

kb = [(f"What is the {k} policy on the {t} plan?", "kb") for k in TOPICS for t in ["Standard", "Premium"]]
kb += [("How do I reset my password?", "kb"), ("Which payment methods do you accept?", "kb"),
       ("When is chat support open?", "kb"), ("Do gift cards expire?", "kb")]
orders = [(f"Where is order ORD-{1000+random.randint(1,200)}?", "order") for _ in range(20)]
esc = [(q, "escalate") for q in [
    "I want to speak to a human right now", "Your service is a scam, I am calling my lawyer",
    "Where is my order?", "Delete all my account data and confirm by phone",
    "I was charged twice and nobody replies", "Transfer me to a manager",
    "This is the third time my package is lost", "I will sue over this broken laptop",
    "Cancel my order and compensate me", "Report a data breach on my account"]]
json.dump([{"query": q, "label": l} for q, l in kb[:20] + orders + esc],
          open("data/test_queries.json", "w"), indent=1)
print("seeded:", len(docs), "docs, 200 orders, 50 queries")
