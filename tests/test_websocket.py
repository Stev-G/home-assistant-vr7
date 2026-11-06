import json

import pytest
from homeassistant.components.vacuum import VacuumActivity

from custom_components.vr7.websocket import VR7WebSocket


@pytest.mark.parametrize(
    ("body", "expected_activity"),
    [
        ({"action": "cleaning", "state": "busy"}, VacuumActivity.CLEANING),
        ({"state": "paused"}, VacuumActivity.PAUSED),
        ({"action": "going_home", "state": "busy"}, VacuumActivity.RETURNING),
        (
            {"state": "idle", "details": {"is_docked": True}},
            VacuumActivity.DOCKED,
        ),
        ({"state": "idle"}, VacuumActivity.IDLE),
        ({"state": "busy"}, None),
        ({"state": "error", "errors": [{"code": "brush_stuck"}]}, VacuumActivity.ERROR),
    ],
)
def test_status_body_maps_to_home_assistant_activity(body, expected_activity):
    updates = []
    client = object.__new__(VR7WebSocket)
    client.update_callback = updates.append

    client._publish_body(body)

    assert updates[0]["activity"] == expected_activity


def test_last_state_phoenix_message_updates_entity_state():
    updates = []
    client = object.__new__(VR7WebSocket)
    client.update_callback = updates.append
    message = [
        "1",
        "3",
        "robots:robot-id",
        "last_state",
        {"body": {"state": "paused", "available_commands": {"resume": True}}},
    ]

    client._handle_message(json.dumps(message))

    assert updates[0]["activity"] == VacuumActivity.PAUSED
    assert updates[0]["available_commands"] == {"resume": True}
