from abc import ABC
from dataclasses import dataclass

from planets.code.planet import Planet
from util.direction import Direction


@dataclass
class UpdateEvent(ABC):
    pass


@dataclass
class SwitchedToPlanetMode(UpdateEvent):
    new_planet: Planet


@dataclass
class AddedTank(UpdateEvent):
    tank_ip: str
    starting_node_id: str
    arrival_from: Direction


@dataclass
class DisconnectedTank(UpdateEvent):
    tank_ip: str


@dataclass
class TankConnectionLost(UpdateEvent):
    tank_ip: str


@dataclass
class TileGrabbed(UpdateEvent):
    pass


@dataclass
class TileReleased(UpdateEvent):
    pass


@dataclass
class TankPlanetUpdate(UpdateEvent):
    planet: Planet
    cur_node: str
