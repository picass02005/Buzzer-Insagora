# Copyright (c) 2026 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
import re
from typing import List, Tuple

from quart import Blueprint, Response, jsonify

from backend.BuzzerLogic.State import State
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication

HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


class ApiLights:
    def __init__(self, bt_comm: BluetoothCommunication, teams: List[Team], state: State):
        """Initialize the lights API and register routes.

        Args:
            bt_comm (BluetoothCommunication):
                Bluetooth communication handler used to query connected devices.
            teams (List[Team]):
                List of teams currently registered in the system.
            state (State):
                Global application state container.
        """

        self.__bt_comm: BluetoothCommunication = bt_comm
        self.__teams: List[Team] = teams
        self.__state: State = state

        self.blueprint = Blueprint("api_lights", __name__, url_prefix="/api/lights")

        self.blueprint.add_url_rule("/reset_led_default", view_func=self.reset_led_default, methods=['PUT'])

    async def reset_led_default(self) -> Tuple[Response, int]:
        await self.__state.set_led_on_state()

        return jsonify({"status": "ok"}), 200

    # TODO: ~~register buzzer~~ Identify buzzer => update_team

    # TODO: docstring
