# Copyright (c) 2026 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import json
from typing import Tuple, AsyncGenerator

from quart import Blueprint, Response, jsonify

from backend.BuzzerLogic.State import State
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication


class ApiFlow:
    """Initialize the flow API and register routes.

    Attributes:
        __bt_comm (BluetoothCommunication):
            Bluetooth communication handler used to send commands to
            connected buzzers and retrieve their configuration.

        __state (State):
            Global application state container.
            This attribute is stored for consistency with other API
            classes, even if not directly used by this class.

        blueprint (Blueprint):
            Quart Blueprint exposing check-related API endpoints.
            All routes are prefixed with ``/api/check``.
    """

    def __init__(self, bt_comm: BluetoothCommunication, state: State):
        """Initialize the flow API and register routes.

        Args:
            bt_comm (BluetoothCommunication):
                Bluetooth communication handler used to communicate
                with connected buzzers.
            state (State):
                Global application state container.
        """

        self.__bt_comm: BluetoothCommunication = bt_comm
        self.__state: State = state

        self.blueprint = Blueprint("api_flow", __name__, url_prefix="/api/flow")

        self.blueprint.add_url_rule("/wait_press", view_func=self.wait_press, methods=['POST'])
        self.blueprint.add_url_rule("/confirm", view_func=self.confirm, methods=['POST'])
        self.blueprint.add_url_rule("/deny", view_func=self.deny, methods=['POST'])

    async def wait_press_stream(self) -> AsyncGenerator[str, str]:
        """Stream press state updates to the client.

        This async generator first emits a state indicating that the system
        is waiting for a buzzer press. It then blocks until a press is
        detected via the global application state, after which it emits a
        state indicating that the system is waiting for confirmation.

        Yields:
            str:
                A JSON-encoded string containing the current flow state,
                terminated by a newline for streaming.
        """

        yield json.dumps({'state': 'waiting for press'}) + "\n"

        await self.__state.wait_press()

        yield json.dumps({'state': 'waiting for confirmation'}) + "\n"

    async def wait_press(self) -> Tuple[Response, int]:
        """Start streaming buzzer press state to the client.

        This endpoint returns a streaming HTTP response that emits flow
        state changes as they occur, using a JSON newline-delimited format.

        Returns:
            Tuple[Response, int]:
                A streaming Quart Response object and the corresponding
                HTTP status code.
        """

        return Response(self.wait_press_stream(), mimetype="application/json"), 200

    async def confirm(self) -> Tuple[Response, int]:
        """Confirm the currently pending buzzer press.

        This signals the global application state that the most recent
        buzzer press has been accepted and processed.

        Returns:
            Tuple[Response, int]:
                A JSON response indicating success, and an HTTP status code.
        """

        await self.__state.confirm_press()

        return jsonify({"status": "ok"}), 200

    async def deny(self) -> Tuple[Response, int]:
        """Deny the currently pending buzzer press.

        This signals the global application state that the most recent
        buzzer press has been rejected and should be ignored.

        Returns:
            Tuple[Response, int]:
                A JSON response indicating success, and an HTTP status code.
        """

        await self.__state.deny_press()

        return jsonify({"status": "ok"}), 200
