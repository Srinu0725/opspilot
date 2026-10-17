from datetime import datetime


def parse_timestamp(
    timestamp: str | None,
) -> datetime | None:
    """
    Parse an ISO-8601 timestamp.

    Supports timestamps ending in Z.
    """

    if not timestamp:
        return None

    try:
        return datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
    except ValueError:
        return None