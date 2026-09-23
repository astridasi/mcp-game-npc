"""Protocol-level demo that calls the server without an API key or LLM."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp import Client

from server import mcp


def show(label: str, value: Any) -> None:
    print(f"\n{label}")
    print(json.dumps(value, indent=2))


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        show("Available MCP tools", [tool.name for tool in tools.tools])

        inventory = await client.call_tool("get_inventory", {})
        show("1. NPC checks authoritative inventory", inventory.structured_content)

        quest = await client.call_tool(
            "get_quest_state", {"quest_id": "find_the_lost_map"}
        )
        show("2. NPC checks authoritative quest state", quest.structured_content)

        grant = await client.call_tool(
            "give_item",
            {
                "item": "torch",
                "quantity": 1,
                "reason": "Player accepted the watchtower quest.",
            },
        )
        show("3. NPC performs an explicit write", grant.structured_content)

        updated = await client.call_tool("get_inventory", {})
        show("4. NPC verifies the updated state", updated.structured_content)


if __name__ == "__main__":
    asyncio.run(main())
