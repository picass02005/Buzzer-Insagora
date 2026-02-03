# Copyright (c) 2026 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
import re
from typing import Tuple

from quart import Blueprint, Response, jsonify, request

from backend.BuzzerLogic.Constants import LED_NB
from backend.BuzzerLogic.State import State
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.ESPCommunication.LEDManager import Color, LEDs

HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


class ApiLights:
    def __init__(self, bt_comm: BluetoothCommunication, state: State):
        """Initialize the lights API and register routes.

        Args:
            bt_comm (BluetoothCommunication):
                Bluetooth communication handler used to query connected devices.
            state (State):
                Global application state container.
        """

        self.__bt_comm: BluetoothCommunication = bt_comm
        self.__state: State = state

        self.blueprint = Blueprint("api_lights", __name__, url_prefix="/api/lights")

        self.blueprint.add_url_rule("/reset_led_default", view_func=self.reset_led_default, methods=['PUT'])
        self.blueprint.add_url_rule("/get_led_nb", view_func=self.get_led_nb, methods=['GET'])
        self.blueprint.add_url_rule("/set_led_color", view_func=self.set_led_color, methods=['PUT'])
        self.blueprint.add_url_rule("/clear_leds", view_func=self.clear_leds, methods=['PUT'])

    async def reset_led_default(self) -> Tuple[Response, int]:
        """Reset LEDs to the default application-controlled state.

        This restores LED behavior to be managed by the global application
        state, typically reflecting team colors or game state.

        Returns:
            Tuple[Response, int]:
                A JSON response indicating success, and an HTTP status code.
        """

        await self.__state.set_led_on_state()

        return jsonify({"status": "ok"}), 200

    @staticmethod
    async def get_led_nb() -> Tuple[Response, int]:
        """Get the total number of LEDs per device.

        Returns:
            Tuple[Response, int]:
                A JSON response containing the number of LEDs, and an HTTP
                status code.

        Response JSON:
            {
                "number": 16
            }
        """

        return jsonify({'number': LED_NB}), 200

    async def set_led_color(self) -> Tuple[Response, int]:
        """Set the color of each LED for a specific device or all devices.

        If no target MAC address is provided, the command is broadcast to
        all connected devices.

        Returns:
            Tuple[Response, int]:
                A JSON response indicating success or failure, and an HTTP
                status code.

        Request JSON:
            {
                "target_mac": "AA:BB:CC:DD:EE:FF",  # Optional
                "colors": [
                    "FF0000",
                    "00FF00",
                    "0000FF",
                    ...
                ]
            }
        """

        payload = await request.get_json()

        if "target_mac" not in payload.keys():
            mac = b"\xFF\xFF\xFF\xFF\xFF\xFF"

        else:
            try:
                mac = self.__bt_comm.target_mac_formatter(payload["target_mac"])
            except AssertionError, TypeError:
                return jsonify({"error": f"Target MAC isn't properly formatted"}), 400

        if "colors" not in payload.keys():
            return jsonify({"error": f"You must define a field named colors containing the color of each LED"}), 400

        if len(payload["colors"]) != LED_NB:
            return jsonify({"error": f"You must define a field named colors containing the color of each LED"}), 400

        leds = LEDs(LED_NB)

        try:
            leds.leds = [Color().from_hex(i) for i in payload["colors"]]

        except AssertionError, ValueError:
            return jsonify({"error": f"Each LED color must be a 6 characters long hexadecimal as RRGGBB"}), 400

        await self.__bt_comm.commands.set_leds(leds, mac)

        return jsonify({"status": "ok"}), 200

    async def clear_leds(self) -> Tuple[Response, int]:
        """Clear (turn off) all LEDs for a specific device or all devices.

        If no target MAC address is provided, the clear command is broadcast
        to all connected devices.

        Returns:
            Tuple[Response, int]:
                A JSON response indicating success or failure, and an HTTP
                status code.

        Request JSON:
            {
                "target_mac": "AA:BB:CC:DD:EE:FF"  # Optional
            }
        """

        payload = await request.get_json()

        if payload is None or "target_mac" not in payload.keys():
            mac = b"\xFF\xFF\xFF\xFF\xFF\xFF"

        else:
            try:
                mac = self.__bt_comm.target_mac_formatter(payload["target_mac"])
            except AssertionError, TypeError:
                return jsonify({"error": f"Target MAC isn't properly formatted"}), 400

        await self.__bt_comm.commands.clear_leds(mac)

        return jsonify({"status": "ok"}), 200
