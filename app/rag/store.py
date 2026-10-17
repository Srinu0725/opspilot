import faiss
import numpy as np


class VectorStore:
    """
    FAISS-based vector store with document metadata.
    """

    def __init__(self, dimension: int):

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.documents: list[dict] = []

    def add(
        self,
        embeddings: np.ndarray,
        documents: list[dict],
    ):
        """
        Add embeddings and their associated metadata.
        """

        if len(embeddings) != len(documents):
            raise ValueError(
                "Number of embeddings must match "
                "number of documents."
            )

        self.index.add(
            embeddings.astype("float32")
        )

        self.documents.extend(
            documents
        )

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        """
        Search for semantically similar documents.

        Results below score_threshold are discarded.
        """

        if self.index.ntotal == 0:
            return []

        # Never request more documents than
        # are actually stored.
        actual_k = min(
            top_k,
            self.index.ntotal,
        )

        scores, indices = self.index.search(
            query_embedding.astype("float32"),
            actual_k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):

            if index == -1:
                continue

            score = float(score)

            if score < score_threshold:
                continue

            document = self.documents[index]

            results.append(
                {
                    "relevance_score": round(
                        score,
                        4,
                    ),
                    "document": document,
                }
            )

        return results