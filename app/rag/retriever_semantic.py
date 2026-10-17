from pathlib import Path

from app.rag.loader import load_runbook
from app.rag.chunker import (
    chunk_markdown,
)
from app.rag.embeddings import (
    embedding_model,
)
from app.rag.store import VectorStore


class RunbookRetriever:

    def __init__(self):

        self.store: VectorStore | None = None

    def build(
        self,
        service: str,
    ):
        """
        Build a vector index for a service runbook.
        """

        document = load_runbook(
            service
        )

        source = (
            Path(
                "data/runbooks"
            )
            / f"{service}.md"
        ).name

        chunks = chunk_markdown(
            text=document,
            source=source,
            service=service,
            max_chunk_size=1200,
        )

        if not chunks:
            raise ValueError(
                f"No chunks generated for service: {service}"
            )

        texts = [
            chunk.content
            for chunk in chunks
        ]

        embeddings = (
            embedding_model.encode(
                texts
            )
        )

        dimension = embeddings.shape[1]

        self.store = VectorStore(
            dimension
        )

        documents = [
            {
                "content": chunk.content,
                "source": chunk.source,
                "service": chunk.service,
                "section": chunk.section,
            }
            for chunk in chunks
        ]

        self.store.add(
            embeddings=embeddings,
            documents=documents,
        )

        print(
            f"[RAG] Built index for "
            f"{service}: "
            f"{len(chunks)} chunks"
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.35,
    ) -> list[dict]:

        if self.store is None:
            raise RuntimeError(
                "Retriever has not been built yet."
            )

        query_embedding = (
            embedding_model.encode(
                [query]
            )
        )

        return self.store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
        )


_retrievers: dict[
    str,
    RunbookRetriever,
] = {}


def search_runbook(
    service: str,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    Search a service runbook using
    semantic similarity.
    """

    print(
        f"[TOOL] search_runbook("
        f"service={service}, "
        f"query={query!r}, "
        f"top_k={top_k}"
        f")"
    )

    if service not in _retrievers:

        retriever = RunbookRetriever()

        retriever.build(
            service
        )

        _retrievers[
            service
        ] = retriever

    results = _retrievers[
        service
    ].search(
        query=query,
        top_k=top_k,
        score_threshold=0.35,
    )

    return results