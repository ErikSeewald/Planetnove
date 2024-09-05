from __future__ import annotations


class Route:
    """
    Class representing a route between nodes on the planet.
    It can span over multiple paths (which only ever connect two neighboring nodes).
    """

    from_id: str
    to_id: str
    length: float

    path_id_list: list[str]

    def __init__(self, from_id: str, to_id: str, length: float, path_id_list: list[str]):
        self.from_id = from_id
        self.to_id = to_id
        self.length = length
        self.path_id_list = path_id_list

    def to_dict(self) -> dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "length": self.length,
            "path_id_list": self.path_id_list
        }

    @staticmethod
    def from_dict(route_dict: dict) -> Route:
        return Route(route_dict['from_id'], route_dict['to_id'], route_dict['length'], route_dict['path_id_list'])
