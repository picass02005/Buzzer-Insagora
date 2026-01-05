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
    """API endpoints exposing current system status.

    This class defines a Quart Blueprint that provides read-only HTTP
    endpoints for retrieving information about:
    - Connected Bluetooth devices
    - Current application state
    - Registered teams and their properties

    Attributes:
        __bt_comm (BluetoothCommunication):
            Bluetooth communication handler used to query connected devices
            and manage the connection cache.

        __teams (List[Team]):
            List of teams currently registered in the system. Each team
            contains scoring information, color configuration, and
            associated buzzer MAC addresses.

        __state (State):
            Global application state container representing the current
            state of the application.

        blueprint (Blueprint):
            Quart Blueprint exposing status-related API endpoints.
            All routes are prefixed with ``/api/status``.
    """

    def __init__(self, bt_comm: BluetoothCommunication, teams: List[Team], state: State):
        """Initialize the status API and register routes.

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

        self.blueprint = Blueprint("api_status", __name__, url_prefix="/api/status")

        self.blueprint.add_url_rule("/get_connected", view_func=self.get_connected, methods=['GET'])
        self.blueprint.add_url_rule("/get_state", view_func=self.get_state, methods=['GET'])
        self.blueprint.add_url_rule("/get_teams", view_func=self.get_teams, methods=['GET'])

    async def get_connected(self) -> Tuple[Response, int]:
        """Get currently connected Bluetooth devices.

        Query Parameters:
            no_cache (bool, optional):
                If ``true`` or ``1``, forces a refresh of the Bluetooth
                connection cache before returning results.

        Returns:
            Tuple[Response, int]:
                JSON response containing connected device identifiers.
        """

        no_cache: bool = request.args.get("no_cache", default="false").lower() in ['1', 'true']

        connected = []

        if self.__bt_comm.client is not None:
            if no_cache:
                await self.__bt_comm.connected_cache.update_cache(force=True)

            connected = await self.__bt_comm.connected_cache.get_connected_str()

        return jsonify({'connected': connected}), 200

    async def get_state(self) -> Tuple[Response, int]:
        """Get the current application state.

        Returns:
            Tuple[Response, int]:
                A JSON response containing the current state name
                and an HTTP status code.

        Response JSON:
            {
                "state": "IDLE"
            }
        """

        return jsonify({'state': str(self.__state.current_state).split(".")[1]}), 200

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
