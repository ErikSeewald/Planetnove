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
        """
            This routine is to be called immediately after the infrared sensor scans a node.
            After the routine, the tank should have moved forward to roughly center itself above the node.
        """

        self.motor.move_straight(seconds=0.4)
        return self.RoutineResult.SUCCESS

    def node_departure(self, target_direction: RelativeDirection) -> RoutineResult:
        """
        Handles the movement routine required to depart from a node before the line follower can be activated.
        Turns to face the target direction and then moves slightly forward to avoid the infrared sensor picking
        scanning the same node again.

        :param target_direction: The relative direction to the facing direction to depart in
        """

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

    def turn_around_avoid_obstacle(self) -> RoutineResult:
        """
        Handles the movement routine upon encountering an obstacle and needing to turn around completely.
        """

        self.motor.rotate_right(seconds=1.6)
        return self.RoutineResult.SUCCESS

