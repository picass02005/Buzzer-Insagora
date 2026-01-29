# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


import asyncio
import contextlib
import logging

from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.GUI.ServeGUI import ServeGUI

logging.basicConfig(
    level=logging.INFO,
)


async def main() -> None:
    """Runs the main asyncio event loop.

    This is the entry point for the asynchronous program.
    """

    bt_comm = BluetoothCommunication()

    gui = ServeGUI(bt_comm)

    ble_task = asyncio.create_task(bt_comm.connect_until_complete())

    try:
        await gui.run()

    finally:
        ble_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await ble_task

    # TODO: Clean CLI / small GUI with flask


if __name__ == "__main__":
    asyncio.run(main())
