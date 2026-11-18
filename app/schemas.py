from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field


class QueryIn(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    query: str
    route: str
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QueryOut(BaseModel):
    answer: str | None
    route: str
    grounded_score: float | None
    ticket: Ticket | None
    latency_s: float
