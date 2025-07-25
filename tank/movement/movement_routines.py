import time
from enum import Enum
from tank.movement.calibrated_motor import CalibratedMotor
from tank.sensors.infrared import InfraredSensor, SensorBitmap
from util.direction import RelativeDirection


class MovementRoutines:
    """
    Class defining commonly used movement routines for the tank robot.
    Each routine returns a RoutineResult.
    """

    ROTATION_SPEED = 1.5

    class RoutineResult(Enum):
        """
        Enum representing the result of a movement routine
        """
        SUCCESS = 1
        FAILURE = -1

    motor: CalibratedMotor
    infrared: InfraredSensor

    def __init__(self, motor: CalibratedMotor, infrared: InfraredSensor):
        self.motor = motor
        self.infrared = infrared

    def node_arrival(self) -> RoutineResult:
        """
        This routine is to be called immediately after the infrared sensor scans a node.
        """

        self.motor.stop_motors()
        return self.RoutineResult.SUCCESS

    def node_departure(self, target_direction: RelativeDirection) -> RoutineResult:
        """
        Handles the movement routine required to depart from a node before the line follower can be activated.

        :param target_direction: The direction (relative to the facing direction) to depart in
        """

        if target_direction == RelativeDirection.UNKNOWN:
            return self.RoutineResult.FAILURE

        if target_direction == RelativeDirection.AHEAD:
            pass
        elif target_direction == RelativeDirection.BEHIND:
            self.motor.setMotors(-self.ROTATION_SPEED, self.ROTATION_SPEED)
            time.sleep(1)
            while self.infrared.update() == SensorBitmap.NONE:
                pass
        else:
            self.motor.move_straight(seconds=0.3)
            if target_direction == RelativeDirection.RIGHT:
                self.motor.setMotors(self.ROTATION_SPEED, -self.ROTATION_SPEED)
            elif target_direction == RelativeDirection.LEFT:
                self.motor.setMotors(-self.ROTATION_SPEED, self.ROTATION_SPEED)

            if self.infrared.update() == SensorBitmap.NONE:
                while True:
                    bitmap = self.infrared.update()
                    if bitmap == SensorBitmap.MIDDLE:
                        break
            else:
                cleared = False
                while True:
                    bitmap = self.infrared.update()
                    if cleared and bitmap == SensorBitmap.MIDDLE:
                        break
                    elif bitmap == SensorBitmap.NONE:
                        cleared = True


        self.motor.stop_motors()
        return self.RoutineResult.SUCCESS

    def turn_around_avoid_obstacle(self) -> RoutineResult:
        """
        Handles the movement routine upon encountering an obstacle and needing to turn around completely.
        """

        self.motor.stop_motors()

        # Turn right until the left sensor is over the line, then continue turning until
        # the right sensor is over the line again.
        #
        # The only cases where this does not lead to a correct turn around are:
        # 1. The sensor malfunctions or the tank is not on a path at all -> Irrelevant
        # 2. All sensors are already to the right of the path but still close -> Will result in 360-degree turn
        #   -> Should recognize the obstacle again and turn around again. This time properly.
        self.motor.setMotors(self.ROTATION_SPEED, -self.ROTATION_SPEED)
        left_seen = False
        while True:
            bitmap = self.infrared.update()
            if bitmap == SensorBitmap.LEFT:
                left_seen = True
            elif left_seen and bitmap == SensorBitmap.RIGHT:
                break

        self.motor.stop_motors()
        return self.RoutineResult.SUCCESS
