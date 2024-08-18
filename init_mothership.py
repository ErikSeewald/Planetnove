import os
from mothership.gui.gui_core import GUICore
from mothership.io.load_planets import PlanetLoader


def init():
    # PLANET TILES
    planet_loader = PlanetLoader(os.path.join(os.getcwd(), "planets"))
    load_result = planet_loader.load()

    if not load_result.is_success():
        print(f"Failed to load planet files: {load_result.message}")
        return 1

    # GUI
    gui = GUICore(planet_loader.svg_tiles)
    gui.loop()


if __name__ == "__main__":
    init()
