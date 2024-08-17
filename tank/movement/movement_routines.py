from enum import Enum
from tank.movement.calibrated_motor import CalibratedMotor
from util.direction import RelativeDirection


class MovementRoutines:
    """
    Class defining commonly used movement routines for the tank robot.
    Each routine returns a RoutineResult.
    """

    class RoutineResult(Enum):
        """
        Enum representing the result of a movement routine
        """
        SUCCESS = 1
        FAILURE = -1

    motor: CalibratedMotor

    def __init__(self, motor: CalibratedMotor):
        self.motor = motor

    def node_arrival(self) -> RoutineResult:
        # Roughly center the tank above the node
        self.motor.move_straight(seconds=0.4)
        return self.RoutineResult.SUCCESS

    def node_departure(self, target_direction: RelativeDirection) -> RoutineResult:
        if target_direction == RelativeDirection.UNKNOWN:
            return self.RoutineResult.FAILURE

        if target_direction == RelativeDirection.AHEAD:
            pass
        elif target_direction == RelativeDirection.RIGHT:
            self.motor.rotate_right(seconds=0.8)
        elif target_direction == RelativeDirection.LEFT:
            self.motor.rotate_left(seconds=0.8)
        elif target_direction == RelativeDirection.BEHIND:
            self.motor.rotate_right(seconds=1.6)

        # Move towards path to avoid tracking node again
        self.motor.move_straight(seconds=0.4)
        return self.RoutineResult.SUCCESS
