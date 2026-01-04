# Copyright (c) 2026 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import List, Tuple, Dict

from quart import Blueprint, Response, jsonify, request

from backend.BuzzerLogic.State import State
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication


class ApiStatus:
    def __init__(self, bt_comm: BluetoothCommunication, teams: List[Team], state: State):
        self.__bt_comm: BluetoothCommunication = bt_comm
        self.__teams: List[Team] = teams
        self.__state: State = state

        self.blueprint = Blueprint("api/status", __name__, url_prefix="/api/status")

        self.blueprint.add_url_rule("/get_connected", view_func=self.get_connected)
        self.blueprint.add_url_rule("/get_status", view_func=self.get_status)
        self.blueprint.add_url_rule("/get_teams", view_func=self.get_teams)

    async def get_connected(self) -> Tuple[Response, int]:
        no_cache: bool = request.args.get("no_cache", default="false").lower() in ['1', 'true']

        connected = []

        if self.__bt_comm.client is not None:
            if no_cache:
                await self.__bt_comm.connected_cache.update_cache(force=True)

            connected = await self.__bt_comm.connected_cache.get_connected_str()

        return jsonify({'connected': connected}), 200

    async def get_status(self) -> Tuple[Response, int]:
        return jsonify({'state': str(self.__state.current_state).split(".")[1]}), 200

    async def get_teams(self) -> Tuple[Response, int]:
        teams: Dict[str, any] = {}

        for i in self.__teams:
            teams.update({i.name: {
                'name': i.name,
                'point': i.point,
                'point_limit': i.point_limit,
                'primary_color': i.primary_color.to_str_value(),
                'secondary_color': i.secondary_color.to_str_value(),
                'associated_buzzers': [self.__bt_comm.mac_to_str(j) for j in i.associated_buzzers]
            }})

        return jsonify(teams), 200
