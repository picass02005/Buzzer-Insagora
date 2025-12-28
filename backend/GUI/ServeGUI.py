import json
import logging
import pathlib
from typing import List

from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart

from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.GUI.Routes.Test import Test

logger = logging.getLogger(__name__)


class ServeGUI:
    """Manages and serves the Quart GUI application for BLE communication.

    This class is responsible for loading configuration, initializing the
    Quart app, registering routes, and running the ASGI server using Hypercorn.

    Attributes:
        quart_app (Quart): The Quart application instance.
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

        test_class = Test(self.__bt_comm)
        self.quart_app.register_blueprint(test_class.blueprint)

        config = Config()
        config.bind = self.__bind
        config.shutdown_timeout = 0.25

        await serve(self.quart_app, config)
