# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import Tuple

from quart import Blueprint, jsonify, Response

from backend.BuzzerLogic.State import State
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.ESPCommunication.LEDManager import Color


class Test:
    """Defines the `/` route for testing the BLE communication backend.

    This class encapsulates a Quart blueprint for the test route, allowing
    the route to access the BluetoothCommunication instance.

    Attributes:
        __bt_comm (BluetoothCommunication): The Bluetooth communication instance
            used by routes.
        blueprint (Blueprint): The Quart blueprint containing the routes for this class.
    """

    def __init__(self, bt_comm: BluetoothCommunication):
        """Defines the `/` route for testing the BLE communication backend.

        This class encapsulates a Quart blueprint for the test route, allowing
        the route to access the BluetoothCommunication instance.

        Attributes:
            __bt_comm (BluetoothCommunication): The Bluetooth communication instance
                used by routes.
            blueprint (Blueprint): The Quart blueprint containing the routes for this class.
        """

        self.__bt_comm: BluetoothCommunication = bt_comm

        self.blueprint = Blueprint("test", __name__, url_prefix="/test")

        self.blueprint.add_url_rule("/", view_func=self.test)

        self.blueprint.add_url_rule("/sidle", view_func=self.state_idle)
        self.blueprint.add_url_rule("/swait", view_func=self.wait_press)
        self.blueprint.add_url_rule("/confirm", view_func=self.confirm_press)
        self.blueprint.add_url_rule("/deny", view_func=self.deny_press)

        self.teams = [Team(name="BLUE", primary_color=Color(0, 0, 255), secondary_color=Color(0, 255, 255), bt_comm=self.__bt_comm,
                           point_limit=5),
                      Team(name="RED", primary_color=Color(255, 0, 0), secondary_color=Color(255, 255, 0), bt_comm=self.__bt_comm,
                           point_limit=5)]

        self.teams[0].associated_buzzers = [b"\x78\x1c\x3c\x2d\x57\x94"]
        self.teams[1].associated_buzzers = [b"\x6c\xc8\x40\x06\xbe\x2c"]
        self.state = State(self.teams, self.__bt_comm)

    async def test(self) -> Tuple[Response, int]:
        """Handles GET requests to the `/` route.

        Returns a simple JSON response indicating the backend is active.

        Returns:
            Tuple[Response, int]: A JSON response and HTTP status code 200.
        """

        ret = {}

        ret.update({"ping": [i.data[0] for i in await self.__bt_comm.commands.ping()]})
        ret.update({"clock": [{i.data[0]: int(i.data[1])} for i in await self.__bt_comm.commands.get_clock()]})

        ret.update({"LED nb": int((await self.__bt_comm.commands.get_led_number(ret["ping"][0]))[0].data[0])})

        return jsonify(ret), 200

    async def state_idle(self) -> Tuple[Response, int]:
        await self.state.set_idle()
        return jsonify({'__state': 'idle'}), 200

    async def wait_press(self) -> Tuple[Response, int]:
        await self.state.wait_press()
        return jsonify({'__state': 'waiting'}), 200

    async def confirm_press(self) -> Tuple[Response, int]:
        await self.state.confirm_press()
        return jsonify({'__state': 'confirmed'}), 200

    async def deny_press(self) -> Tuple[Response, int]:
        await self.state.deny_press()
        return jsonify({'__state': 'denied'}), 200

# TODO: Team selector
# TODO: proper interface
