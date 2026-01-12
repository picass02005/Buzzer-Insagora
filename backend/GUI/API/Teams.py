# Copyright (c) 2026 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import re
from typing import List, Tuple, Dict, Literal, cast

from quart import Blueprint, Response, jsonify, request

from backend.BuzzerLogic.State import State
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.ESPCommunication.LEDManager import Color

HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


class ApiTeams:
    def __init__(self, bt_comm: BluetoothCommunication, teams: List[Team], state: State):
        """Initialize the teams API and register routes.

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

        self.blueprint = Blueprint("api_teams", __name__, url_prefix="/api/teams")

        self.blueprint.add_url_rule("/get", view_func=self.get_teams, methods=['GET'])
        self.blueprint.add_url_rule("/make", view_func=self.make_team, methods=['POST'])
        self.blueprint.add_url_rule("/set_point_limit", view_func=self.set_point_limit, methods=['POST'])
        self.blueprint.add_url_rule("/reset_points", view_func=self.reset_points, methods=['POST'])

    async def get_teams(self) -> Tuple[Response, int]:
        """Get all registered teams and their properties.

        Returns:
            Tuple[Response, int]:
                A JSON response mapping team names to their details
                and an HTTP status code.

        Response JSON:
            {
                "Team A": {
                    "name": "Team A",
                    "point": 10,
                    "point_limit": 50,
                    "primary_color": "#FF0000",
                    "secondary_color": "#FFFFFF",
                    "associated_buzzers": [
                        "AA:BB:CC:DD:EE:FF"
                    ]
                }
            }
        """

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

    @staticmethod
    def is_valid_hex_color(value: str) -> bool:
        return bool(HEX_COLOR_RE.match(value))

    async def make_team(self) -> Tuple[Response, int]:
        payload = await request.get_json()

        for i in ["team_name", "primary_color", "secondary_color"]:
            if i not in payload.keys():
                return jsonify({"error": f"You must define a field named {i} in the body"}), 400

        for i in ["primary_color", "secondary_color"]:
            if not self.is_valid_hex_color(payload[i]):
                return jsonify({"error": f"{i} must be given in #RRGGBB form"}), 400

        if payload["team_name"] in [i.name for i in self.__teams]:
            return jsonify({"error": f"Team {payload["team_name"]} already exists"}), 400

        team_name: str = str(payload["team_name"])
        primary_color: Color = Color().from_hex(payload["primary_color"].lstrip("#"))
        secondary_color: Color = Color().from_hex(payload["secondary_color"].lstrip("#"))

        if len(self.__teams) == 0:
            point_limit: Literal[5, 8, 10, 16] = 8

        else:
            point_limit: Literal[5, 8, 10, 16] = self.__teams[0].point_limit

        team = Team(name=team_name, primary_color=primary_color, secondary_color=secondary_color,
                    bt_comm=self.__bt_comm, point_limit=point_limit)
        self.__teams.append(team)

        return jsonify({"status": "ok"}), 200

    async def set_point_limit(self):
        payload = await request.get_json()

        if "limit" not in payload.keys():
            return jsonify({"error": f"You must define a field named limit in the body"}), 400

        if payload["limit"] not in [5, 8, 10, 16]:
            return jsonify({"error": f"Valid limits are 5, 8, 10 or 16"}), 400

        limit: Literal[5, 8, 10, 16] = cast(Literal[5, 8, 10, 16], payload["limit"])

        for i in self.__teams:
            i.point_limit = limit

        return jsonify({"status": "ok"}), 200

    async def reset_points(self):
        for i in self.__teams:
            i.point = 0

        return jsonify({"status": "ok"}), 200

    # TODO: register buzzer
    # TODO: remove team
    # TODO: update team

    # TODO: docstring
