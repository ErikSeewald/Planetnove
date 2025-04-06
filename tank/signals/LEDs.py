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
    LED_BRIGHTNESS = 255
    LED_INVERT = False  # True to invert the signal for NPN transistor level shift
    LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

    # ANIMATION CONFIG
    class ArrivalType(Enum):
        """
        Enum describing the types of node arrivals that have corresponding animations.
        """

        KNOWN_PATH = 0,
        NEW_PATH = 1,
        TARGET_REACHED = 2,

    # ANIMATION DATA
    _ALL_PIXELS = [0, 1, 2, 3]

    _TURN_ANIMATIONS: dict[RelativeDirection, list[int]] = {
        RelativeDirection.AHEAD: [],
        RelativeDirection.LEFT: [1, 0, 3],
        RelativeDirection.RIGHT: [0, 1, 2],
        RelativeDirection.BEHIND: [1, 2, 3],
        RelativeDirection.UNKNOWN: [0, 2, 1, 3]
    }

    _PIXELS_AT_DIRECTION: dict[RelativeDirection, list[int]] = {
        RelativeDirection.AHEAD: [0, 1],
        RelativeDirection.LEFT: [0, 3],
        RelativeDirection.RIGHT: [1, 2],
        RelativeDirection.BEHIND: [2, 3],
        RelativeDirection.UNKNOWN: []
    }

    _DIRECTION_COLORS: dict[Direction, tuple[int, int, int]] = {
        Direction.NORTH: (255, 0, 0),
        Direction.EAST: (0, 255, 0),
        Direction.SOUTH: (0, 0, 255),
        Direction.WEST: (255, 255, 0),
        Direction.UNKNOWN: (255, 0, 255)
    }

    _ARRIVAL_COLORS: dict[ArrivalType, tuple[int, int, int]] = {
        ArrivalType.KNOWN_PATH: (0, 0, 255),
        ArrivalType.NEW_PATH: (0, 255, 0),
        ArrivalType.TARGET_REACHED: (255, 0, 0)
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

    @staticmethod
    def convert_color_format(order: str, color: int) -> tuple[int,int,int]:
        """
        Converts a color integer into the given channel order (e.g. 'GRB').
        """

        # Extract each channel
        b = color & 0xFF
        g = (color >> 8) & 0xFF
        r = (color >> 16) & 0xFF

        order_to_color = {
            "GRB": Color(g, r, b),
            "GBR": Color(g, b, r),
            "RGB": Color(r, g, b),
            "RBG": Color(r, b, g),
            "BRG": Color(b, r, g),
            "BGR": Color(b, g, r),
        }

        return order_to_color[order]

    def reset_all(self):
        """Turns off all pixels"""

        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, (0, 0, 0))
        self.strip.show()

    def rainbow_color_from_pos(self, pos: int) -> tuple[int, int, int]:
        """
        Generate a rainbow color for a given position in the range 0–255.

        - Positions outside 0–255 return black
        - Positions within 0–85 map from black/red to green,
          85–170 from green to blue, and 170–255 from blue to red
        - The returned color is converted to self.COLOR_ORDER
        """

        if not (0 <= pos <= 255):
            return self.convert_color_format(self.COLOR_ORDER, (0, 0, 0))

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

        return self.convert_color_format(self.COLOR_ORDER, (r, g, b))

    def set_pixels(self, indices: list[int], color):
        """
        Sets the pixels at the given indices to the given color.
        Assumes all indices are valid.
        """

        for i in indices:
            self.strip.setPixelColor(i, color)
        self.strip.show()

    def set_pixels_at_direction(self, direction: RelativeDirection, color):
        """
        Sets the two pixels at the given RelativeDirection to the given color.
        """

        self.set_pixels(self._PIXELS_AT_DIRECTION[direction], color)

    def rainbow_cycle(self, step_s: float = 0.020, iterations: int = 5):
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
                self.strip.setPixelColor(i, self.rainbow_color_from_pos(rainbow_pos))
            self.strip.show()
            time.sleep(step_s)

    def turn_animation(self, direction: RelativeDirection, color, step_s: float = 0.25, iterations: int = 3):
        """
            Plays an animation indicating a turn in the given RelativeDirection.
            Function only returns once the animation has finished.

            :param direction: The RelativeDirection that is being turned towards
            :param color: The led color to use for the animation
            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for _ in range(iterations):
            for index in self._TURN_ANIMATIONS[direction]:
                self.reset_all()
                self.strip.setPixelColor(index, color)
                self.strip.show()
                time.sleep(step_s)

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

    def obstacle_animation(self, step_s: float = 0.25, iterations: int = 1):
        """
            Plays an animation for the event of encountering an obstacle.

            Function only returns once the animation has finished.

            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for _ in range(iterations):
            for i in range(3):
                self.reset_all()
                time.sleep(step_s)
                self.set_pixels_at_direction(RelativeDirection.AHEAD, (255, 0, 0))
                time.sleep(step_s)
            self.turn_animation(RelativeDirection.BEHIND, (255, 0, 0))

    def node_arrival(self, arrival_type: ArrivalType, step_s: float = 0.2, iterations: int = 2):
        """
            Plays an animation for the event of arriving at a node with the given ArrivalType.

            Function only returns once the animation has finished.

            :param arrival_type: The ArrivalType to play the corresponding animation for.
            :param step_s: Determines the rate in seconds at which the animation steps play
            :param iterations: Determines the number of iterations of the animation
        """

        for i in range(iterations):
            self.reset_all()
            time.sleep(step_s)
            self.set_pixels(self._ALL_PIXELS, self._ARRIVAL_COLORS[arrival_type])
            time.sleep(step_s)

        self.reset_all()


if __name__ == '__main__':
    led = LEDs()
    try:
        #led.node_arrival(LEDs.ArrivalType.KNOWN_PATH)
        led.reset_all()
    except KeyboardInterrupt:
        led.reset_all()