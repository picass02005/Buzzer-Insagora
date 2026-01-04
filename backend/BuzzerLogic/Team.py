# Copyright (c) 2025 picasso2005 <clementduran0@gmail.com>
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import List, Literal

from backend.BuzzerLogic.Constants import LED_NB
from backend.ESPCommunication.BluetoothCommunication import BluetoothCommunication
from backend.ESPCommunication.LEDManager import Color, LEDs

T_point_lim = Literal[5, 8, 10, 16]


class Team:
    """Represents a team with scoring logic and LED display control.

    A Team manages its score, associated buzzers, and LED visualization
    based on a configurable point limit. It communicates with ESP devices
    via Bluetooth to update LEDs accordingly.

    Attributes:
        primary_color (Color): Main color used to display points.
        secondary_color (Color): Secondary color used when exceeding base
            score ranges.
        bt_comm (BluetoothCommunication): Bluetooth communication interface
            used to send LED commands to ESP devices.
        point_limit (Literal[5, 8, 10, 16]): Maximum number of points for
            the team.
        point (int): Current score of the team.
        associated_buzzers (List[bytes]): List of MAC addresses identifying
            buzzers associated with this team.
    """

    def __init__(self, primary_color: Color, secondary_color: Color, bt_comm: BluetoothCommunication,
                 point_limit: T_point_lim) -> None:
        """Initializes a Team instance.

        Args:
            primary_color (Color): Main color used to display points.
            secondary_color (Color): Secondary color used when exceeding base
                score ranges.
            bt_comm (BluetoothCommunication): Bluetooth communication interface
                used to send LED commands.
            point_limit (Literal[5, 8, 10, 16]): Maximum number of points for
                the team.
        """

        self.primary_color: Color = primary_color
        self.secondary_color: Color = secondary_color
        self.bt_comm: BluetoothCommunication = bt_comm

        self.point_limit: T_point_lim = point_limit

        self.point: int = 0
        self.associated_buzzers: List[bytes] = []

    def calc_led_points(self) -> List[Color]:
        """Computes the LED color pattern representing the current score.

        The returned pattern represents a single circular score module
        containing 8 LEDs. This pattern is later mirrored onto both score
        modules.

        Returns:
            List[Color]: A list of 8 Color objects representing the LED
            pattern for one circular score module.
        """

        if self.point_limit == 5 or (self.point_limit == 10 and self.point <= 5):
            return [self.primary_color if i else Color(0, 0, 0) for i in self.__calc_led_point_5(self.point)]

        elif self.point_limit == 8 or (self.point_limit == 16 and self.point <= 8):
            return [self.primary_color if i else Color(0, 0, 0) for i in self.__calc_led_point_8(self.point)]

        elif self.point_limit == 10 and self.point > 5:
            return [self.secondary_color if i else self.primary_color for i in self.__calc_led_point_5(self.point - 5)]

        else:
            return [self.secondary_color if i else self.primary_color for i in self.__calc_led_point_8(self.point - 8)]

    @staticmethod
    def __calc_led_point_5(score: int) -> List[bool]:
        """Generates a symmetric circular LED pattern for scores up to 5.

        LEDs are lit symmetrically around the circular module, starting from
        the bottom LED (index 0) and expanding clockwise and counterclockwise
        as the score increases.

        Physical LED layout assumptions:
            - 8 LEDs arranged in a circle
            - LED index 0 is the bottom LED
            - Indices increase clockwise

        Args:
            score (int): Current score value.

        Returns:
            List[bool]: Boolean list of length 8 indicating which LEDs should
            be lit for a single score module.
        """

        ret = [False for _ in range(8)]

        if score >= 1:
            ret[7] = True

        if score >= 2:
            ret[0] = True
            ret[6] = True

        if score >= 3:
            ret[1] = True
            ret[5] = True

        if score >= 4:
            ret[2] = True
            ret[4] = True

        if score == 5:
            ret[3] = True

        return ret

    @staticmethod
    def __calc_led_point_8(score: int) -> List[bool]:
        """Generates a symmetric circular LED pattern for scores up to 8.

        LEDs are activated following a predefined order that expands around
        the circular module starting from the bottom LED (index 0). The pattern
        alternates around the circle to maintain visual balance rather than
        strictly lighting LEDs in clockwise order.

        Physical LED layout assumptions:
            - 8 LEDs arranged in a circle
            - LED index 0 is the bottom LED
            - Indices increase clockwise

        Activation order:
            [7, 6, 0, 5, 1, 4, 2, 3]

        Args:
            score (int): Current score value.

        Returns:
            List[bool]: Boolean list of length 8 indicating which LEDs should
            be lit for a single score module.
        """

        order = [7, 6, 0, 5, 1, 4, 2, 3]

        ret = [False for _ in range(8)]

        for i in order[:score]:
            ret[i] = True

        return ret

    def __set_led_logo(self, led: LEDs) -> LEDs:
        """Sets the logo section of the LED strip to the team's primary color.

        The logo section corresponds to LED indices from 16 to LED_NB - 1.

        Args:
            led (LEDs): LED object to modify.

        Returns:
            LEDs: The modified LED object with logo LEDs set.
        """

        for i in range(16, LED_NB):
            led.leds[i] = self.primary_color

        return led

    async def set_led_point(self) -> None:
        """Updates the LEDs on all associated buzzers to display the score.

        The computed LED pattern is mirrored on both halves of the display,
        the logo section is applied, and the final LED state is sent to all
        associated buzzers via Bluetooth.
        """

        l = LEDs(LED_NB)

        for i, j in enumerate(self.calc_led_points()):
            l.leds[i] = j
            l.leds[i + 8] = j

        l = self.__set_led_logo(l)

        for i in self.associated_buzzers:
            await self.bt_comm.commands.set_leds(l, i)
