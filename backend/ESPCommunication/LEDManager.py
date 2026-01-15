from dataclasses import dataclass
from typing import List, Any


class LEDs:
    """Represents all LEDs on a buzzer.

    Attributes:
        led_nb (int): Number of LEDs on the buzzer. This attribute is constant after initialization.
        leds (List[Color]): List of LED color values.
    """

    def __init__(self, led_nb: int) -> None:
        """Initializes a LEDs instance.

        All LEDs are initialized to the default color (0, 0, 0).

        Args:
            led_nb (int): Number of LEDs on this buzzer.
        """

        self.led_nb = led_nb
        self.leds: List[Color] = [Color(0, 0, 0) for _ in range(self.led_nb)]

    def __setattr__(self, name: str, value: Any) -> None:
        """Validates attribute modifications.

        Ensures that `leds` length is not changed and `led_nb` cannot be modified after initialization.

        Args:
            name (str): Name of the attribute being modified.
            value (Any): New value for the attribute.

        Raises:
            ValueError: If `leds` is not a list or its length does not match `led_nb`.
            RuntimeError: If attempting to modify `led_nb` after initialization.
        """

        if name == "leds":
            if not isinstance(value, list) or len(value) != getattr(self, "led_nb", len(value)):
                raise ValueError(f"Leds must be a list of length {self.led_nb}")

        elif name == "led_nb" and "led_nb" in self.__dict__:
            raise RuntimeError("This attribute is a constant")

        super().__setattr__(name, value)

    def __str__(self) -> str:
        """Returns a human-readable string of the object.

        Each LED color is displayed as a 6-digit hexadecimal value.

        Returns:
            str: Formatted string representing all LED colors.
        """

        return f"<LEDs {" ".join([f"{int(i):06X}" for i in self.leds])}>"

    def __bytes__(self) -> bytes:
        """Returns the bytes representation of the LEDs.

        Each LED is represented by 3 bytes: red, green, and blue.

        Returns:
            str: Bytes suitable for sending to the hardware.
        """

        return b"".join([bytes(i) for i in self.leds])


@dataclass
class Color:
    """Represents a color with red, green, and blue components.

    Each attribute value must be an integer in the range 0–255.

    Attributes:
        red (int): Red component (0–255).
        green (int): Green component (0–255).
        blue (int): Blue component (0–255).
    """

    red: int = 0
    green: int = 0
    blue: int = 0

    def __post_init__(self) -> None:
        """Validates color component values after initialization.

        Ensures that each of red, green, and blue is an integer between 0 and 255.

        Raises:
            AssertionError: If any component is not an integer in the range 0–255.
        """

        assert isinstance(self.red, int) and 0 <= self.red <= 255, "Red must be an integer in the range 0 - 255"
        assert isinstance(self.blue, int) and 0 <= self.blue <= 255, "Blue must be an integer in the range 0 - 255"
        assert isinstance(self.green, int) and 0 <= self.green <= 255, "Green must be an integer in the range 0 - 255"

    def __setattr__(self, name: str, value: Any) -> None:
        """Validates modifications to color components.

        Ensures that red, green, and blue remain integers in the range 0–255.

        Args:
            name (str): Name of the attribute being modified.
            value (Any): New value for the attribute.

        Raises:
            AssertionError: If the new value for red, green, or blue is not an integer in the range 0–255.
        """

        if name == "red" or name == "blue" or name == "green":
            assert isinstance(value, int) and 0 <= value <= 255, "Colors must be integers in the range 0 - 255"

        super().__setattr__(name, value)

    def from_hex(self, value: str) -> Color:
        """Initializes a Color from a hexadecimal string.

        Args:
            value (str): 6-character hexadecimal string in RRGGBB format.

        Returns:
            Color: The Color object with RGB values set according to the hex string.

        Raises:
            AssertionError: If the string is not 6 characters long.
            ValueError: If the string contains invalid hexadecimal characters.
        """

        value.lstrip("0x")

        assert len(value) == 6, "Hex value must be 6 characters long"

        try:
            red = int(value[0:2], 16)
            green = int(value[2:4], 16)
            blue = int(value[4:6], 16)

        except ValueError:
            raise ValueError("A color in hex must be a combinaison of hexadecimals numbers in the format RRGGBB")

        self.red = red
        self.green = green
        self.blue = blue

        return self

    def to_str_value(self) -> str:
        """Return the color as a 6-digit uppercase hexadecimal string.

        The returned string is formatted as ``RRGGBB``, where each component
        (red, green, blue) is encoded as a two-digit uppercase hexadecimal value.

        Returns:
            str: The color encoded as a hexadecimal RGB string (e.g. ``"FFA07A"``).
        """

        return f"{self.red:02X}{self.green:02X}{self.blue:02X}"

    def __str__(self) -> str:
        """Returns a human-readable string of the color.

        Displays the color as a 6-digit hexadecimal value.

        Returns:
            str: Formatted string representing the color.
        """

        return f"<Color {self.red:02X}{self.green:02X}{self.blue:02X}>"

    def __repr__(self) -> str:
        """Returns the official string representation of the color.

        Delegates to __str__.

        Returns:
            str: Same as __str__.
        """

        return self.__str__()

    def __index__(self) -> int:
        """Returns the color as an integer.

        Converts the RGB color to a 24-bit integer in 0xRRGGBB format.

        Returns:
            int: Integer representing the color.
        """

        return (self.red << 16) + (self.green << 8) + self.blue

    def __bytes__(self) -> bytes:
        """Returns the bytes representation of the color.

        Each color component is represented by one byte: red, green, and blue.

        Returns:
            bytes: Bytes representing the color.
        """

        return self.__index__().to_bytes(length=3)
