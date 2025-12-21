# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


import asyncio
import logging

from backend.Modules.BluetoothCommunication import BluetoothCommunication

logging.basicConfig(
    level=logging.DEBUG,  # TODO: Set to INFO for prod
)

async def main() -> None:
    """
    Main event loop for asyncio
    :return: None
    """

    bt_comm = BluetoothCommunication()

    await bt_comm.connect_oneshot()

    await bt_comm.send_command("ACLK")
    await asyncio.sleep(0.1)
    await bt_comm.send_command("SLED", b"\x00\x0f\x0f\x0f\x0f\x00"*4)
    await bt_comm.send_command("GCLK")

    while True:
        await asyncio.sleep(1)

    # TODO: Clean CLI / small GUI with flask


if __name__ == "__main__":
    asyncio.run(main())
