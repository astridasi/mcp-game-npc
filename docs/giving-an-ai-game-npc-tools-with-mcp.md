# Giving an AI Game NPC Tools: From Dialogue to Action with MCP

Large language models are good at producing dialogue that sounds plausible. A game, however, cannot treat plausibility as truth.

If an NPC says, “You already collected the rusty key,” the game needs to know whether that item is really in the player's inventory. If the NPC promises, “I have added a torch to your pack,” the inventory must actually change. A prompt containing a summary of the game world can help, but summaries become stale and a model can still invent details.

This article describes a small learning project I built to explore a better boundary: an MCP server with three tools that let an AI-enabled NPC read and update mock game state.

The project is intentionally limited. It is not a production game integration and I am not presenting it as production MCP experience. The point is to make the architecture visible, test it, and document the trade-offs clearly.

## Start with the source of truth

The first design decision is not about the model. It is about ownership.

The game service owns inventory and quest state. The language model does not. The model can decide that it needs information or propose an action, but it must use a defined interface to obtain the current answer or request the state change.

The demo exposes three tools:

```text
get_inventory()
get_quest_state(quest_id)
give_item(item, quantity, reason)
```

The first two read state. The third writes state. That separation is simple, but it changes the interaction from “generate a convincing sentence” to “check facts, request an operation, then explain the result.”

## Where MCP sits

Model Context Protocol standardizes how an AI application connects to external tools and data. In this example:

1. A game client or AI host connects to the MCP server.
2. The host discovers the server's available tools and their schemas.
3. A model can select a tool based on the player's request and the tool description.
4. The host invokes the tool, subject to its own approval and security policy.
5. The server returns structured data.
6. The model uses that result when composing the NPC's response.

MCP is therefore the connection contract. It does not make the model truthful by itself, and it does not replace game logic, authentication, or authorization.

This distinction matters because “the model has tools” can sound as if the model directly controls the application. In practice, a host mediates the connection. The server decides which operations exist and validates requests; the host decides what it will expose or approve; the model proposes how to use those capabilities.

## A minimal implementation

I used Python and the official MCP Python SDK. The server is small enough to understand in one reading:

```python
from mcp.server import MCPServer
from mcp_types import ToolAnnotations

from game_state import game_state

mcp = MCPServer("MCP Game NPC")


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def get_inventory() -> dict:
    """Return the player's current inventory from authoritative game state."""
    return game_state.get_inventory()
```

The SDK derives a tool schema from the Python type hints and docstring. A client can discover that schema through MCP instead of depending on a separate, manually synchronized description.

The quest tool follows the same pattern but takes a stable quest identifier:

```python
@mcp.tool(...)
def get_quest_state(quest_id: str) -> dict:
    """Return one quest's status and objective."""
    return game_state.get_quest_state(quest_id)
```

Unknown identifiers return an explicit `found: false` result. That is preferable to returning an empty string that a model might interpret too freely.

## The write tool needs a different mindset

Reading an inventory and modifying it are not equivalent operations.

The demo's `give_item` tool is marked as a write and as non-idempotent. If the same call is replayed, the player receives the item again. The implementation therefore validates the item against an allowlist, limits quantity, requires a reason, and records an audit event.

```python
@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )
)
def give_item(item: str, quantity: int, reason: str) -> dict:
    """Add an allowed item to the player's inventory."""
    return game_state.give_item(item, quantity, reason)
```

The annotations communicate intent to a client, but they are not enforcement. The MCP specification says clients must treat annotations as untrusted unless they come from a trusted server. The actual safety boundary remains server-side validation plus the host's authorization and confirmation policy.

In a real game, I would also expect authenticated player identity, server-authoritative transactions, durable logs, rate limits, idempotency keys or replay protection, and monitoring. A valuable item grant might require a stricter approval path than a dialogue lookup.

## An example interaction

Imagine the player tells an NPC:

> I cannot see inside the watchtower. Can you help?

A tool-aware flow could be:

1. Query `get_quest_state("find_the_lost_map")`.
2. Verify that the active objective is to search the old watchtower.
3. Query `get_inventory()`.
4. See that the player has no torch.
5. Request `give_item("torch", 1, "Player accepted the watchtower quest.")`.
6. Generate the response from the confirmed result: “Take this torch. The old watchtower is your next objective.”

The sentence is still generated language. The inventory fact and the item grant are not.

There is also a useful failure mode. If the model requests a `legendary_sword`, the server rejects it and returns the allowed items. The model can then recover in dialogue without the game accepting an invalid state change.

## Testing the boundary, not only the functions

Unit tests cover inventory reads, known and unknown quests, successful grants, validation failures, and audit records. I also added a protocol-level test that creates an MCP client, connects directly to the server in memory, lists the tools, and calls `get_quest_state`.

That second test is important. Directly calling a Python function proves the business logic works; calling it through an MCP client also checks that the tool is registered, discoverable, serialized, and callable through the protocol layer.

The repository includes a `demo_client.py` script that performs the same sequence and prints structured results. It uses no API key and no model provider. That keeps the example reproducible and isolates the question being tested: does the MCP tool boundary work?

## What MCP solves—and what it does not

This project helped me separate several concerns that are easy to blend together:

- **MCP provides discovery and invocation.** It gives hosts a consistent way to list and call tools.
- **The game service provides authority.** Inventory rules and quest data still belong to the application.
- **The host provides control.** It can require approval, hide tools, log calls, or reject operations.
- **The model provides interpretation and language.** It decides what information may help and turns verified results into dialogue.

MCP does not guarantee that a model will always choose the correct tool. It does not automatically secure a poorly designed write operation. It does not remove the need for application-specific error handling. It makes those boundaries explicit enough to inspect and improve.

## Design choices I would revisit for production

The demo keeps all state in memory, so it resets when the process exits. There is one player, one quest, no concurrency, and no network deployment. Those limitations are deliberate, but a production design would need decisions about:

- player and session identity;
- authorization per tool and per item;
- transactions and concurrent updates;
- retry behavior for non-idempotent calls;
- audit retention and operational monitoring;
- versioning of tool schemas and game content;
- how the game engine and AI host exchange context;
- latency budgets for dialogue and actions;
- fallback behavior when the model or tool server is unavailable.

I would also evaluate whether every operation should be a tool. Stable reference information may be better represented as a resource, while state-changing commands naturally fit tools. The smallest useful interface is usually easier to secure and easier for a model to select correctly.

## What I learned

My background is in commercial game development and interactive systems rather than production infrastructure engineering. That perspective made the game-NPC analogy useful: game designers already work with state, conditions, triggers, permissions, and visible player feedback.

Building this demo turned an abstract topic into a concrete workflow:

1. identify the authoritative system;
2. define the smallest useful capabilities;
3. distinguish observation from mutation;
4. validate actions at the boundary;
5. test both logic and protocol behavior;
6. document what the example does not solve.

That is also why I am interested in Developer Relations and Developer Experience. I enjoy taking a technical system, making a focused experiment, debugging it, and then explaining it in a way another developer can reproduce and question.

## References

- [Model Context Protocol documentation](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)

