from app.rag.loader import load_runbook
from app.rag.chunker import chunk_text


def test_load_payment_api_runbook():
    text = load_runbook("payment-api")

    assert text
    assert "Payment API" in text
    assert "Database Latency" in text


def test_chunk_runbook():
    text = load_runbook("payment-api")

    chunks = chunk_text(
        text,
        chunk_size=500,
        chunk_overlap=100,
    )

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.strip()