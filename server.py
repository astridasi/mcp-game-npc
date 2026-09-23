"""MCP tools for a game NPC to read and update authoritative game state."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_types import ToolAnnotations

from game_state import game_state


mcp = MCPServer(
    "MCP Game NPC",
    instructions=(
        "Use get_inventory and get_quest_state before making claims about the "
        "player's state. Call give_item only when the player has explicitly "
        "earned or requested an allowed item, and explain the reason."
    ),
)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Get inventory",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def get_inventory() -> dict[str, Any]:
    """Return the player's current inventory from authoritative game state."""
    return game_state.get_inventory()


@mcp.tool(
    annotations=ToolAnnotations(
        title="Get quest state",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def get_quest_state(quest_id: str) -> dict[str, Any]:
    """Return one quest's status and objective.

    Args:
        quest_id: Stable quest identifier, for example ``find_the_lost_map``.
    """
    return game_state.get_quest_state(quest_id)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Give item",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )
)
def give_item(item: str, quantity: int, reason: str) -> dict[str, Any]:
    """Add an allowed item to the player's inventory.

    This is a write operation. Repeating the same call grants the item again.

    Args:
        item: Grantable item identifier.
        quantity: Number of items to add (1-5).
        reason: Short audit explanation for the grant.
    """
    return game_state.give_item(item, quantity, reason)


if __name__ == "__main__":
    mcp.run(transport="stdio")

