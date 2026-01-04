# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import logging
import time
from typing import List, TYPE_CHECKING

from backend.ESPCommunication.RecvPool import RecvObject

if TYPE_CHECKING:
    from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication

logger = logging.getLogger(__name__)


class ConnectedCache:
    def __init__(self, bt_comm: BluetoothCommunication, expires_after: int = 10) -> None:
        self.bt_comm: BluetoothCommunication = bt_comm
        self.expires_after: int = expires_after

        self.next_poll: int = 0

        self.__connected: List[str] = []

    async def update_cache(self, force: bool = False) -> None:
        if not force and self.next_poll > time.time():
            return

        logging.debug("Updating connected cache")

        ret: List[RecvObject] = await self.bt_comm.commands.ping(target_mac=b"\xFF\xFF\xFF\xFF\xFF\xFF")

        self.__connected = [i.data[0] for i in ret]
        self.next_poll = int(time.time() + self.expires_after)

    async def get_connected_str(self) -> List[str]:
        await self.update_cache()

        return self.__connected

    async def get_connected_bytes(self) -> List[bytes]:
        await self.update_cache()

        return [self.bt_comm.target_mac_formatter(i) for i in self.__connected]
