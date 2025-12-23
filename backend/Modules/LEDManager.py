from dataclasses import dataclass
from typing import List


class LEDs:
    """
    Class used to represent all LEDs on a buzzer
    """

    def __init__(self, led_nb: int) -> None:
        """
        :param led_nb: The number of LEDs on a buzzer. This value is a constant
        :return: None
        """

        self.led_nb = led_nb
        self.leds: List[Color] = [Color(0, 0, 0) for _ in range(self.led_nb)]

    def __setattr__(self, name, value):
        if name == "leds":
            if not isinstance(value, list) or len(value) != getattr(self, "led_nb", len(value)):
                raise ValueError(f"Leds must be a list of length {self.led_nb}")

        elif name == "led_nb" and "led_nb" in self.__dict__:
            raise RuntimeError("This attribute is a constant")

        super().__setattr__(name, value)

    def __str__(self) -> str:
        return f"<LEDs {" ".join([f"{int(i):06X}" for i in self.leds])}>"

    def __bytes__(self) -> bytes:
        return b"".join([bytes(i) for i in self.leds])


@dataclass
class Color:
    """
    Class used to represent a LED color
    """

    red: int = 0
    green: int = 0
    blue: int = 0

    def __post_init__(self):
        """
        Check data integrity on initialization
        """

        assert isinstance(self.red, int) and 0 <= self.red <= 255, "Red must be an integer in the range 0 - 255"
        assert isinstance(self.blue, int) and 0 <= self.blue <= 255, "Blue must be an integer in the range 0 - 255"
        assert isinstance(self.green, int) and 0 <= self.green <= 255, "Green must be an integer in the range 0 - 255"


    def __setattr__(self, name, value):
        """
        Check data integrity on attribute change
        """

        if name == "red" or name == "blue" or name == "green":
            assert isinstance(value, int) and 0 <= value <= 255, "Colors must be integers in the range 0 - 255"

        super().__setattr__(name, value)


    def from_hex(self, value: str) -> Color:
        """
        Set values based on a hex color
        :param value: The hex value
        :return: Color class
        """

        value.lstrip("0x")

        assert len(value) == 6, "Hex value must be 6 characters long"

        try:
            red = int(value[0:1], 16)
            green = int(value[2:3], 16)
            blue = int(value[4:5], 16)

        except ValueError:
            raise ValueError("A color in hex must be a combinaison of hexadecimals numbers in the format RRGGBB")

        self.red = red
        self.green = green
        self.blue = blue

        return self


    def __str__(self) -> str:
        return f"<Color {self.red:02X}{self.green:02X}{self.blue:02X}>"

    def __repr__(self) -> str:
        return self.__str__()

    def __index__(self) -> int:
        return (self.red << 16) + (self.green << 8) + self.blue

    def __bytes__(self) -> bytes:
        return self.__index__().to_bytes(length=3)
