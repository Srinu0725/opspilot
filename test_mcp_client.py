import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def main():
    # url = "http://127.0.0.1:8002/mcp"
    url = "https://opspilot-odgn.onrender.com/mcp"

    async with streamablehttp_client(url) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(
            read_stream, write_stream
        ) as session:
            await session.initialize()

            print("\nConnected to OpsPilot MCP server.")

            tools = await session.list_tools()

            print("\nAvailable tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            print("\nTesting runbook search...")

            result = await session.call_tool(
                "find_runbook_guidance",
                arguments={
                    "service": "payment-api",
                    "query": "slow database query payment_lookup",
                    "top_k": 3,
                },
            )

            print("\nRunbook search result:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            if result.isError:
                raise RuntimeError("Runbook tool returned an error")
            
            print("\nTesting full incident investigation...")

            result = await session.call_tool(
                "investigate_service",
                arguments={
                    "service": "payment-api",
                },
            )

            print("\nInvestigation result:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            if result.isError:
                raise RuntimeError(
                    "Investigation tool returned an error"
                )
if __name__ == "__main__":
    asyncio.run(main())
