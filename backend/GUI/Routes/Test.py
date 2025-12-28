# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import Tuple

from quart import Blueprint, jsonify, Response

from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication


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

        self.blueprint = Blueprint("test", __name__, url_prefix="/")

        self.blueprint.add_url_rule("/", view_func=self.test)

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
