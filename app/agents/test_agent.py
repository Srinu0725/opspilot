import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents.opspilot_agent import root_agent


async def main():
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="opspilot",
    )

    session = await runner.session_service.create_session(
        app_name="opspilot",
        user_id="local-user",
    )

    message = types.Content(
    role="user",
    parts=[
        types.Part(
            text=(
                "The payment-api service is experiencing "
                "a sudden increase in latency. "
                "Investigate the issue and identify "
                "the likely root cause."
            )
        )
    ],
)
    print("\nStarting OpsPilot investigation...\n")

    async for event in runner.run_async(
        user_id="local-user",
        session_id=session.id,
        new_message=message,
    ):
        if not event.content:
            continue

        if not event.content.parts:
            continue

        for part in event.content.parts:
            if part.text:
                print(part.text)


if __name__ == "__main__":
    asyncio.run(main())
