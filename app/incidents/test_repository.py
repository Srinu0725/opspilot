import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import AsyncSessionLocal
from app.incidents.repository import IncidentRepository


async def test_repository():
    incident_id = str(uuid4())

    async with AsyncSessionLocal() as session:
        repository = IncidentRepository(session)

        incident = await repository.create(
            incident_id=incident_id,
            service="payment-api",
            status="CREATED",
            stage="CREATED",
            severity="high",
            description="Repository database test",
            start_time=datetime.now(timezone.utc),
            end_time=None,
            created_at=datetime.now(timezone.utc),
            metadata={"source": "repository-test"},
        )

        print("\nCreated incident:")
        print(f"  ID:      {incident.incident_id}")
        print(f"  Service: {incident.service}")
        print(f"  Status:  {incident.status}")
        print(f"  Stage:   {incident.stage}")

        fetched = await repository.get_by_id(incident_id)

        if fetched is None:
            raise RuntimeError("Failed to fetch the created incident.")

        print("\nFetched incident:")
        print(f"  ID:      {fetched.incident_id}")
        print(f"  Service: {fetched.service}")
        print(f"  Status:  {fetched.status}")
        print(f"  Stage:   {fetched.stage}")

        assert fetched.incident_id == incident_id
        assert fetched.service == "payment-api"
        assert fetched.status == "CREATED"
        assert fetched.stage == "CREATED"

        print("\nRepository test passed.")
        print("PostgreSQL persistence is working correctly.")


if __name__ == "__main__":
    asyncio.run(test_repository())