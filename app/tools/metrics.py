from app.observability.local import LocalObservabilityProvider


provider = LocalObservabilityProvider()


def get_service_metrics(
    service: str,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict:
    """
    Retrieve service metrics through the configured
    observability provider.

    Args:
        service: Name of the service.
        start_time: Optional ISO-8601 start timestamp.
        end_time: Optional ISO-8601 end timestamp.

    Returns:
        Historical or snapshot metric data.
    """

    return provider.get_service_metrics(
        service=service,
        start_time=start_time,
        end_time=end_time,
    )