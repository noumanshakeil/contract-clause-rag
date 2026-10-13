# Architecture — Contract Clause RAG

Ingest splits contract text into overlapping chunks, applies regex risk detectors
(indemnity, liability, data, IP, auto-renew, termination), stores clauses, then
ranks them for search/ask with a risk-score bias so dangerous language surfaces first.
