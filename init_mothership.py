import os
from mothership.gui.gui_core import GUICore
from mothership.io.load_planets import PlanetLoader


def init():
    # PLANET TILES
    planet_loader = PlanetLoader(os.path.join(os.getcwd(), "planets"))
    planet_loader.load()

    # GUI
    gui = GUICore(planet_loader.svg_tiles, planet_loader.tile_data)
    gui.loop()


if __name__ == "__main__":
    init()
