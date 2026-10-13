"""Contract ingest, risk tagging, and clause search."""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.llm import get_llm
from backend.models import Clause, Contract
from backend.services.rag_core import Hit, chunk_text, pack_citations, score_chunk

RISK_PATTERNS = [
    ("indemnity", 0.85, re.compile(r"indemnif|hold harmless", re.I)),
    ("liability", 0.8, re.compile(r"limitation of liability|consequential damages", re.I)),
    ("termination", 0.65, re.compile(r"terminat|for convenience", re.I)),
    ("data", 0.75, re.compile(r"personal data|gdpr|ccpa|data processing", re.I)),
    ("ip", 0.7, re.compile(r"intellectual property|work product|assignment of", re.I)),
    ("auto_renew", 0.55, re.compile(r"auto(?:matic)? renew", re.I)),
]


def tag_clause(text: str) -> tuple[str, float]:
    best_tag, best = "general", 0.15
    for tag, score, rx in RISK_PATTERNS:
        if rx.search(text) and score > best:
            best_tag, best = tag, score
    return best_tag, best


async def ingest(session: AsyncSession, name: str, body: str, counterparty: str = "") -> dict:
    contract = Contract(
        id=uuid.uuid4().hex[:10],
        name=name.strip()[:200],
        counterparty=counterparty.strip()[:160],
        body=body.strip(),
    )
    session.add(contract)
    await session.flush()
    chunks = chunk_text(body, size=500, overlap=80)
    created = 0
    for piece in chunks:
        tag, score = tag_clause(piece)
        heading = piece.split(".")[0][:120]
        session.add(
            Clause(
                id=uuid.uuid4().hex[:12],
                contract_id=contract.id,
                heading=heading,
                text=piece,
                risk_tag=tag,
                risk_score=score,
            )
        )
        created += 1
    await session.commit()
    return {"contract_id": contract.id, "clauses": created}


async def list_contracts(session: AsyncSession) -> list[Contract]:
    return list((await session.execute(select(Contract).order_by(Contract.created_at.desc()))).scalars())


async def list_clauses(
    session: AsyncSession, *, contract_id: str | None = None, risk_tag: str | None = None
) -> list[Clause]:
    stmt = select(Clause)
    if contract_id:
        stmt = stmt.where(Clause.contract_id == contract_id)
    if risk_tag:
        stmt = stmt.where(Clause.risk_tag == risk_tag)
    stmt = stmt.order_by(Clause.risk_score.desc())
    return list((await session.execute(stmt)).scalars())


async def search(session: AsyncSession, query: str, *, k: int = 6) -> list[Hit]:
    clauses = list((await session.execute(select(Clause))).scalars())
    contracts = {c.id: c for c in (await session.execute(select(Contract))).scalars()}
    hits: list[Hit] = []
    for cl in clauses:
        s = score_chunk(query, cl.text) + cl.risk_score * 0.15
        if s <= 0:
            continue
        title = contracts.get(cl.contract_id).name if cl.contract_id in contracts else cl.contract_id
        hits.append(
            Hit(
                chunk_id=cl.id,
                document_id=cl.contract_id,
                title=f"{title} · {cl.risk_tag}",
                text=cl.text,
                score=s,
                meta={"risk_tag": cl.risk_tag, "risk_score": cl.risk_score, "heading": cl.heading},
            )
        )
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:k]


async def ask(session: AsyncSession, question: str) -> dict:
    hits = await search(session, question)
    context = pack_citations(hits) if hits else "(no clauses indexed)"
    llm = get_llm()
    answer = await llm.complete(
        f"Legal ops assistant. Quote risk tags. QUESTION: {question}\n\nCLAUSES:\n{context}",
        system="Be precise. Flag indemnity, liability, data, and termination risks.",
    )
    return {
        "answer": answer,
        "citations": [
            {
                "index": i,
                "clause_id": h.chunk_id,
                "contract_id": h.document_id,
                "title": h.title,
                "risk_tag": h.meta.get("risk_tag"),
                "score": round(h.score, 3),
                "snippet": h.text[:240],
            }
            for i, h in enumerate(hits, start=1)
        ],
    }
