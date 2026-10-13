from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import contracts as svc

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Contract Clause RAG",
            "contracts": await svc.list_contracts(db),
            "clauses": await svc.list_clauses(db),
            "answer": None,
            "citations": [],
        },
    )

@router.post("/ui/contracts")
async def ui_add(
    name: str = Form(...),
    counterparty: str = Form(""),
    body: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    await svc.ingest(db, name, body, counterparty)
    return RedirectResponse("/", status_code=303)

@router.post("/ui/ask", response_class=HTMLResponse)
async def ui_ask(request: Request, question: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await svc.ask(db, question)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Contract Clause RAG",
            "contracts": await svc.list_contracts(db),
            "clauses": await svc.list_clauses(db),
            "answer": result["answer"],
            "citations": result["citations"],
            "question": question,
        },
    )
