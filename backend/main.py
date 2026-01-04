# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


import asyncio
import logging

from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.GUI.ServeGUI import ServeGUI

logging.basicConfig(
    level=logging.DEBUG,  # TODO: Set to INFO for prod
)


async def main() -> None:
    """Runs the main asyncio event loop.

    This is the entry point for the asynchronous program.
    """

    bt_comm = BluetoothCommunication()

    gui = ServeGUI(bt_comm)
    asyncio.create_task(gui.run())

    # TODO: Clean CLI / small GUI with flask


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()
