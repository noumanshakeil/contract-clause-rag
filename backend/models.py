from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base

def utcnow(): return datetime.utcnow()

class Contract(Base):
    __tablename__ = "contracts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    counterparty: Mapped[str] = mapped_column(String(160), default="")
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class Clause(Base):
    __tablename__ = "clauses"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    contract_id: Mapped[str] = mapped_column(String(32), index=True)
    heading: Mapped[str] = mapped_column(String(200), default="")
    text: Mapped[str] = mapped_column(Text)
    risk_tag: Mapped[str] = mapped_column(String(64), default="general", index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
