from __future__ import annotations
from enum import Enum


# ---ABSOLUTE DIRECTION---
class Direction(Enum):
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270
    UNKNOWN = -1

    @staticmethod
    def real_directions_ordered() -> list[Direction]:
        """
        Returns the list of real directions, ordered by their degree value.
        [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        """

        return [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]

    def rotated(self, rot_angle_deg: int) -> Direction:
        """
        :param rot_angle_deg: The angle to rotate in degrees
        :return: The direction that lines up with the rotation (or Direction.UNKNOWN if no such direction exists)
        """

        if rot_angle_deg % 90 != 0 or self == Direction.UNKNOWN:
            return Direction.UNKNOWN
        return Direction((self.value + rot_angle_deg) % 360)

    def abbreviation(self) -> str:
        """
        :return: The corresponding direction abbreviation (e.g. 'N' for Direction.NORTH)
        """

        return direction_to_upper_str.get(self)

    @staticmethod
    def from_str(dir_str: str) -> Direction | None:
        """
        Tries to convert the given string into a direction.
        :param dir_str: The string representation of the direction
        :return: The direction or None if no matching direction was found
        """

        dir_str = dir_str.upper()
        return upper_str_to_direction.get(dir_str)

    def is_inverse_of(self, direction: Direction) -> bool:
        """
        :return: Whether this direction object is the inverse of the given direction
        """

        return (self.value - direction.value) % 360 == 180


upper_str_to_direction: dict[str, Direction] = {
    "NORTH": Direction.NORTH, "N": Direction.NORTH,
    "EAST": Direction.EAST, "E": Direction.EAST,
    "SOUTH": Direction.SOUTH, "S": Direction.SOUTH,
    "WEST": Direction.WEST, "W": Direction.WEST,
    "UNKNOWN": Direction.UNKNOWN, "U": Direction.UNKNOWN
}

direction_to_upper_str: dict[Direction, str] = {
    Direction.NORTH: "N", Direction.EAST: "E", Direction.SOUTH: "S", Direction.WEST: "W",
    Direction.UNKNOWN: "U"
}


# ---RELATIVE DIRECTION---
class RelativeDirection(Enum):
    AHEAD = 0
    RIGHT = 1
    BEHIND = 2
    LEFT = 3
    UNKNOWN = -1

    @staticmethod
    def from_absolute(facing: Direction, target: Direction) -> RelativeDirection:
        """
        Gets the relative direction of the given target direction
        in relation to the given absolute facing direction.
        Example: (facing=NORTH, target=EAST) => RIGHT
        """

        if facing == Direction.UNKNOWN or target == Direction.UNKNOWN:
            return RelativeDirection.UNKNOWN

        relative_value = ((target.value - facing.value) / 90) % 4
        return RelativeDirection(relative_value)

    def absolute_direction(self, facing: Direction) -> Direction:
        """
        Gets the absolute direction of this relative target direction
        in relation to the given absolute facing direction.
        Example: (facing=NORTH, relative_target=RIGHT) => EAST
        """

        if facing == Direction.UNKNOWN or self == RelativeDirection.UNKNOWN:
            return Direction.UNKNOWN

        relative_value = (facing.value / 90 + self.value) % 4
        return Direction(relative_value * 90)
