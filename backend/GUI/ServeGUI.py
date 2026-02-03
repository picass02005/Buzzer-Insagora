# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import json
import logging
import pathlib
import webbrowser
from typing import List

import quart
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart

from backend.BuzzerLogic.State import State
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.GUI.API.Check import ApiCheck
from backend.GUI.API.Flow import ApiFlow
from backend.GUI.API.Light import ApiLights
from backend.GUI.API.Status import ApiStatus
from backend.GUI.API.Teams import ApiTeams

logger = logging.getLogger(__name__)


class ServeGUI:
    """Manages and serves the Quart GUI application for BLE communication.

    This class is responsible for loading configuration, initializing the
    Quart app, registering routes, and running the ASGI server using Hypercorn.

    Attributes:
        quart_app (Quart): The Quart application instance.
        __teams (List[Team]): Unordered list of __teams participating in the current game session.
        __buzz_state (State): Central game __state manager responsible for tracking
            the current game phase (IDLE, WAIT, CHECK), controlling team LEDs,
            and handling buzzer input validation (confirmation or rejection).
        __bt_comm (BluetoothCommunication): Instance of BluetoothCommunication used by routes.
        __bind (List[str]): List of addresses and ports to bind the server to.
    """

    def __init__(self, bt_comm: BluetoothCommunication) -> None:
        """Initializes the ServeGUI instance.

        Args:
            bt_comm (BluetoothCommunication): The Bluetooth communication instance
                to be used by GUI routes.
        """

        self.quart_app: Quart = Quart(__name__)

        self.__bt_comm: BluetoothCommunication = bt_comm
        self.__state: State = State(self.__bt_comm)
        self.__bind: List[str] = []

        self.__load_config()

    def __load_config(self) -> None:
        """Loads configuration from `backend-config.json` into class attributes.

        Raises:
            ValueError: If any required key is missing in the configuration.
        """

        with open(f"{pathlib.Path(__file__).resolve().parent.parent}/backend-config.json", "r") as f:
            config = json.loads(f.read())

        if "Webpage" not in config.keys():
            raise ValueError(f"Value Webpage not defined in backend-config")

        for i in ["Bind"]:
            if i not in config["Webpage"].keys():
                raise ValueError(f"Value Webpage/{i} not defined in backend-config")

        self.__bind = config["Webpage"]["Bind"]

    async def run(self) -> None:
        """Runs the Quart application with Hypercorn.

        This method:
        - Instantiates route classes and registers their blueprints.
        - Configures the Hypercorn server with the bind addresses from configuration.
        - Starts the Quart app asynchronously using Hypercorn.
        """

        static_bp = quart.Blueprint(
            "static",
            __name__,
            static_folder="static",
            static_url_path="/"
        )

        self.quart_app.register_blueprint(static_bp)

        status_class = ApiStatus(self.__bt_comm, self.__state)
        self.quart_app.register_blueprint(status_class.blueprint)

        check_class = ApiCheck(self.__bt_comm, self.__state)
        self.quart_app.register_blueprint(check_class.blueprint)

        teams_class = ApiTeams(self.__bt_comm, self.__state)
        self.quart_app.register_blueprint(teams_class.blueprint)

        lights_class = ApiLights(self.__bt_comm, self.__state)
        self.quart_app.register_blueprint(lights_class.blueprint)

        flow_class = ApiFlow(self.__bt_comm, self.__state)
        self.quart_app.register_blueprint(flow_class.blueprint)

        config = Config()
        config.bind = self.__bind
        config.shutdown_timeout = 10

        logger.info(f"Opening url http://{self.__bind[0]}/index.html")
        webbrowser.open_new(f"http://{self.__bind[0]}/index.html")

        logger.info(f"Serving backend on {' '.join([f"http://{i}" for i in self.__bind])}")

        await serve(self.quart_app, config)
