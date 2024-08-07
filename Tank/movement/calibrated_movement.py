from Motor import Motor
import time

class CalibratedMotor:
    PWM: Motor

    # Calibrated speed values
    # -> move(c_left, c_right) should move straight
    c_left: int
    c_right: int

    def __init__(self):
        self.PWM = Motor()
        self.calibrate_straight(1400, 1000)

    def calibrate_straight(self, speed_left: int, speed_right: int):
        self.c_left = speed_left
        self.c_right = speed_right

    def move_straight(self, seconds: float, speed: float = 1):
        self.PWM.setMotorModel(self.c_left * speed, self.c_right * speed)
        time.sleep(seconds)
        self.PWM.setMotorModel(0, 0)

    def turn_left(self, seconds: float, turn_speed: float, forward_speed: float = 1,):
        turn_factor = 1 / (turn_speed + 1)
        self.PWM.setMotorModel(self.c_left * forward_speed * turn_factor, self.c_right * forward_speed)
        time.sleep(seconds)
        self.PWM.setMotorModel(0, 0)

    def turn_right(self, seconds: float, turn_speed: float, forward_speed: float = 1,):
        turn_factor = 1 / (turn_speed + 1)
        self.PWM.setMotorModel(self.c_left * forward_speed, self.c_right * forward_speed * turn_factor)
        time.sleep(seconds)
        self.PWM.setMotorModel(0, 0)
