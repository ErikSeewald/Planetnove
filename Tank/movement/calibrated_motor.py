from movement.pwm import PWM
import time


class CalibratedMotor:
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
        self.c_left = speed_left
        self.c_right = speed_right

    def move_straight(self, seconds: float, speed: float = 1):
        self.PWM.setMotors(self.c_left * speed, self.c_right * speed)
        time.sleep(seconds)
        self.PWM.setMotors(0, 0)

    def rotate_right(self, seconds: float, rotation_speed: float = 1):
        self.PWM.setMotors(1500 * rotation_speed, -1500 * rotation_speed)
        time.sleep(seconds)
        self.PWM.setMotors(0, 0)

    def rotate_left(self, seconds: float, rotation_speed: float = 1):
        self.PWM.setMotors(-1500 * rotation_speed, 1500 * rotation_speed)
        time.sleep(seconds)
        self.PWM.setMotors(0, 0)
