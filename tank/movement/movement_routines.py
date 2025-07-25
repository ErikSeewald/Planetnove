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

    ROTATION_SPEED = 1.25

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
            # Turn left until left path (if it exists) is cleared, then turn to the path.
            self.motor.setMotors(-self.ROTATION_SPEED, self.ROTATION_SPEED)
            time.sleep(1)
            while self.infrared.update() == SensorBitmap.MIDDLE:
                pass

        else:
            # 1. Get a little headroom ahead of the node
            self.motor.move_straight(seconds=0.3)

            # 2. Rotate off of the forward path (if it exists), then continue rotating
            # The reason this needs the timed rotation and not the following while loop
            # is because the path can be between two sensors and show up as NONE.
            if target_direction == RelativeDirection.RIGHT:
                self.motor.rotate_right(seconds=0.3)
                self.motor.setMotors(self.ROTATION_SPEED, -self.ROTATION_SPEED)
            elif target_direction == RelativeDirection.LEFT:
                self.motor.rotate_left(seconds=0.3)
                self.motor.setMotors(-self.ROTATION_SPEED, self.ROTATION_SPEED)

            # 3. Fully clear forward path with all sensors.
            # After step 2 there should no longer be a risk of this finding NONE
            # inbetween two sensors. After this loop the forward path should be cleared
            # enough for the next detected MIDDLE to be the correct destination.
            while self.infrared.update() != SensorBitmap.NONE:
                pass

            # 4. Continue rotating until the sensor detects MIDDLE.
            # Now we should face the destination path.
            while self.infrared.update() != SensorBitmap.MIDDLE:
                pass

        self.motor.stop_motors()
        return self.RoutineResult.SUCCESS

    def turn_around_avoid_obstacle(self) -> RoutineResult:
        """
        Handles the movement routine upon encountering an obstacle and needing to turn around completely.
        """

        self.motor.stop_motors()

        # Turn right until the left sensor is over the line, then continue turning until
        # the middle sensor is over the line again.
        self.motor.setMotors(self.ROTATION_SPEED, -self.ROTATION_SPEED)
        left_seen = False
        while True:
            bitmap = self.infrared.update()
            if bitmap == SensorBitmap.LEFT:
                left_seen = True
            elif left_seen and bitmap == SensorBitmap.MIDDLE:
                break

        self.motor.stop_motors()
        return self.RoutineResult.SUCCESS
