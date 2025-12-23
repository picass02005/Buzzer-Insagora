# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import TYPE_CHECKING, List

from backend.Modules.LEDManager import LEDs
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

        cmd_id = await self.bt_comm.send_command(command=b"PING", target_mac=target_mac)

        await self.bt_comm.recv_poll.wait_for_polling(
            cmd_id,
            "PING",
            is_broadcast=self.bt_comm.is_broadcast(target_mac)
        )

        return self.bt_comm.recv_poll.get_object_by_cmd_id_and_cmd(cmd_id, "PING")

    async def get_clock(self, target_mac: bytes | str = None) -> List[RecvObject]:
        """
        Get the clock value and return responses
        :param target_mac: The MAC address to target, by default, it is the broadcast address
        :return: A list of responses
        """

        cmd_id = await self.bt_comm.send_command(command=b"GCLK", target_mac=target_mac)

        await self.bt_comm.recv_poll.wait_for_polling(
            cmd_id,
            "GCLK",
            is_broadcast=self.bt_comm.is_broadcast(target_mac)
        )

        return self.bt_comm.recv_poll.get_object_by_cmd_id_and_cmd(cmd_id, "GCLK")

    async def reset_clock(self, target_mac: bytes | str = None) -> None:
        """
        Reset the clock internal value
        :param target_mac: The MAC address to target, by default, it is the broadcast address
        :return: None
        """

        await self.bt_comm.send_command(command=b"RCLK", target_mac=target_mac)

    async def set_clock(self, new_clock: int, target_mac: bytes | str = None) -> None:
        """
        Set the clock internal value to new_clock if it is smaller than actual internal clock
        :param new_clock: The new clock value to set
        :param target_mac: The MAC address to target, by default, it is the broadcast address
        :return: None
        """

        i_new_clock = int(new_clock)

        assert 0 <= i_new_clock <= 9223372036854775807, "Clock must be in the range 0 - MAX_INT64"

        await self.bt_comm.send_command(command=b"SCLK", args=str(i_new_clock), target_mac=target_mac)


    async def automatic_set_clock(self, target_mac: bytes | str = None) -> bool:
        """
        Automatically synchronize all buzzer clocks
        For more information, check ACLK command in onboard documentation
        :param target_mac: The MAC address to target, by default, it is the broadcast address
        :return: A boolean indicating if it worked
        """

        cmd_id = await self.bt_comm.send_command(command=b"ACLK", target_mac=target_mac)

        await self.bt_comm.recv_poll.wait_for_polling(
            cmd_id,
            "ACLK",
            is_broadcast=False  # Even if this command is made by broadcast, only master will respond
        )

        return len(self.bt_comm.recv_poll.get_object_by_cmd_id_and_cmd(cmd_id, "ACLK")) == 1

    async def get_led_number(self, target_mac: bytes | str = None) -> List[RecvObject]:
        """
        Get number of LED installed on a buzzer
        :param target_mac: The MAC address to target, by default, it is the broadcast address
        :return: A list of responses
        """

        cmd_id = await self.bt_comm.send_command(command=b"GLED", target_mac=target_mac)

        await self.bt_comm.recv_poll.wait_for_polling(
            cmd_id,
            "GLED",
            is_broadcast=self.bt_comm.is_broadcast(target_mac)
        )

        return self.bt_comm.recv_poll.get_object_by_cmd_id_and_cmd(cmd_id, "GLED")

    async def set_leds(self, leds: LEDs, target_mac: bytes | str = None) -> None:
        """
        Set LEDs colors on a buzzer
        :param leds: The colors for each LED on the buzzer
        :param target_mac: The MAC address to target, by default, it is the broadcast address
        :return: None
        """

        await self.bt_comm.send_command(command=b"SLED", args=bytes(leds), target_mac=target_mac)
