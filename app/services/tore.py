import faiss
import numpy as np


class VectorStore:
    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatIP(dimension)
        self.documents: list[str] = []

    def add(
        self,
        embeddings: np.ndarray,
        documents: list[str],
    ):
        self.index.add(
            embeddings.astype("float32")
        )

        self.documents.extend(documents)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
    ) -> list[dict]:

        scores, indices = self.index.search(
            query_embedding.astype("float32"),
            top_k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index == -1:
                continue

            results.append(
                {
                    "score": float(score),
                    "document": self.documents[index],
                }
            )

        return results