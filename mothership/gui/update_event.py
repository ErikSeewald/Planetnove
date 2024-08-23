from abc import ABC
from dataclasses import dataclass

from planets.code.planet import Planet


@dataclass
class UpdateEvent(ABC):
    pass


@dataclass
class SwitchedToPlanetMode(UpdateEvent):
    new_planet: Planet


@dataclass
class TileGrabbed(UpdateEvent):
    pass


@dataclass
class TileReleased(UpdateEvent):
    pass
