import os
from mothership.gui.gui_core import GUICore
from mothership.io.load_planets import PlanetLoader
from mothership.mothership import Mothership


def init():
    # PLANET TILES
    planet_loader = PlanetLoader(os.path.join(os.getcwd(), "planets"))
    planet_loader.load()

    # MOTHERSHIP
    mothership = Mothership()

    # GUI
    gui = GUICore(planet_loader.svg_tiles, planet_loader.tile_data, mothership)
    gui.loop()


if __name__ == "__main__":
    init()
