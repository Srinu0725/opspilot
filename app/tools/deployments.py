# import json
# from pathlib import Path


# DEPLOYMENTS_DIR = Path("data/deployments")


# def get_recent_deployment(service: str) -> dict:
#     """
#     Retrieve the latest deployment information.

#     Currently reads local JSON data.
#     Later this can query a real deployment system.
#     """

#     print(
#         f"[TOOL] get_recent_deployment(service={service})"
#     )

#     deployment_file = DEPLOYMENTS_DIR / f"{service}.json"

#     if not deployment_file.exists():
#         return {
#             "error": (
#                 f"No deployment information "
#                 f"available for service: {service}"
#             )
#         }

#     try:
#         with deployment_file.open(
#             "r",
#             encoding="utf-8",
#         ) as file:
#             return json.load(file)

#     except json.JSONDecodeError:
#         return {
#             "error": (
#                 f"Invalid deployment data "
#                 f"available for service: {service}"
#             )
#         }

from app.observability.local import LocalObservabilityProvider


provider = LocalObservabilityProvider()


def get_recent_deployment(service: str) -> dict:
    """
    Retrieve deployment information through the configured
    observability provider.
    """
    return provider.get_recent_deployment(
        service=service
    )