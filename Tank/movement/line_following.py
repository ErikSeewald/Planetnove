from sensors.infrared import InfraredSensor, SensorBitmap
from movement.calibrated_motor import CalibratedMotor
import time


class LineFollower:

    sensor: InfraredSensor
    motor: CalibratedMotor

    def __init__(self, sensor: InfraredSensor, motor: CalibratedMotor):
        self.sensor = sensor
        self.motor = motor

    def run(self):

        # Valid bitmaps in this case are simply SensorBitmap states that the script can currently deal with.
        last_valid_bitmap = SensorBitmap.MIDDLE
        valid_bitmaps = [SensorBitmap.LEFT, SensorBitmap.MIDDLE, SensorBitmap.RIGHT, SensorBitmap.ALL]

        while True:
            time.sleep(0.1)
            bitmap = self.sensor.update()

            # Handling inbetween states:
            # For example, starting with SensorBitmap.LEFT and turning left to get to SensorBitmap.MIDDLE can result
            # in temporary SensorBitmap.NONE state where the black tape is inbetween the left and middle sensor.
            # In that case, continue to use the last valid bitmap as the current bitmap until the sensors
            # detect the tape again.
            if bitmap in valid_bitmaps:
                last_valid_bitmap = bitmap
            else:
                bitmap = last_valid_bitmap

            # BITMAP MOVEMENT
            if bitmap == SensorBitmap.LEFT:
                self.motor.rotate_left(seconds=0.05)

            elif bitmap == SensorBitmap.RIGHT:
                self.motor.rotate_right(seconds=0.05)

            elif bitmap == SensorBitmap.MIDDLE:
                self.motor.move_straight(seconds=0.1)

            # NODE INDICATOR
            if bitmap == SensorBitmap.ALL:
                self.motor.move_straight(seconds=0.4)

                choice = input("l or r: ")
                if choice == "l":
                    self.motor.rotate_left(seconds=0.8)
                    last_valid_bitmap = SensorBitmap.LEFT
                elif choice == "r":
                    self.motor.rotate_right(seconds=0.8)
                    last_valid_bitmap = SensorBitmap.RIGHT
                time.sleep(0.1)
                self.motor.move_straight(seconds=0.3)
