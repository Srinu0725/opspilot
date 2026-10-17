from app.observability.local import LocalObservabilityProvider


provider = LocalObservabilityProvider()


def search_logs(
    service: str,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[str]:
    """
    Search service logs through the configured
    observability provider.

    Args:
        service: Name of the service.
        keyword: Optional keyword to search for.
        start_time: Optional ISO-8601 start timestamp.
        end_time: Optional ISO-8601 end timestamp.

    Returns:
        Matching log lines.
    """

    return provider.search_logs(
        service=service,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
    )