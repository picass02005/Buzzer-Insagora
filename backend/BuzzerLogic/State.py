# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import asyncio
import logging
from enum import Enum
from typing import List

from backend.BuzzerLogic.Constants import LED_NB
from backend.BuzzerLogic.Team import Team
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.ESPCommunication.LEDManager import LEDs, Color
from backend.ESPCommunication.RecvPool import RecvObject

logger = logging.getLogger(__name__)


class State:
    """Manages the current __state of the game and controls LEDs for __teams.

    The State class handles:
        - Current game __state (IDLE, WAIT, CHECK)
        - LED updates for each __state
        - Detection and confirmation/denial of button presses from __teams

    Attributes:
        teams (List[Team]): List of Team instances participating in the game.
        bt_comm (BluetoothCommunication): Bluetooth communication interface
            for interacting with team buzzers.
        current_state (StateEnum): Current __state of the system.
        team_check (Optional[Team]): The team currently being checked for a press.
    """

    def __init__(self, teams: List[Team], bt_comm: BluetoothCommunication) -> None:
        """Initializes the State instance.

        Args:
            teams (List[Team]): List of Team instances participating in the game.
            bt_comm (BluetoothCommunication): Bluetooth communication interface
                used to control LEDs and read button presses.
        """

        self.teams: List[Team] = teams
        self.bt_comm: BluetoothCommunication = bt_comm

        self.current_state: StateEnum = StateEnum.IDLE
        self.team_check: None | Team = None

    async def __wait_press_led(self) -> None:
        """Sets all LEDs to white to indicate the system is waiting for a press.

        This is used internally when the __state is WAIT.
        """

        l = LEDs(LED_NB)
        l.leds = [Color(255, 255, 255) for _ in range(LED_NB)]

        await self.bt_comm.commands.set_leds(l, "ff:ff:ff:ff:ff:ff")

    async def __check_led(self) -> None:
        """Sets LEDs for the team currently being checked.

        - Even indices are set to red
        - Odd indices are set to green
        - Clears all previous LEDs before updating

        This visually indicates that a press is being checked.

        Raises:
            AttributeError: If `team_check` is None when called.
        """

        l: LEDs = LEDs(LED_NB)
        l.leds = [Color(255, 0, 0) if i % 2 == 0 else Color(0, 255, 0) for i in range(LED_NB)]

        await self.bt_comm.commands.clear_leds()

        for mac in self.team_check.associated_buzzers:
            await self.bt_comm.commands.set_leds(l, mac)

    async def __confirm_deny_led(self, confirm: bool) -> None:
        """Flashes LEDs to indicate confirmation or denial of a press.

        - If `confirm` is True: LEDs flash green
        - If `confirm` is False: LEDs flash red
        - Flashes 5 times with 0.25 second intervals

        Args:
            confirm (bool): Whether the press is confirmed (True) or denied (False).
        """

        if confirm:
            color: Color = Color(0, 255, 0)

        else:
            color: Color = Color(255, 0, 0)

        l: LEDs = LEDs(LED_NB)
        l.leds = [color for _ in range(LED_NB)]

        await self.bt_comm.commands.clear_leds()

        for i in range(5):
            for mac in self.team_check.associated_buzzers:
                await self.bt_comm.commands.set_leds(l, mac)

            await asyncio.sleep(0.25)

            await self.bt_comm.commands.clear_leds()

            await asyncio.sleep(0.25)

    async def set_idle(self) -> None:
        """Switches the system to the IDLE __state and updates LEDs.

        Resets `team_check` to None.
        """

        logger.debug("Switching __state to IDLE")

        self.current_state = StateEnum.IDLE
        self.team_check = None

        await self.__set_led_on_state()

    async def wait_press(self) -> None:
        """Switches the system to WAIT __state and waits for the first button press.

        Updates LEDs to indicate waiting. When a press is received, the __state
        switches to CHECK if a valid team is detected; otherwise, it returns
        to IDLE.

        Raises:
            TimeoutError: If no button press is received (depending on callback).
        """

        logger.debug("Switching __state to WAIT")

        logger.debug("Performing automatic clock set")
        await self.bt_comm.commands.automatic_set_clock()

        self.current_state = StateEnum.WAIT
        await self.__set_led_on_state()

        recv: RecvObject = await self.bt_comm.but_callback.get_first_press(timeout=None)

        mac: str = recv.data[0]

        self.team_check = self.get_team_from_mac(mac)

        if self.team_check is None:
            await self.set_idle()

        else:
            logger.debug("Switching __state to CHECK")

            self.current_state = StateEnum.CHECK
            await self.__set_led_on_state()

    async def confirm_press(self) -> None:
        """Confirms the current press and updates the team's score.

        Updates LEDs to indicate confirmation, increments the team's point,
        and returns the system to IDLE.

        Does nothing if the current __state is WAIT or no team is selected.
        """

        if self.current_state == StateEnum.WAIT or self.team_check is None:
            self.team_check = None
            await self.__set_led_on_state()
            return

        logger.debug(f"Press for {self.team_check.associated_buzzers} confirmed")

        self.team_check.point += 1

        await self.__confirm_deny_led(confirm=True)
        await self.set_idle()

    async def deny_press(self) -> None:
        """Denies the current press and updates LEDs to indicate denial.

        Flashes red on the buzzer LEDs and returns the system to IDLE.

        Does nothing if the current __state is WAIT or no team is selected.
        """

        if self.current_state == StateEnum.WAIT or self.team_check is None:
            self.team_check = None
            await self.__set_led_on_state()
            return

        logger.debug(f"Press for {self.team_check.associated_buzzers} denied")

        await self.__confirm_deny_led(confirm=False)
        await self.set_idle()

    def get_team_from_mac(self, mac: bytes | str) -> None | Team:
        """Finds a Team associated with a given MAC address.

        Args:
            mac (bytes | str): MAC address of the buzzer.

        Returns:
            Optional[Team]: The Team associated with the MAC address,
            or None if no team matches.
        """

        mac_f = self.bt_comm.target_mac_formatter(mac)

        for i in self.teams:
            if mac_f in i.associated_buzzers:
                return i

        return None

    async def __set_led_on_state(self):
        """Updates LEDs to reflect the current system __state.

        - IDLE: Updates all __teams’ LEDs to show their current points
        - WAIT: Lights all LEDs white to indicate waiting for a press
        - CHECK: Lights LEDs for the team currently being checked
        - Other states: Clears all LEDs
        """

        match self.current_state:
            case StateEnum.IDLE:
                for t in self.teams:
                    await t.set_led_point()

            case StateEnum.WAIT:
                await self.__wait_press_led()

            case StateEnum.CHECK:
                await self.__check_led()

            case _:
                await self.bt_comm.commands.clear_leds()


class StateEnum(Enum):
    """Enumeration of possible states for the game/__state machine.

    Attributes:
        IDLE (int): System is idle; no active press being handled.
        WAIT (int): Waiting for a button press from a team.
        CHECK (int): A press has been detected and is being checked.
    """

    IDLE = 0
    WAIT = 1
    CHECK = 2
