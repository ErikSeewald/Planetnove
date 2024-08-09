from enum import Enum


# ---ABSOLUTE DIRECTION---
class Direction(Enum):
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270
    UNKNOWN = -1


upper_str_to_direction: dict[str, Direction] = {
    "NORTH": Direction.NORTH, "N": Direction.NORTH,
    "EAST": Direction.EAST, "E": Direction.EAST,
    "SOUTH": Direction.SOUTH, "S": Direction.SOUTH,
    "WEST": Direction.WEST, "W": Direction.WEST,
    "UNKNOWN": Direction.UNKNOWN, "U": Direction.UNKNOWN
}


def str_to_direction(dir_str: str) -> Direction | None:
    """
    Tries to convert the given string into a direction.
    :param dir_str: The string representation of the direction
    :return: The direction or None if no matching direction was found
    """

    dir_str = dir_str.upper()
    return upper_str_to_direction.get(dir_str)


# ---RELATIVE DIRECTION---
class RelativeDirection(Enum):
    AHEAD = 0
    RIGHT = 1
    BEHIND = 2
    LEFT = 3
    UNKNOWN = -1


def get_relative_direction(facing: Direction, target: Direction) -> RelativeDirection:
    """
    Gets the relative direction of the given target direction
    in relation to the given absolute facing direction.
    Example: (facing=NORTH, target=EAST) => RIGHT
    """

    if facing == Direction.UNKNOWN or target == Direction.UNKNOWN:
        return RelativeDirection.UNKNOWN

    relative_value = ((target.value - facing.value) / 90) % 4
    return RelativeDirection(relative_value)


def get_absolute_direction(facing: Direction, relative_target: RelativeDirection) -> Direction:
    """
    Gets the absolute direction of the given relative target direction
    in relation to the given absolute facing direction.
    Example: (facing=NORTH, relative_target=RIGHT) => EAST
    """

    if facing == Direction.UNKNOWN or relative_target == RelativeDirection.UNKNOWN:
        return Direction.UNKNOWN

    relative_value = (facing.value / 90 + relative_target.value) % 4
    return Direction(relative_value * 90)
