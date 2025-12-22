# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
from typing import TYPE_CHECKING, List

from backend.Modules.RecvPolling import RecvObject

if TYPE_CHECKING:
    from backend.Modules.BluetoothCommunication import BluetoothCommunication


class Commands:
    """
    Class used to make commands via BLE communication
    """

    def __init__(self, bt_comm: BluetoothCommunication) -> None:
        self.bt_comm: BluetoothCommunication = bt_comm

    async def ping(self, target_mac: bytes | str = None) -> List[RecvObject]:
        """
        Performs a ping and return responses
        :param target_mac: The MAC address to target, by default, it is the broadcast address
        :return: A list of responses
        """

        cmd_id = await self.bt_comm.send_command(command="PING", target_mac=target_mac)

        await self.bt_comm.recv_poll.wait_for_polling(
            cmd_id,
            "PING",
            is_broadcast=self.bt_comm.is_broadcast(target_mac)
        )

        return self.bt_comm.recv_poll.get_object_by_cmd_id_and_cmd(cmd_id, "PING")
