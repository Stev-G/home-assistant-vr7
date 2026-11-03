"""Companion WebSocket client for live VR7 state updates."""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from typing import Any

import aiohttp
from homeassistant.components.vacuum import VacuumActivity
from homeassistant.core import HomeAssistant

from .const import (
    COMP_WS,
    MOBILE_APP_ACCEPT_ENCODING,
    MOBILE_APP_BUILD,
    MOBILE_APP_OS,
    MOBILE_APP_OS_VERSION,
    MOBILE_APP_USER_AGENT,
    MOBILE_APP_VERSION,
    SUPPORTED_MARKETS,
    DEFAULT_MARKET,
)

_LOGGER = logging.getLogger(__name__)

_CLEANING_ACTIONS = {
    "cleaning",
    "fast_mapping",
    "mapping",
    "map_creation",
    "spot_cleaning",
}
_RETURNING_ACTIONS = {"docking", "returning", "going_home"}


class VR7WebSocket:
    """Maintain the Companion status channel and publish normalized states."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api: Any,
        robot_id: str,
        market: str,
        update_callback: Callable[[dict[str, Any]], None],
    ) -> None:
        self.hass = hass
        self.session = session
        self.api = api
        self.robot_id = robot_id
        self.market = market
        self.update_callback = update_callback
        self._task: asyncio.Task | None = None
        self._websocket: aiohttp.ClientWebSocketResponse | None = None
        self._stopping = False

    def start(self) -> None:
        """Start the reconnecting listener in the Home Assistant loop."""
        if self._task is None or self._task.done():
            self._stopping = False
            self._task = self.hass.async_create_task(
                self._run(), "vr7_status_websocket"
            )

    async def stop(self) -> None:
        """Close the WebSocket and stop reconnect attempts."""
        self._stopping = True
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _run(self) -> None:
        retry_delay = 2
        while not self._stopping:
            heartbeat_task = None
            try:
                authorization = await self.api.get_companion_authorization()
                language = SUPPORTED_MARKETS.get(
                    self.market, SUPPORTED_MARKETS[DEFAULT_MARKET]
                )["accept_language"]
                headers = {
                    "Authorization": authorization,
                    "Accept-Language": language,
                    "mobile-app-version": MOBILE_APP_VERSION,
                    "mobile-app-build": MOBILE_APP_BUILD,
                    "mobile-app-os": MOBILE_APP_OS,
                    "mobile-app-os-version": MOBILE_APP_OS_VERSION,
                    "Accept-Encoding": MOBILE_APP_ACCEPT_ENCODING,
                    "User-Agent": MOBILE_APP_USER_AGENT,
                }
                async with self.session.ws_connect(
                    COMP_WS, headers=headers, heartbeat=30
                ) as websocket:
                    self._websocket = websocket
                    await self._join_robot_channel(websocket)
                    heartbeat_task = self.hass.async_create_task(
                        self._phoenix_heartbeat(websocket)
                    )
                    _LOGGER.info("Connected to VR7 status service")
                    retry_delay = 2
                    async for message in websocket:
                        if message.type == aiohttp.WSMsgType.TEXT:
                            self._handle_message(message.data)
                        elif message.type == aiohttp.WSMsgType.ERROR:
                            raise websocket.exception() or ConnectionError(
                                "VR7 WebSocket connection failed"
                            )
                    if not self._stopping:
                        raise ConnectionError("VR7 WebSocket closed")
            except asyncio.CancelledError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError) as err:
                if not self._stopping:
                    _LOGGER.warning(
                        "VR7 status connection failed; retrying in %s seconds: %s",
                        retry_delay,
                        err,
                    )
            except Exception:
                if not self._stopping:
                    _LOGGER.exception("Unexpected error in VR7 status connection")
            finally:
                self._websocket = None
                if heartbeat_task:
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        _LOGGER.debug("VR7 Phoenix heartbeat stopped", exc_info=True)
            if not self._stopping:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)

    async def _join_robot_channel(
        self, websocket: aiohttp.ClientWebSocketResponse
    ) -> None:
        topic = f"robots:{self.robot_id}"
        await websocket.send_json(["1", "2", topic, "phx_join", {}])
        await websocket.send_json(
            [
                "1",
                "3",
                topic,
                "last_state",
                {"request_id": str(uuid.uuid4())},
            ]
        )

    async def _phoenix_heartbeat(
        self, websocket: aiohttp.ClientWebSocketResponse
    ) -> None:
        ref = 3
        while not websocket.closed and not self._stopping:
            await asyncio.sleep(30)
            ref += 1
            await websocket.send_json([None, str(ref), "phoenix", "heartbeat", {}])

    def _handle_message(self, message: str) -> None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            _LOGGER.debug("Ignoring non-JSON VR7 status message")
            return

        if isinstance(data, list) and len(data) >= 5:
            event, payload = data[3], data[4]
            if event == "last_state":
                self._publish_body(payload.get("body"))
            elif event == "phx_reply":
                self._publish_body(
                    (payload.get("response") or {}).get("body")
                )
            elif event == "state_changed":
                self._publish_body(payload.get("state", payload))
            return

        if isinstance(data, dict):
            event = data.get("event_type")
            payload = data.get("payload") or {}
            if event == "state_changed":
                self._publish_body(payload.get("state", payload))
            elif event == "last_state":
                self._publish_body(payload.get("body", payload))

    def _publish_body(self, body: Any) -> None:
        if not isinstance(body, dict):
            return

        details = body.get("details") or {}
        errors = body.get("errors") or []
        action = body.get("action")
        state = body.get("state")

        if errors:
            activity = VacuumActivity.ERROR
        elif action in _CLEANING_ACTIONS:
            activity = VacuumActivity.CLEANING
        elif action in _RETURNING_ACTIONS:
            activity = VacuumActivity.RETURNING
        elif state == "paused":
            activity = VacuumActivity.PAUSED
        elif state == "charging":
            activity = VacuumActivity.DOCKED
        elif state == "idle":
            activity = (
                VacuumActivity.DOCKED
                if details.get("is_docked")
                else VacuumActivity.IDLE
            )
        elif state == "busy":
            activity = VacuumActivity.CLEANING if action else None
        else:
            activity = None

        self.update_callback(
            {
                "activity": activity,
                "status": action or state,
                "available_commands": body.get("available_commands"),
                "battery_level": details.get("charge"),
                "is_charging": details.get("is_charging"),
                "errors": errors,
            }
        )
