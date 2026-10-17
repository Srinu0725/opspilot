from app.rag.retriever import (
    search_runbook,
)


def print_results(
    query: str,
    results: list[dict],
):
    print()
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    if not results:
        print("No relevant results found.")
        return

    for i, result in enumerate(
        results,
        start=1,
    ):

        print()
        print(
            f"RESULT {i}"
        )

        print(
            f"Score: "
            f"{result['relevance_score']}"
        )

        document = result[
            "document"
        ]

        print(
            f"Source: "
            f"{document['source']}"
        )

        print(
            f"Service: "
            f"{document['service']}"
        )

        print(
            f"Section: "
            f"{document['section']}"
        )

        print(
            "Content:"
        )

        print(
            document["content"]
        )


def main():

    queries = [

        (
            "Database latency is high "
            "but CPU and memory are normal"
        ),

        (
            "What should I check after "
            "a recent deployment causes latency?"
        ),

        (
            "What evidence should be "
            "correlated to determine root cause?"
        ),

        (
            "What should I investigate "
            "when payment lookup becomes slow?"
        ),

    ]

    for query in queries:

        results = search_runbook(
            service="payment-api",
            query=query,
            top_k=3,
        )

        print_results(
            query,
            results,
        )


if __name__ == "__main__":
    main()