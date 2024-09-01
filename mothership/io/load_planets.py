import json
import os
import glob
from pygame import Vector2
from mothership.gui.planet_view.tile import DraggableTile
from planets.code.tile_data import Tile


class PlanetLoader:
    """
    Class responsible for loading and holding the planet data (i.e. the svg files and data files).
    Has some error handling but largely assumes that all files are formatted correctly.
    """

    planet_directory: str

    svg_tiles: list[DraggableTile]
    tile_data: list[Tile]
    base_tile: Tile

    def __init__(self, planet_dir: str):
        self.planet_directory = planet_dir
        self.svg_tiles = list()
        self.tile_data = list()

    def load(self):
        """
        Loads the planet data from the class' planet_directory. By the end of the function, the class'
        svg_tiles, tile_data and base_tile variables are set, assuming that the datafiles are formatted correctly.
        """
        
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
            raise FileNotFoundError("data files and svg files do not match")

        # Check if each tile has a blank version and the other way around
        blank_pattern = os.path.join(svg_dir, 'tile_[a-zA-Z]_blank.svg')
        blank_files = glob.glob(blank_pattern)
        blank_bases = {os.path.splitext(os.path.basename(f))[0][0:6] for f in blank_files}
        if svg_bases != blank_bases:
            raise FileNotFoundError("svg tile and svg blank tile files do not match")

        # TILES
        for file in tile_files:
            tile_id = os.path.splitext(os.path.basename(file))[0]
            print(f"Loading svg for: {tile_id}...")
            blank_file = os.path.join(svg_dir, tile_id + "_blank.svg")
            self.svg_tiles.append(DraggableTile(tile_id, file, blank_file, Vector2(500, 500), scale=0.4))

        # BASE_TILE
        print("Loading data for: base_tile...")
        base_tile_path = os.path.join(data_dir, "base_tile.json")
        if not os.path.isfile(base_tile_path):
            raise FileNotFoundError("could not find base_tile.json")
        data = open(base_tile_path, "r").read()
        self.base_tile = Tile.as_base_tile(json.loads(data))

        # DATA
        for file in data_files:
            data = open(file, "r").read()
            tile_id = os.path.splitext(os.path.basename(file))[0]

            print(f"Loading data for: {tile_id}...", flush=True)
            self.tile_data.append(Tile.from_json_dict(json.loads(data), self.base_tile, tile_id))
