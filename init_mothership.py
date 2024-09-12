import os
from mothership.io.load_tiles import TileLoader
from mothership.mothership import Mothership


def init():
    # PLANET TILES
    planet_loader = TileLoader(os.path.join(os.getcwd(), "planets"))
    planet_loader.load()

    # MOTHERSHIP
    mothership = Mothership(planet_loader.svg_tiles, planet_loader.tile_data)
    mothership.loop()


if __name__ == "__main__":
    init()
