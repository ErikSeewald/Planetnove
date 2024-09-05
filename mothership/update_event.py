from abc import ABC
from dataclasses import dataclass
from planets.code.planet import Planet
from planets.code.route import Route
from util.direction import Direction


@dataclass
class UpdateEvent(ABC):
    """
    Abstract base class for an event occurring during the updating process of a mothership submodule.
    Used to handle events at the top level mothership module after the submodules have fully finished updating.
    """

    pass


@dataclass
class SwitchedToPlanetMode(UpdateEvent):
    """
    Update event that occurs when the PlanetView submodule switches to planet mode.
    Contains the new_planet currently being used in planet mode.
    """

    new_planet: Planet


@dataclass
class AddedTank(UpdateEvent):
    """
    Update event that occurs when the communications submodule adds a new tank client.
    Additionally to the client's ip address, the event dataclass also contains the id of the node that the tank will
    be starting from as well as the direction it will arrive from. These are set the planet view SubGUI.
    """

    tank_ip: str
    starting_node_id: str
    arrival_from: Direction


@dataclass
class DisconnectedTank(UpdateEvent):
    """
    Update event that occurs if the user disconnects the tank client using the coms SubGUI.
    Contains the tank clients ip address.
    """

    tank_ip: str


@dataclass
class TankConnectionLost(UpdateEvent):
    """
    Update event that occurs if the communication submodule loses the connection to the tank client.
    Contains the tank clients ip address.
    """

    tank_ip: str


@dataclass
class TileGrabbed(UpdateEvent):
    """
    Update event that occurs whenever a tile is grabbed in planet edit mode.
    """

    pass


@dataclass
class TileReleased(UpdateEvent):
    """
    Update event that occurs whenever a tile is released in planet edit mode.
    """

    pass


@dataclass
class TankPlanetUpdate(UpdateEvent):
    """
    Update event that occurs whenever the tank sends it's internal planet state.
    Contains that data.
    """

    planet: Planet
    cur_node: str
    target_node: str
    target_route: Route
    depart_dir: Direction
