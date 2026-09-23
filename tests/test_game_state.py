from game_state import GameState


def test_inventory_is_returned_as_structured_data() -> None:
    state = GameState()
    assert state.get_inventory() == {
        "items": [
            {"item": "healing_potion", "quantity": 2},
            {"item": "rusty_key", "quantity": 1},
        ]
    }


def test_known_and_unknown_quest_results_are_explicit() -> None:
    state = GameState()
    assert state.get_quest_state("find_the_lost_map")["status"] == "active"
    assert state.get_quest_state("invented_quest") == {
        "found": False,
        "quest_id": "invented_quest",
        "error": "Unknown quest. Ask for a valid quest_id.",
    }


def test_give_item_mutates_state_and_records_reason() -> None:
    state = GameState()
    result = state.give_item("torch", 1, "Quest reward")
    assert result["success"] is True
    assert state.inventory["torch"] == 1
    assert state.audit_log == [
        {
            "action": "give_item",
            "item": "torch",
            "quantity": 1,
            "reason": "Quest reward",
        }
    ]


def test_give_item_rejects_unapproved_or_excessive_grants() -> None:
    state = GameState()
    assert state.give_item("legendary_sword", 1, "Because")["success"] is False
    assert state.give_item("torch", 99, "Because")["success"] is False
    assert state.inventory == {"healing_potion": 2, "rusty_key": 1}

