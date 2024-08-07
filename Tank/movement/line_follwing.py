from sensors.infrared import InfraredSensor, SensorBitmaps
from calibrated_movement import CalibratedMotor
import time


class LineFollower:

    sensor: InfraredSensor
    motor: CalibratedMotor

    def __init__(self, sensor: InfraredSensor, motor: CalibratedMotor):
        self.sensor = sensor
        self.motor = motor

    def run(self):
        time.sleep(0.1)
        self.sensor.update()

        bitmap = self.sensor.get_bitmap()

        if bitmap == SensorBitmaps.LEFT:
            self.motor.turn_left(seconds=0.1, turn_speed=1)

        elif bitmap == SensorBitmaps.RIGHT:
            self.motor.turn_right(seconds=0.1, turn_speed=1)

        elif bitmap == SensorBitmaps.MIDDLE:
            self.motor.move_straight(seconds=0.1)
