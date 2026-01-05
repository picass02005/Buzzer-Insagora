# Copyright (c) 2026 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import List, Tuple, Dict, Any

from quart import Blueprint, Response, jsonify

from backend.BuzzerLogic.Constants import LED_NB
from backend.BuzzerLogic.State import State
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication


class ApiCheck:
    """API endpoints used for system consistency and hardware checks.

    This class exposes diagnostic endpoints used to verify that the
    Bluetooth-connected buzzers are correctly configured. Currently,
    it provides an endpoint for validating the number of LEDs configured
    on each connected buzzer.

    Attributes:
        __bt_comm (BluetoothCommunication):
            Bluetooth communication handler used to send commands to
            connected buzzers and retrieve their configuration.

        __teams (List[Team]):
            List of teams currently registered in the system.
            This attribute is stored for consistency with other API
            classes, even if not directly used by this class.

        __state (State):
            Global application state container.
            This attribute is stored for consistency with other API
            classes, even if not directly used by this class.

        blueprint (Blueprint):
            Quart Blueprint exposing check-related API endpoints.
            All routes are prefixed with ``/api/check``.
    """

    def __init__(self, bt_comm: BluetoothCommunication, teams: List[Team], state: State):
        """Initialize the check API and register routes.

        Args:
            bt_comm (BluetoothCommunication):
                Bluetooth communication handler used to communicate
                with connected buzzers.
            teams (List[Team]):
                List of teams currently registered in the system.
            state (State):
                Global application state container.
        """

        self.__bt_comm: BluetoothCommunication = bt_comm
        self.__teams: List[Team] = teams
        self.__state: State = state

        self.blueprint = Blueprint("api_check", __name__, url_prefix="/api/check")

        self.blueprint.add_url_rule("/led_nb", view_func=self.check_led_nb, methods=['GET'])

    async def check_led_nb(self) -> Tuple[Response, int]:
        """Verify the number of LEDs configured on each connected buzzer.

        This endpoint queries all connected buzzers using a broadcast
        Bluetooth MAC address and validates that each device reports
        the expected number of LEDs.

        Returns:
            Tuple[Response, int]:
                A JSON response containing the expected LED configuration
                and a status message, along with an HTTP status code.

        Response JSON:
            {
                "config": 12,
                "status": "OK"
            }

        Notes:
            - A broadcast MAC address (FF:FF:FF:FF:FF:FF) is used to query
              all connected devices.
            - If **any inconsistency** is detected (i.e. at least one buzzer
              reports an unexpected number of LEDs), the endpoint returns
              **HTTP 500**.
            - If all buzzers report the expected LED count, the endpoint
              returns **HTTP 200**.
        """

        ret: Dict[str, Any] = {'config': LED_NB}
        err = False

        for i in await self.__bt_comm.commands.get_led_number(target_mac=b"\xff\xff\xff\xff\xff\xff"):
            print(i)
            if int(i.data[0]) != LED_NB:
                err = True

        if err:
            ret.update({'status': 'One of the buzzer does not have the correct number of LEDs'})

            return jsonify(ret), 500

        else:
            ret.update({'status': 'OK'})

            return jsonify(ret), 200
