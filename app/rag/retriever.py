import os

if os.getenv("OPSPILOT_LIGHTWEIGHT_RAG", "0") == "1":
    from app.rag.retriever_lightweight import search_runbook
else:
    from app.rag.retriever_semantic import search_runbook
