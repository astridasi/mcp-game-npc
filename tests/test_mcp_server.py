import pytest
from mcp import Client

from server import mcp


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_tools_are_discoverable_and_callable_through_mcp() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools.tools} == {
            "get_inventory",
            "get_quest_state",
            "give_item",
        }

        result = await client.call_tool(
            "get_quest_state", {"quest_id": "find_the_lost_map"}
        )
        assert result.structured_content["found"] is True
        assert result.structured_content["status"] == "active"
