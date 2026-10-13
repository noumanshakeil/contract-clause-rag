import pytest

SAMPLE = '''
This Agreement includes a limitation of liability for consequential damages.
Provider shall indemnify Customer against third-party IP claims.
Personal data will be processed under GDPR with a DPA.
Either party may terminate for convenience with 30 days notice.
'''

@pytest.mark.asyncio
async def test_ingest_and_risk(client):
    r = await client.post(
        "/api/contracts",
        json={"name": "Acme MSA", "counterparty": "Acme", "body": SAMPLE},
    )
    assert r.status_code == 200
    assert r.json()["clauses"] >= 1
    clauses = (await client.get("/api/clauses")).json()["clauses"]
    tags = {c["risk_tag"] for c in clauses}
    assert "indemnity" in tags or "liability" in tags or "data" in tags
    ask = await client.post("/api/ask", json={"question": "What are the indemnity terms?"})
    assert ask.status_code == 200
    assert "citations" in ask.json()
