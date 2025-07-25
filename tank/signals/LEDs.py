from __future__ import annotations

import time
from enum import Enum
from util.direction import Direction, RelativeDirection
from rpi_ws281x import Adafruit_NeoPixel, Color

class LEDs:
    """
    Class representing the LED strip on the tank robot. Offers specific animations
    for certain actions but also the option to set the colors of the LEDs manually.
    """

    # LED STRIP CONFIG
    COLOR_ORDER = "RGB" # sending order of color data
    LED_COUNT = 4
    LED_PIN = 18  # GPIO pin connected to the pixels (uses PWM)
    LED_FREQ_HZ = 800000
    LED_DMA = 10  # DMA channel for generating signal
    LED_BRIGHTNESS = 64 # 0 - 255
    LED_INVERT = False  # True to invert the signal for NPN transistor level shift
    LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

    # ANIMATION CONFIG
    class DepartureType(Enum):
        """
        Enum describing the types of node departues that have corresponding animations.
        """

        KNOWN_PATH = 0,
        NEW_PATH = 1,
        TARGET_NEXT = 2,

    class LEDColor:
        """
        Dataclass for the color of LED pixels.
        Used to avoid using Color() from rpi_ws281x for as long as possible.
        """

        r: int
        g: int
        b: int
        def __init__(self, r: int, g: int, b: int):
            self.r = r
            self.g = g
            self.b = b

        @staticmethod
        def from_int24(color_int: int) -> LEDs.LEDColor:
            # Extract each channel
            b = color_int & 0xFF
            g = (color_int >> 8) & 0xFF
            r = (color_int >> 16) & 0xFF

            return LEDs.LEDColor(r, g, b)


    # ANIMATION DATA
    """
    |1      0|
    |        | Index layout
    |2      3|
    """
    _ALL_PIXELS = [0, 1, 2, 3]

    _COLOR_OFF = LEDColor(0, 0, 0)
    _COLOR_OBSTACLE = LEDColor(255, 0, 0)
    _COLOR_SUCCESS = LEDColor(0, 255, 0)

    _TURN_ANIMATIONS: dict[RelativeDirection, list[int]] = {
        RelativeDirection.AHEAD: [],
        RelativeDirection.LEFT: [0, 1, 2],
        RelativeDirection.RIGHT: [1, 0, 3],
        RelativeDirection.BEHIND: [0, 3, 2],
        RelativeDirection.UNKNOWN: [1, 3, 0, 2]
    }

    _DEPARTURE_ANIMATION = [
        [2, 3], [1, 0]
    ]

    _CONNECT_ANIMATION = [1, 0, 3, 2]

    _PIXELS_AT_DIRECTION: dict[RelativeDirection, list[int]] = {
        RelativeDirection.AHEAD: [0, 1],
        RelativeDirection.LEFT: [1, 2],
        RelativeDirection.RIGHT: [0, 3],
        RelativeDirection.BEHIND: [2, 3],
        RelativeDirection.UNKNOWN: []
    }

    _DIRECTION_COLORS: dict[Direction, LEDColor] = {
        Direction.NORTH: LEDColor(255, 0, 0),
        Direction.EAST: LEDColor(0, 255, 0),
        Direction.SOUTH: LEDColor(0, 0, 255),
        Direction.WEST: LEDColor(255, 80, 0),
        Direction.UNKNOWN: LEDColor(255, 0, 255)
    }

    _DEPARTURE_COLORS: dict[DepartureType, LEDColor] = {
        DepartureType.KNOWN_PATH: LEDColor(0, 0, 255),
        DepartureType.NEW_PATH: LEDColor(0, 255, 0),
        DepartureType.TARGET_NEXT: LEDColor(255, 25, 0)
    }

    def __init__(self):
        self.strip = Adafruit_NeoPixel(
            self.LED_COUNT,
            self.LED_PIN,
            self.LED_FREQ_HZ,
            self.LED_DMA,
            self.LED_INVERT,
            self.LED_BRIGHTNESS,
            self.LED_CHANNEL
        )

        self.strip.begin()

    def rainbow_color_from_pos(self, pos: int) -> LEDColor:
        """
        Generate a rainbow color for a given position in the range 0–255.

        - Positions outside 0–255 return black
        - Positions within 0–85 map from black/red to green,
          85–170 from green to blue, and 170–255 from blue to red
        """

        if not (0 <= pos <= 255):
            return self.LEDColor(0, 0, 0)

        if pos < 85:
            r = pos * 3
            g = 255 - pos * 3
            b = 0
        elif pos < 170:
            pos -= 85
            r = 255 - (pos * 3)
            g = 0
            b = pos * 3
        else:
            pos -= 170
            r = 0
            g = pos * 3
            b = 255 - (pos * 3)

        return self.LEDColor(r, g, b)

    def set_pixels(self, indices: list[int], color: LEDColor):
        """
        Sets the pixels at the given indices to the given color.
        Assumes all indices are valid.
        """

        for i in indices:
            self.strip.setPixelColor(i, Color(color.r, color.g, color.b))
        self.strip.show()

    def set_pixels_at_direction(self, direction: RelativeDirection, color: LEDColor):
        """
        Sets the two pixels at the given RelativeDirection to the given color.
        """

        self.set_pixels(self._PIXELS_AT_DIRECTION[direction], color)

    def reset_all(self):
        """Turns off all pixels"""
        self.set_pixels(self._ALL_PIXELS, self._COLOR_OFF)

    def rainbow_cycle(self, step_s: float = 0.020, iterations: int = 3):
        """
            Plays a rainbow animation with a different phase value for each pixel.
            Function only returns once the animation has finished.

            :param step_s: Determines the rate in seconds at which the colors change
            :param iterations: Determines the number of iterations of the rainbow cycle
        """

        num_pixels = self.strip.numPixels()
        phase_offsets = [int(i * 256 / num_pixels) for i in range(num_pixels)]

        for j in range(256 * iterations):
            for i in range(num_pixels):
                rainbow_pos = (phase_offsets[i] + j) % 256
                self.set_pixels([i], self.rainbow_color_from_pos(rainbow_pos))
            self.strip.show()
            time.sleep(step_s)
        self.reset_all()

    def turn_animation(self, direction: RelativeDirection, color: LEDColor = LEDColor(255, 255, 255),
                       step_s: float = 0.25, iterations: int = 1):
        """
            Plays an animation indicating a turn in the given RelativeDirection.
            Function only returns once the animation has finished.

            :param direction: The RelativeDirection that is being turned towards
            :param color: The color to use for the animation
            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for _ in range(iterations):
            for index in self._TURN_ANIMATIONS[direction]:
                self.reset_all()
                self.set_pixels([index], color)
                self.strip.show()
                time.sleep(step_s)
        self.reset_all()

    def global_direction_indicator(self, facing_direction: Direction, step_s: float = 0.5, iterations: int = 1):
        """
            Plays an animation indicating which global direction matches which relative direction of the LED strip.
            Colors: {north: red, east: green, south: blue, west: yellow}

            Function only returns once the animation has finished.

            :param facing_direction: The Direction that is directly ahead
            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for _ in range(iterations):
            for direction in Direction.valid_directions_ordered():
                self.reset_all()
                self.set_pixels_at_direction(
                    RelativeDirection.from_absolute(facing_direction, direction),
                    self._DIRECTION_COLORS[direction]
                )
                time.sleep(step_s)
        self.reset_all()

    def obstacle_animation(self, step_s: float = 0.25, iterations: int = 1):
        """
            Plays an animation for the event of encountering an obstacle.

            Function only returns once the animation has finished.

            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for _ in range(iterations):
            for i in range(2):
                self.reset_all()
                time.sleep(step_s)
                self.set_pixels_at_direction(RelativeDirection.AHEAD, self._COLOR_OBSTACLE)
                time.sleep(step_s)
            self.turn_animation(RelativeDirection.BEHIND, self._COLOR_OBSTACLE)
        self.reset_all()

    def node_departure(self, departure_type: DepartureType, step_s: float = 0.2, iterations: int = 1):
        """
            Plays an animation for the event of departing from a node (after already having rotated to face the
            departure direction).

            Function only returns once the animation has finished.

            :param departure_type: The type of departure to animate
            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for _ in range(iterations):
            for index_list in self._DEPARTURE_ANIMATION:
                self.reset_all()
                self.set_pixels(index_list, self._DEPARTURE_COLORS[departure_type])
                time.sleep(step_s)
            time.sleep(step_s)

        self.reset_all()

    def client_connected_animation(self, step_s: float = 0.3, iterations: int = 1):
        """
            Plays an animation for the event of the tank client connecting to the mothership.
            Function only returns once the animation has finished.

            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for _ in range(iterations):
            for i in self._CONNECT_ANIMATION:
                self.set_pixels([i], self._COLOR_SUCCESS)
                time.sleep(step_s)