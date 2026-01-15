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
        self.blueprint.add_url_rule("/set_point_limit", view_func=self.set_point_limit, methods=['PATCH'])
        self.blueprint.add_url_rule("/reset_points", view_func=self.reset_points, methods=['PATCH'])
        self.blueprint.add_url_rule("/delete", view_func=self.delete_team, methods=['DELETE'])
        self.blueprint.add_url_rule("/change_name", view_func=self.change_team_name, methods=['PATCH'])
        self.blueprint.add_url_rule("/update", view_func=self.update_team, methods=['PATCH'])

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

        await self.__bt_comm.commands.clear_leds()

        return jsonify({"status": "ok"}), 200

    async def delete_team(self) -> Tuple[Response, int]:
        payload = await request.get_json()

        if "team_name" not in payload.keys():
            return jsonify({"error": f"You must define a field named team_name in the body"}), 400

        if payload["team_name"] not in [i.name for i in self.__teams]:
            return jsonify({"error": f"Team {payload["team_name"]} does not exist"}), 400

        self.__teams = [i for i in self.__teams if i.name != payload["team_name"]]

        return jsonify({"status": "ok"}), 200

    async def change_team_name(self) -> Tuple[Response, int]:
        payload = await request.get_json()

        for i in ["old_name", "new_name"]:
            if i not in payload.keys():
                return jsonify({"error": f"You must define a field named {i} in the body"}), 400

        team_names = [i.name for i in self.__teams]

        if payload["old_name"] not in team_names:
            return jsonify({"error": f"Team {payload["old_name"]} does not exist"}), 400

        if payload["new_name"] in team_names:
            return jsonify({"error": f"Team {payload["new_name"]} already exists"}), 400

        for i in self.__teams.copy():
            if i.name == payload["old_name"]:
                i.name = payload["new_name"]
                self.__teams.append(i)

                break

        self.__teams = [i for i in self.__teams if i.name != payload["old_name"]]

        return jsonify({"status": "ok"}), 200

    async def update_team(self) -> Tuple[Response, int]:
        payload = await request.get_json()

        if "team_name" not in payload.keys():
            return jsonify({"error": f"You must define a field named team_name in the body"}), 400

        team: Team | None = None

        for i in self.__teams:
            if payload["team_name"] == i.name:
                team = i
                break

        if team is None:
            return jsonify({"error": f"Team {payload["team_name"]} does not exist"}), 400

        if "associated_buzzers" in payload.keys():
            await self.__bt_comm.connected_cache.update_cache(force=False)
            connected = await self.__bt_comm.connected_cache.get_connected_str()

            for i in payload["associated_buzzers"]:
                for j in self.__teams:
                    if j.name != payload["team_name"] and i in j.associated_buzzers:
                        return jsonify({"error": f"Buzzer {i} is already associated to team {j.name}"}), 400

                    if i not in connected:
                        return jsonify({"error": f"Buzzer {i} is not connected"}), 400

            team.associated_buzzers = payload["associated_buzzers"]

        if "point" in payload.keys():
            if isinstance(payload["point"], int) and 0 <= payload["point"] <= team.point_limit:
                team.point = payload["point"]

            else:
                return jsonify({"error": f"Point must be an integer from 0 to point_limit ({team.point_limit})"}), 400

        if "primary_color" in payload.keys():
            if self.is_valid_hex_color(payload["primary_color"]):
                primary = Color().from_hex(payload["primary_color"])

            else:
                return jsonify({"error": f"Primary color must be a 6 character long hexadecimal number"}), 400

            team.primary_color = primary

        if "secondary_color" in payload.keys():
            if self.is_valid_hex_color(payload["secondary_color"]):
                secondary = Color().from_hex(payload["secondary_color"])

            else:
                return jsonify({"error": f"Secondary color must be a 6 character long hexadecimal number"}), 400

            team.secondary_color = secondary

        self.__teams = [i for i in self.__teams if i.name != payload["team_name"]]
        self.__teams.append(team)

        return jsonify({"status": "ok"}), 200

    # TODO: docstring
