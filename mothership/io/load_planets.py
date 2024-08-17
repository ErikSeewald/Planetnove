import os
import glob
from pygame import Vector2
from mothership.gui.tile import DraggableTile
from util.result_msg import ResultMSG


class PlanetLoader:
    """
    Class responsible for loading and holding the planet data (i.e. the svg files and data files).
    Has some error handling but largely assumes that all files are formatted correctly.
    """

    planet_directory: str

    svg_tiles: list[DraggableTile]
    tile_data: list[str] # TODO: make datastructure

    def __init__(self, planet_dir: str):
        self.planet_directory = planet_dir
        self.svg_tiles = list()
        self.tile_data = list()

    def load(self) -> ResultMSG:
        svg_dir = os.path.join(self.planet_directory, "svg")
        data_dir = os.path.join(self.planet_directory, "data")

        tile_pattern = os.path.join(svg_dir, 'tile_[a-zA-Z].svg')
        tile_files = glob.glob(tile_pattern)

        data_pattern = os.path.join(data_dir, 'tile_[a-zA-Z].json')
        data_files = glob.glob(data_pattern)

        # Check if each tile has a corresponding data file and the other way around
        svg_bases = {os.path.splitext(os.path.basename(f))[0] for f in tile_files}
        data_bases = {os.path.splitext(os.path.basename(f))[0] for f in data_files}
        if svg_bases != data_bases:
            return ResultMSG.failure("data files and svg files do not match")

        # Check if each tile has a blank version and the other way around
        blank_pattern = os.path.join(svg_dir, 'tile_[a-zA-Z]_blank.svg')
        blank_files = glob.glob(blank_pattern)
        blank_bases = {os.path.splitext(os.path.basename(f))[0][0:6] for f in blank_files}
        if svg_bases != blank_bases:
            return ResultMSG.failure("svg tile and svg blank tile files do not match")

        # TILES
        for file in tile_files:
            tile_id = os.path.splitext(os.path.basename(file))[0]
            blank_file = os.path.join(svg_dir, tile_id + "_blank.svg")
            self.svg_tiles.append(DraggableTile(tile_id, file, blank_file, Vector2(500,500), scale=0.4))

        # DATA
        for file in data_files:
            self.tile_data.append(file)

        return ResultMSG.success()
