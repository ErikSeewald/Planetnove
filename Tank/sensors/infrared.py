import RPi.GPIO as GPIO
from enum import Enum


class SensorBitmaps(Enum):
    """
    Enum representing all configurations of bitmap states that the infrared sensor can have.
    The MSB represents the left sensor, the LSB the right sensor. '1' -> black underneath sensor, else '0'.
    """

    NONE = 0b000
    RIGHT = 0b001
    MIDDLE = 0b010
    MIDDLE_RIGHT = 0b011
    LEFT = 0b100
    LEFT_RIGHT = 0b101
    LEFT_MIDDLE = 0b110
    ALL = 0b111


class InfraredSensor:
    """
    Class representing the three infrared sensors. The value of each sensor ('True' -> black underneath sensor) can be
    read directly from the class attributes. Their state is static until the update() method is called, which updates
    all three sensor states at the same time.
    """

    # State of the infrared sensors
    # 'True' -> Black underneath, else 'False'
    left: bool
    middle: bool
    right: bool

    def __init__(self):
        self.IR01 = 16
        self.IR02 = 20
        self.IR03 = 21
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)

        self.left = False
        self.middle = False
        self.right = False

    def update(self):
        self.left = GPIO.input(self.IR01)
        self.middle = GPIO.input(self.IR02)
        self.right = GPIO.input(self.IR03)

    def get_bitmap(self) -> int:
        """
        :return: The bitmap representation of the current sensor states.
        The MSB represents the left sensor, the LSB the right sensor.
        '1' -> black underneath sensor, else '0'.
        Use 'SensorBitmaps' enum for clarity.
        """
        return (self.left * 4) | (self.middle * 2) | self.right
