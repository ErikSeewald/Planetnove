from movement.pwm import PWM
import time


class CalibratedMotor:
    """
    Class controlling the PWM using manually calibrated values. These differ from product to product.
    """
    PWM: PWM

    # Calibrated speed values
    # -> move(c_left, c_right) should move straight
    c_left: int
    c_right: int

    def __init__(self):
        self.PWM = PWM()

        # These values can be different for each tank.
        self.calibrate_straight(1400, 1000)

    def calibrate_straight(self, speed_left: int, speed_right: int):
        """
        Sets the calibration values needed for moving the tank forward in a straight line
        :param speed_left: Speed value for the left wheel
        :param speed_right: Speed value for the right wheel
        """

        self.c_left = speed_left
        self.c_right = speed_right

    def move_straight(self, seconds: float, speed: float = 1):
        """
        Moves in a straight line based on the currently set calibration values.
        A negative speed parameter will make the tank move backwards.
        The thread sleeps during the movement.
        :param seconds: How many seconds the tank should move for
        :param speed: The speed multiplier. Values too small or too large will be cut off.
        """

        self.PWM.setMotors(self.c_left * speed, self.c_right * speed)
        time.sleep(seconds)
        self.PWM.setMotors(0, 0)

    def rotate_right(self, seconds: float, rotation_speed: float = 1):
        """
        Rotates in place to the right. Due to the wheel layout of the tank this is not a perfect rotation
        around it's center and longer rotations will introduce large shifts in position.
        The thread sleeps during the rotation.
        :param seconds: How many seconds the tank should rotate for
        :param rotation_speed: The speed multiplier. Values too small or too large will be cut off.
        """

        self.PWM.setMotors(1500 * rotation_speed, -1500 * rotation_speed)
        time.sleep(seconds)
        self.PWM.setMotors(0, 0)

    def rotate_left(self, seconds: float, rotation_speed: float = 1):
        """
        Rotates in place to the left. Due to the wheel layout of the tank this is not a perfect rotation
        around it's center and longer rotations will introduce large shifts in position.
        The thread sleeps during the rotation.
        :param seconds: How many seconds the tank should rotate for
        :param rotation_speed: The speed multiplier. Values too small or too large will be cut off.
        """

        self.PWM.setMotors(-1500 * rotation_speed, 1500 * rotation_speed)
        time.sleep(seconds)
        self.PWM.setMotors(0, 0)
