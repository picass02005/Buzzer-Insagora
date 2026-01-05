# Copyright (c) 2026 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import List, Tuple, Dict, Any

from quart import Blueprint, Response, jsonify, request

from backend.BuzzerLogic.Constants import LED_NB
from backend.BuzzerLogic.State import State
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication


class ApiCheck:
    def __init__(self, bt_comm: BluetoothCommunication, teams: List[Team], state: State):
        self.__bt_comm: BluetoothCommunication = bt_comm
        self.__teams: List[Team] = teams
        self.__state: State = state

        self.blueprint = Blueprint("api/check", __name__, url_prefix="/api/check")

        self.blueprint.add_url_rule("/led_nb", view_func=self.check_led_nb)

    async def check_led_nb(self) -> Tuple[Response, int]:
        ret: Dict[str, Any] = {'config': LED_NB}
        err = False

        for i in await self.__bt_comm.commands.get_led_number(target_mac=b"\xff\xff\xff\xff\xff\xff"):
            print(i)
            if int(i.data[0]) != LED_NB:
                err = True

        if err:
            ret.update({'status': 'One of the buzzer does not have the correct number of LEDs'})

            return jsonify(ret), 200

        else:
            ret.update({'status': 'OK'})

            return jsonify(ret), 500
