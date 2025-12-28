# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import TYPE_CHECKING, List

from backend.ESPCommunication.LEDManager import LEDs
from backend.ESPCommunication.RecvPool import RecvObject

if TYPE_CHECKING:
    from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication


class Commands:
    """Provides methods to send commands to buzzers via BLE communication.

    Each method sends a specific command using the BluetoothCommunication instance.
    """

    def __init__(self, bt_comm: BluetoothCommunication) -> None:
        """Initializes a Commands instance.

        Args:
            bt_comm (BluetoothCommunication): The Bluetooth communication instance used to send commands.
        """

        self.bt_comm: BluetoothCommunication = bt_comm

    async def ping(self, target_mac: bytes | str = None) -> List[RecvObject]:
        """Performs a ping command and returns the responses.

        Args:
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.

        Returns:
            List[RecvObject]: List of responses from the buzzer(s).
        """

        cmd_id = await self.bt_comm.send_command(command=b"PING", target_mac=target_mac)

        await self.bt_comm.recv_pool.wait_for_responses(
            cmd_id,
            "PING",
            is_broadcast=self.bt_comm.is_broadcast(target_mac)
        )

        return self.bt_comm.recv_pool.get_object_by_cmd_id_and_cmd(cmd_id, "PING")

    async def get_clock(self, target_mac: bytes | str = None) -> List[RecvObject]:
        """Retrieves the internal clock value from the buzzer(s).

        Args:
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.

        Returns:
            List[RecvObject]: List of responses containing clock values.
        """

        cmd_id = await self.bt_comm.send_command(command=b"GCLK", target_mac=target_mac)

        await self.bt_comm.recv_pool.wait_for_responses(
            cmd_id,
            "GCLK",
            is_broadcast=self.bt_comm.is_broadcast(target_mac)
        )

        return self.bt_comm.recv_pool.get_object_by_cmd_id_and_cmd(cmd_id, "GCLK")

    async def reset_clock(self, target_mac: bytes | str = None) -> None:
        """Resets the internal clock on the buzzer(s).

        Args:
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.
        """

        await self.bt_comm.send_command(command=b"RCLK", target_mac=target_mac)

    async def set_clock(self, new_clock: int, target_mac: bytes | str = None) -> None:
        """Sets the internal clock to a new value if it is smaller than the current value.

        Args:
            new_clock (int): New clock value to set.
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.

        Raises:
            AssertionError: If `new_clock` is outside the valid range 0–MAX_INT64.
        """

        i_new_clock = int(new_clock)

        assert 0 <= i_new_clock <= 9223372036854775807, "Clock must be in the range 0 - MAX_INT64"

        await self.bt_comm.send_command(command=b"SCLK", args=str(i_new_clock), target_mac=target_mac)

    async def automatic_set_clock(self, target_mac: bytes | str = None) -> bool:
        """Automatically synchronizes all buzzer clocks.

        Args:
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.

        Returns:
            bool: True if synchronization was successful (master buzzer responded), False otherwise.
        """

        cmd_id = await self.bt_comm.send_command(command=b"ACLK", target_mac=target_mac)

        await self.bt_comm.recv_pool.wait_for_responses(
            cmd_id,
            "ACLK",
            is_broadcast=False  # Even if this command is made by broadcast, only master will respond
        )

        return len(self.bt_comm.recv_pool.get_object_by_cmd_id_and_cmd(cmd_id, "ACLK")) == 1

    async def get_led_number(self, target_mac: bytes | str = None) -> List[RecvObject]:
        """Retrieves the number of LEDs installed on the buzzer(s).

        Args:
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.

        Returns:
            List[RecvObject]: Responses containing the number of LEDs.
        """

        cmd_id = await self.bt_comm.send_command(command=b"GLED", target_mac=target_mac)

        await self.bt_comm.recv_pool.wait_for_responses(
            cmd_id,
            "GLED",
            is_broadcast=self.bt_comm.is_broadcast(target_mac)
        )

        return self.bt_comm.recv_pool.get_object_by_cmd_id_and_cmd(cmd_id, "GLED")

    async def set_leds(self, leds: LEDs, target_mac: bytes | str = None) -> None:
        """Sets the colors of LEDs on the buzzer(s).

        Args:
            leds (LEDs): LED colors to set.
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.
        """

        await self.bt_comm.send_command(command=b"SLED", args=bytes(leds), target_mac=target_mac)

    async def clear_leds(self, target_mac: bytes | str = None) -> None:
        """Clears all LEDs on the buzzer(s).

        Args:
            target_mac (bytes | str, optional): MAC address to target. Defaults to broadcast.
        """

        await self.bt_comm.send_command(command=b"CLED", target_mac=target_mac)
