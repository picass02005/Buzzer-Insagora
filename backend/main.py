# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


import asyncio
import logging

from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.ESPCommunication.LEDManager import LEDs, Color
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

    await bt_comm.connect()

    print(await bt_comm.commands.automatic_set_clock())

    l = LEDs(8)
    l.leds[0] = Color(15, 0, 0)
    l.leds[1] = Color(15, 15, 0)
    l.leds[2] = Color(0, 15, 0)
    l.leds[3] = Color(0, 15, 15)
    l.leds[4] = Color(0, 0, 15)
    l.leds[5] = Color(15, 0, 15)
    l.leds[6] = Color(15, 0, 0)
    l.leds[7] = Color(15, 15, 15)

    await bt_comm.commands.set_leds(l)

    print(await bt_comm.commands.get_clock())

    print(await bt_comm.commands.ping())
    print(await bt_comm.commands.ping(target_mac="78:1C:3C:2D:57:94"))

    print(await bt_comm.commands.get_led_number())

    for i in range(10):
        print(i, await bt_comm.but_callback.get_first_press())
        await asyncio.sleep(1)

    # TODO: Clean CLI / small GUI with flask


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()
