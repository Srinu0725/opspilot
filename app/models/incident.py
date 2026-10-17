from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    service: str = Field(
        ...,
        description="Name of the affected service.",
        examples=["payment-api"],
    )

    description: str = Field(
        ...,
        description="Description of the production incident.",
        examples=[
            "Payment API latency has suddenly increased"
        ],
    )

    severity: str = Field(
        default="medium",
        description="Incident severity.",
        examples=["low", "medium", "high", "critical"],
    )