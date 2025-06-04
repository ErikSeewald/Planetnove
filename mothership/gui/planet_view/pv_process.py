import os
import time
from multiprocessing import Process, Pipe, connection
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.io.load_tiles import TileLoader
from mothership.update_event import UpdateEvent
from planets.code.node import Node

class PVProcess:
    """
    Class responsible for extending the planet view into its own process that can communicate
    with the main process. This was added in later because the pygame and dpg cannot share the same opengl
    context on a single process on Linux X11. That is why this adapter exists to bridge the gap without
    having to change too much of the original code.
    """
    parent_conn: connection.Connection
    child_conn: connection.Connection

    def __init__(self):
        self.parent_conn, self.child_conn = Pipe()

        self.switch = False

    def start(self):
        """
        Starts the independent planet view process.
        """

        Process(target=PVProcess.child_process_target, args=(self.child_conn, )).start()

    def update(self) -> list[UpdateEvent]:
        """
        Calls update() on the planet view process, thereby updating the planet view and returning
        update events.
        """

        self.parent_conn.send("update")
        return self.parent_conn.recv()

    def get_mode(self) -> PlanetView.Mode:
        """
        Returns the current mode of the planet view process.
        """

        self.parent_conn.send("get_mode")
        return self.parent_conn.recv()

    def reset_planet(self):
        """
        Calls reset_planet() on the planet view process.
        """

        self.parent_conn.send("reset_planet")

    def can_finish_planet(self) -> bool:
        """
        Returns whether the planet view can parse and finish the planet that is currently being edited.
        """

        self.parent_conn.send("can_finish_planet")
        return self.parent_conn.recv()

    def finish_planet(self):
        """
        Schedules a planet view mode switch for the next update, provided that can_finish_planet() is true.
        """

        self.parent_conn.send("finish_planet")

    def switch_to_edit(self):
        """
        Switches the planet view mode to EDIT.
        """

        self.parent_conn.send("switch_to_edit")

    def get_planet(self) -> dict:
        """
        Returns the planet view's planet as a dict.
        """

        self.parent_conn.send("get_planet")
        return self.parent_conn.recv()

    @staticmethod
    def child_process_target(conn: connection.Connection):
        """
        This function is the starting point of the planet view process and acts as an adapter
        for process setup that planet_view.py is unaware of.
        """

        import pygame # Has to happen here to avoid pygame messing with opengl on the main process
        pygame.init()


        planet_loader = TileLoader(os.path.join(os.getcwd(), "planets"))
        planet_loader.load()

        planet_view = PlanetView(planet_loader.svg_tiles, planet_loader.tile_data)

        # PIPE COMMUNICATION LOOP
        while True:
            msg = conn.recv()

            if msg == "update":
                pv_events = planet_view.update()
                conn.send(pv_events)

            elif msg == "get_mode":
                conn.send(planet_view.mode)

            elif msg == "reset_planet":
                planet_view.reset_planet()

            elif msg == "can_finish_planet":
                conn.send(planet_view.can_finish_planet())

            elif msg == "finish_planet":
                planet_view.finish_planet()

            elif msg == "switch_to_edit":
                planet_view.switch_mode(PlanetView.Mode.EDIT)

            elif msg == "get_planet":
                conn.send(planet_view.planet.to_dict())
