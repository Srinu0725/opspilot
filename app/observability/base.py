from abc import ABC, abstractmethod


class ObservabilityProvider(ABC):
    """
    Abstract interface for production observability data.

    The agent interacts with this interface rather than knowing
    whether the data comes from local files, Google Cloud,
    Prometheus, Datadog, etc.
    """

    @abstractmethod
    def get_service_metrics(
        self,
        service: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """
        Retrieve service metrics for an optional time window.

        Args:
            service: Name of the service.
            start_time: Optional ISO-8601 start timestamp.
            end_time: Optional ISO-8601 end timestamp.

        Returns:
            Dictionary containing metric observations.
        """
        pass

    @abstractmethod
    def search_logs(
        self,
        service: str,
        keyword: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[str]:
        """
        Search service logs within an optional time window.

        Args:
            service: Name of the service.
            keyword: Optional keyword to search for.
            start_time: Optional ISO-8601 start timestamp.
            end_time: Optional ISO-8601 end timestamp.

        Returns:
            Matching log lines.
        """
        pass

    @abstractmethod
    def get_recent_deployment(
        self,
        service: str,
    ) -> dict:
        """
        Retrieve the most recent deployment information
        for a service.

        Args:
            service: Name of the service.

        Returns:
            Deployment information.
        """
        pass