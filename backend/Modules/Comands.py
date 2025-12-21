# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.Modules.BluetoothCommunication import BluetoothCommunication


class Commands:
    """
    Class used to make commands via BLE communication
    """

    def __init__(self, bt_comm: BluetoothCommunication):
        self.bt_comm: BluetoothCommunication = bt_comm

    async def ping(self, target_mac: bytes | str = None):
        cmd_id = await self.bt_comm.send_command(command="PING", target_mac=target_mac)

        print(cmd_id, "TODO")  # TODO: Command polling for responses + docstring
