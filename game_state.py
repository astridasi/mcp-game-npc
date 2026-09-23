"""Small, in-memory source of truth for the demo game world."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


INITIAL_INVENTORY = {"healing_potion": 2, "rusty_key": 1}
INITIAL_QUESTS = {
    "find_the_lost_map": {
        "title": "Find the Lost Map",
        "status": "active",
        "objective": "Search the old watchtower.",
    }
}
ALLOWED_ITEMS = {"healing_potion", "torch", "silver_coin"}
MAX_GRANT_QUANTITY = 5


@dataclass
class GameState:
    """Authoritative mock state exposed through a narrow tool boundary."""

    inventory: dict[str, int] = field(
        default_factory=lambda: deepcopy(INITIAL_INVENTORY)
    )
    quests: dict[str, dict[str, str]] = field(
        default_factory=lambda: deepcopy(INITIAL_QUESTS)
    )
    audit_log: list[dict[str, Any]] = field(default_factory=list)

    def get_inventory(self) -> dict[str, Any]:
        return {
            "items": [
                {"item": item, "quantity": quantity}
                for item, quantity in sorted(self.inventory.items())
            ]
        }

    def get_quest_state(self, quest_id: str) -> dict[str, Any]:
        quest = self.quests.get(quest_id)
        if quest is None:
            return {
                "found": False,
                "quest_id": quest_id,
                "error": "Unknown quest. Ask for a valid quest_id.",
            }
        return {"found": True, "quest_id": quest_id, **deepcopy(quest)}

    def give_item(self, item: str, quantity: int, reason: str) -> dict[str, Any]:
        if item not in ALLOWED_ITEMS:
            return {
                "success": False,
                "error": "Item is not grantable.",
                "allowed_items": sorted(ALLOWED_ITEMS),
            }
        if not 1 <= quantity <= MAX_GRANT_QUANTITY:
            return {
                "success": False,
                "error": f"quantity must be between 1 and {MAX_GRANT_QUANTITY}.",
            }
        if not reason.strip():
            return {"success": False, "error": "A reason is required."}

        self.inventory[item] = self.inventory.get(item, 0) + quantity
        event = {
            "action": "give_item",
            "item": item,
            "quantity": quantity,
            "reason": reason.strip(),
        }
        self.audit_log.append(event)
        return {
            "success": True,
            "item": item,
            "quantity_added": quantity,
            "new_quantity": self.inventory[item],
            "audit_event": event,
        }


game_state = GameState()

