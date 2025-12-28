import json
import logging
import pathlib
from typing import List

from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart

from backend.GUI.Routes.Test import test_bp

logger = logging.getLogger(__name__)


class ServeGUI:
    def __init__(self) -> None:
        self.quart_app: Quart = Quart(__name__)

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

    async def run(self):
        self.quart_app.register_blueprint(test_bp)

        config = Config()
        config.bind = self.__bind

        await serve(self.quart_app, config)
