from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import contracts as svc

class ContractIn(BaseModel):
    name: str = Field(min_length=2)
    counterparty: str = ""
    body: str = Field(min_length=40)

class AskIn(BaseModel):
    question: str = Field(min_length=3)

router = APIRouter()

@router.get("/contracts")
async def list_contracts(db: AsyncSession = Depends(get_db)):
    rows = await svc.list_contracts(db)
    return {"contracts": [{"id": c.id, "name": c.name, "counterparty": c.counterparty} for c in rows]}

@router.post("/contracts")
async def create(payload: ContractIn, db: AsyncSession = Depends(get_db)):
    return await svc.ingest(db, payload.name, payload.body, payload.counterparty)

@router.get("/clauses")
async def clauses(
    contract_id: str | None = None,
    risk_tag: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    rows = await svc.list_clauses(db, contract_id=contract_id, risk_tag=risk_tag)
    return {
        "clauses": [
            {
                "id": c.id,
                "contract_id": c.contract_id,
                "heading": c.heading,
                "risk_tag": c.risk_tag,
                "risk_score": c.risk_score,
                "text": c.text[:280],
            }
            for c in rows
        ]
    }

@router.get("/search")
async def search(q: str = Query(min_length=2), db: AsyncSession = Depends(get_db)):
    hits = await svc.search(db, q)
    return {"hits": [{"id": h.chunk_id, "title": h.title, "score": h.score, "text": h.text[:200]} for h in hits]}

@router.post("/ask")
async def ask(payload: AskIn, db: AsyncSession = Depends(get_db)):
    return await svc.ask(db, payload.question)
