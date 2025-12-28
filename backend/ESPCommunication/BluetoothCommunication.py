# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import asyncio
import json
import logging
import pathlib
import time

from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic

from backend.ESPCommunication.ButtonCallback import ButtonCallback
from backend.ESPCommunication.Comands import Commands
from backend.ESPCommunication.RecvPool import RecvPool, RecvObject

logger = logging.getLogger(__name__)


class BluetoothCommunication:
    """Handles communication with buzzers over BLE.

    Provides methods to connect, send commands, and receive packets from BLE buzzers.

    Attributes:
        SERVICE_UUID (str): UUID of the BLE service used by buzzers.
        CHARACTERISTIC_UUID (str): UUID of the BLE service used by buzzers.
        TARGET_NAME (str): Name of the BLE device to connect to.
        client (BleakClient or None): BLE client instance when connected, None otherwise.
        commands (Commands): Commands object for sending commands to buzzers.
        but_callback (ButtonCallback): Callback handler for button press events received from buzzers.
            Responsible for processing and deduplicating button press notifications.
        recv_pool (RecvPool): Pool for storing received packets.
        __cmd_id (int): Command ID counter (0–255) for outgoing commands.
        __cmd_id_lock (asyncio.Lock): Lock to prevent race conditions when incrementing __cmd_id.
    """

    def __init__(self) -> None:
        """Initializes a BluetoothCommunication instance.

        Loads configuration from `backend-config.json` and sets attributes accordingly.
        """

        self.SERVICE_UUID: str = ""
        self.CHARACTERISTIC_UUID: str = ""
        self.TARGET_NAME: str = ""

        self.client: None | BleakClient = None

        self.commands: Commands = Commands(self)
        self.but_callback: ButtonCallback = ButtonCallback(self)

        self.recv_pool: RecvPool = RecvPool()

        self.__cmd_id: int = 0
        self.__cmd_id_lock: asyncio.Lock = asyncio.Lock()

        self.__load_config()

    def __load_config(self) -> None:
        """Loads configuration from `backend-config.json` into class attributes.

        Raises:
            ValueError: If any required key is missing in the configuration.
        """

        with open(f"{pathlib.Path(__file__).resolve().parent.parent}/backend-config.json", "r") as f:
            config = json.loads(f.read())

        for i in ["Service_UUID", "Characteristic_UUID", "BT_target_name"]:
            if i not in config.keys():
                raise ValueError(f"Value {i} not defined in backend-config")

        self.SERVICE_UUID = config["Service_UUID"]
        self.CHARACTERISTIC_UUID = config["Characteristic_UUID"]
        self.TARGET_NAME = config["BT_target_name"]

    async def connect(self) -> bool:
        """Attempts to connect to a buzzer via BLE.

        Discovers nearby devices, selects the target by name, and establishes a BLE connection.
        Also attaches a notification handler to the buzzer characteristic.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """

        logger.info("Discovering BLE devices...")

        devices = await BleakScanner.discover(timeout=5.0)

        target = None
        for d in devices:
            logger.debug(f"Discovered device : {d.name} - {d.address}")
            if d.name == self.TARGET_NAME:
                target = d

        if target is None:
            logger.error("Buzzer not found")
            return False

        logger.info(f"\nConnecting to {target.name} ({target.address})...")

        self.client = BleakClient(
            address_or_ble_device=target,
            disconnected_callback=self.on_disconnect
        )

        await self.client.connect()

        i = 0
        while i < 20 and self.client is None:
            await asyncio.sleep(0.1)
            i += 1

        if self.client is None or not self.client.is_connected:
            logger.error("Couldn't connect to buzzer")
            return False

        logger.debug("Attaching notifications handler")
        await self.client.start_notify(self.CHARACTERISTIC_UUID, self.on_notification)

        logger.info("Buzzer connected")

        await asyncio.sleep(0.1)  # Ensure BT stack is properly initialized

        return True

    async def send_command(self, command: bytes | str, args: bytes | str = b"", target_mac: bytes | str = None) -> int:
        """Sends a command to one or more buzzers.

        Formats the command and arguments, applies target MAC addressing (broadcast if None),
        and writes the command to the BLE characteristic.

        Args:
            command (bytes | str): Command to send.
            args (bytes | str, optional): Arguments for the command, defaults to empty bytes.
            target_mac (bytes | str | None, optional): Target MAC address for the command.
                Defaults to broadcast (None). Acceptable formats:
                - b"\x00\x11\x22\x33\x44\x55"
                - "00:11:22:33:44:55"

        Raises:
            AssertionError: If MAC format or value is invalid.
            TypeError: If `command` or `args` are not of type bytes or str.

        Returns:
            int: ID of the sent command.
        """

        target_mac_format = self.target_mac_formatter(target_mac)

        if isinstance(command, bytes):
            command_format = command

        elif isinstance(command, str):
            command_format = command.encode()

        else:
            raise TypeError("Command should be a str or a bytes object")

        if isinstance(args, bytes):
            args_format = args

        elif isinstance(args, str):
            args_format = args.encode()

        else:
            raise TypeError("Args should be a str or a bytes object")

        async with self.__cmd_id_lock:  # Lock other coroutine from accessing this critical section
            cmd_id = self.__cmd_id

            if 0 <= self.__cmd_id < 255:
                self.__cmd_id += 1

            else:
                self.__cmd_id = 0

        if len(args_format):
            msg_b = target_mac_format + cmd_id.to_bytes(signed=False) + command_format + b" " + args_format

        else:
            msg_b = target_mac_format + cmd_id.to_bytes(signed=False) + command_format

        logger.debug(
            f"SEND: To {':'.join([format(i, "02X") for i in target_mac_format])} command {command_format} with args "
            f"{args_format}"
        )

        await self.client.write_gatt_char(self.CHARACTERISTIC_UUID, msg_b, response=False)

        return cmd_id

    @staticmethod
    def target_mac_formatter(target_mac: bytes | str | None) -> bytes:
        """Formats a target MAC address into bytes suitable for BLE communication.

        Args:
            target_mac (bytes | str | None): Target MAC address. If None, uses broadcast.

        Raises:
            AssertionError: If the MAC string or bytes format is invalid.
            TypeError: If the type of `target_mac` is not supported.

        Returns:
            bytes: MAC address formatted as 6 bytes.
        """

        if target_mac is None:
            target_mac_format = b"\xFF\xFF\xFF\xFF\xFF\xFF"

        elif isinstance(target_mac, bytes):
            assert len(target_mac) == 6, \
                "Target MAC should be in the form b\"\\x00\\x11\\x22\\x33\\x44\\x55\" when using bytes"

            target_mac_format = target_mac

        elif isinstance(target_mac, str):
            assert len(target_mac) == 17, "Target MAC should be in the form 00:11:22:33:44:55 when using str"

            target_mac_format = b"".join([int(i, 16).to_bytes(signed=False) for i in target_mac.split(":")])

        else:
            raise TypeError("Target mac should be either None, bytes or a string")

        return target_mac_format

    def is_broadcast(self, mac_addr: bytes | str | None) -> bool:
        """Checks if a MAC address represents a broadcast address.

        Args:
            mac_addr (bytes | str | None): MAC address to check.

        Returns:
            bool: True if the MAC address is broadcast, False otherwise.
        """

        return self.target_mac_formatter(mac_addr) == b"\xff\xff\xff\xff\xff\xff"

    def on_disconnect(self, client: BleakClient) -> None:
        """Callback invoked when the buzzer disconnects.

        Args:
            client (BleakClient): BLE client that got disconnected.
        """

        logger.error("Client disconnected [TODO: RECONNECT]")

        self.client = None

    async def on_notification(self, sender: int | BleakGATTCharacteristic, data: bytearray) -> None:
        """Callback invoked when a buzzer sends a packet to the computer.

        Parses the received data, creates a `RecvObject`, and inserts it into the `recv_pool`.

        Args:
            sender (int | BleakGATTCharacteristic): Sender of the packet.
            data (bytearray): Data received from the buzzer.
        """

        data_format = bytes(data).rstrip(b"\x00")

        recv_obj = RecvObject(int(time.time()), data_format)
        self.recv_pool.insert_object(recv_obj)

        logger.debug(f"Added {str(recv_obj)} into poll")

        if recv_obj.cmd == "BPRS":
            self.but_callback.bprs_callback_maker()
