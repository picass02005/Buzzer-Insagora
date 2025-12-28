# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import asyncio
import logging
from typing import TYPE_CHECKING, List

from backend.ESPCommunication.RecvPool import RecvObject

if TYPE_CHECKING:
    from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication

logger = logging.getLogger(__name__)


class ButtonCallback:
    """Handles button press events received via Bluetooth.

    This class ensures that only one callback is processed at a time and
    keeps track of previously seen button presses to avoid duplicates.
    It also allows waiting asynchronously for the next button press using
    an event-based mechanism.

    Attributes:
        bt_comm (BluetoothCommunication): The Bluetooth communication instance used to receive button presses.
        last_seen (List[RecvObject]): List of the last processed button press objects to avoid duplicates.
        __callback_running (bool): Internal flag indicating if a callback is currently running.
        __callback_event (asyncio.Event): Internal event used to notify waiters of new button presses.
    """

    def __init__(self, bt_comm: BluetoothCommunication) -> None:
        """Initializes a ButtonCallback instance.

        Args:
            bt_comm (BluetoothCommunication): The Bluetooth communication instance used to receive button presses.
        """

        self.bt_comm: BluetoothCommunication = bt_comm

        self.last_seen: List[RecvObject] = []

        self.__callback_event: asyncio.Event = asyncio.Event()
        self.__callback_running: bool = False

    def bprs_callback_maker(self):
        """Schedules a callback to process new button presses.

        If a callback is already running, this method returns immediately
        without scheduling another one. Otherwise, it sets the running flag
        and creates an asynchronous task to process the button presses.
        """

        if self.__callback_running:
            return

        self.__callback_running = True

        asyncio.create_task(self.__callback())
        logger.debug("New callback task created")

    async def __callback(self):
        """Processes new button press events asynchronously.

        This method:
        - Waits briefly to allow multiple notifications to accumulate.
        - Filters out previously seen presses.
        - Sorts the new presses by their internal clock.
        - Updates the `last_seen` list.
        - Sets the internal event to notify any coroutines waiting for a press.
        - Clears the receive pool regardless of exceptions to free resources.
        """

        try:
            await asyncio.sleep(0.15)

            presses: List[RecvObject] = list(filter(
                lambda x: x not in self.last_seen,
                self.bt_comm.recv_pool.get_object_by_cmd("BPRS"))
            )

            presses.sort(key=lambda x: int(x.data[1]))

            # No new button presses were made
            if not presses:
                return

            self.__callback_event.set()

            self.last_seen = presses.copy()

        finally:
            self.bt_comm.recv_pool.clear_by_command("BPRS")

            # Free the callback even if exceptions happens during execution
            self.__callback_running = False

    async def get_first_press(self, timeout: None | float = None) -> RecvObject:
        """Waits for the next button press and returns the first press received.

        This method waits asynchronously until a new button press is detected
        by `__callback` and returns the first `RecvObject` from the `last_seen` list.
        The wait can be limited with the `timeout` parameter.

        Args:
            timeout (float | None): Maximum number of seconds to wait for a button press.
                If None, waits indefinitely. If the timeout expires before a press is
                received, an `asyncio.TimeoutError` is raised.

        Returns:
            RecvObject: The first new button press object.

        Raises:
            asyncio.TimeoutError: If no button press is detected before the timeout expires.
        """
        
        self.__callback_event.clear()

        try:
            await asyncio.wait_for(self.__callback_event.wait(), timeout=timeout)
            return self.last_seen[0]

        finally:
            self.__callback_event.clear()
