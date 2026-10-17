import re

from app.rag.loader import load_runbook
from app.rag.chunker import chunk_markdown


_retrievers: dict[str, list[dict]] = {}


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if len(token) > 1
    }


def _build(service: str) -> list[dict]:
    document = load_runbook(service)

    chunks = chunk_markdown(
        text=document,
        source=f"{service}.md",
        service=service,
        max_chunk_size=1200,
    )

    if not chunks:
        raise ValueError(
            f"No runbook chunks generated for service: {service}"
        )

    return [
        {
            "content": chunk.content,
            "source": chunk.source,
            "service": chunk.service,
            "section": chunk.section,
            "_tokens": _tokens(chunk.content),
        }
        for chunk in chunks
    ]


def search_runbook(
    service: str,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """Retrieve runbook sections using lightweight keyword overlap."""

    if service not in _retrievers:
        _retrievers[service] = _build(service)

    query_tokens = _tokens(query)

    if not query_tokens:
        return []

    ranked = []

    for document in _retrievers[service]:
        matched = query_tokens & document["_tokens"]

        if not matched:
            continue

        score = len(matched) / len(query_tokens)

        result_document = {
            key: value
            for key, value in document.items()
            if key != "_tokens"
        }

        ranked.append({
            "relevance_score": round(score, 4),
            "document": result_document,
        })

    ranked.sort(
        key=lambda item: item["relevance_score"],
        reverse=True,
    )

    print(
        f"[RAG-LITE] {service}: "
        f"{len(ranked)} matching chunks"
    )

    return ranked[:max(0, top_k)]
