# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
import asyncio
import json
import logging
import pathlib

from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic

from backend.Modules.Comands import Commands

logger = logging.getLogger(__name__)


class BluetoothCommunication:
    """
    Class used to represent a BLE communication with a buzzer
    """

    def __init__(self):
        self.SERVICE_UUID: str = ""
        self.CHARACTERISTIC_UUID: str = ""
        self.TARGET_NAME: str = ""

        self.client: None | BleakClient = None

        self.commands: Commands = Commands(self)

        self.__cmd_id: int = 0
        self.__cmd_id_lock: asyncio.Lock = asyncio.Lock()

        self.__load_config()
    

    def __load_config(self) -> None:
        """
        Load configuration from `backend-config.json` into class attributes
        :raise ValueError: If config is malformed
        :return: None
        """

        with open(f"{pathlib.Path(__file__).resolve().parent.parent}/backend-config.json", "r") as f:
            config = json.loads(f.read())
        
        for i in ["Service_UUID", "Characteristic_UUID", "BT_target_name"]:
            if i not in config.keys():
                raise ValueError(f"Value {i} not defined in backend-config")

        self.SERVICE_UUID = config["Service_UUID"]
        self.CHARACTERISTIC_UUID = config["Characteristic_UUID"]
        self.TARGET_NAME = config["BT_target_name"]
    

    async def connect_oneshot(self) -> bool:
        """
        Tries to connect to a buzzer
        :return: True if connection is successful
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

        await asyncio.sleep(0.5)

        if not self.client.is_connected:
            logger.error("Couldn't connect to buzzer")
            return False

        logger.debug("Attaching notifications handler")
        await self.client.start_notify(self.CHARACTERISTIC_UUID, self.on_notification)

        logger.info("Buzzer connected")

        await asyncio.sleep(0.1)  # Ensure BT stack is properly initialized

        return True


    async def send_command(self, command: bytes | str, args: bytes | str = b"", target_mac: bytes | str = None) -> int:
        """
        Send a command to buzzer(s)
        :param command: The command to send
        :param args: If needed, arguments for the command to send (in raw format)
        :param target_mac: The MAC address to target, by default, perform a broadcast
                           Accepted format are b"\x00\x11\x22\x33\x44\x55" or "00:11:22:33:44:55"
        :raises AssertionError: One assertion was not successful
        :raises TypeError: One argument wasn't an accepted type
        :return: Return sent command id
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
        """
        Method used to convert a target MAC address to proper format (in bytes)
        :param target_mac: The target MAC to format
        :raises AssertionError: One assertion was not successful
        :raises TypeError: One argument wasn't an accepted type
        :return: The formatted target MAC
        """

        if target_mac is None:
            target_mac_format = b"\xFF\xFF\xFF\xFF\xFF\xFF"

        elif isinstance(target_mac, bytes):
            assert len(target_mac) == 6, \
                "Target MAC should be in the form b\"\\x00\\x11\\x22\\x33\\x44\\x55\" when using bytes"

            target_mac_format = target_mac

        elif isinstance(target_mac, str):
            assert len(target_mac) == 17, "Target MAC should be in the form 00:11:22:33:44:55 when using str"

            target_mac_format = b"".join([bytes(int(i, 16)) for i in target_mac.split(":")])

        else:
            raise TypeError("Target mac should be either None, bytes or a string")

        return target_mac_format



    def on_disconnect(self, client: BleakClient) -> None:
        """
        Callback invoked when buzzer disconnect
        :param client: The client who got disconnected
        :return: None
        """

        logger.error("Client disconnected [TODO: RECONNECT]")

        self.client = None

    @staticmethod
    async def on_notification(sender: int | BleakGATTCharacteristic, data: bytearray) -> None:
        """
        Callback invoked when a buzzer send a packet to computer
        :param sender: The sender who sent the packet
        :param data: The data sent as bytearray
        :return: None
        """

        data_format = bytes(data).rstrip(b"\x00")

        logger.debug(f"RECV: {sender} - {data_format}")

    # TODO: add each commands
