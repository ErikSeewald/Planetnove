import os
import time
import traceback
from typing import Any
import pygame
from multiprocessing import Process, Event, Queue
from mothership.gui.planet_view.planet_view import PlanetView
from mothership.io.load_tiles import TileLoader
from mothership.update_event import UpdateEvent

class PVProcess:
    """
    Class responsible for extending the planet view into its own process that can communicate
    with the main process. This was added in later because the pygame and dpg cannot share the same opengl
    context on a single process on Linux X11. That is why this adapter exists to bridge the gap without
    having to change too much of the original code.
    """

    parent_to_child: Queue
    child_to_parent: Queue

    child: Process
    quit_event: Event

    def __init__(self):
        self.parent_to_child = Queue()
        self.child_to_parent = Queue()

        self.quit_event = Event()
        self.switch = False

    def start(self):
        """
        Starts the independent planet view process.
        """
        self.child = Process(target=PVProcess.child_process_target, args=(self.parent_to_child,
                                                                          self.child_to_parent, self.quit_event))
        self.child.start()

        msg = self.child_to_parent.get()
        if msg == "failure":
            self.child.join()
            exit(1)

    def exit(self):
        """
        Exits the planet view process.
        """
        self._safe_send("exit")
        self.child.join()

    def _safe_send(self, message: str):
        """
        Sends the given method to the planet view process while checking for its quit event.
        """

        if self.quit_event.is_set():
            self.child.join()
            exit(0)
        self.parent_to_child.put(message)

    def _safe_recv(self) -> Any:
        """
        Safely receives a message from the planet view process.
        """

        return self.child_to_parent.get()

    def update(self) -> list[UpdateEvent]:
        """
        Calls update() on the planet view process, thereby updating the planet view and returning
        update events.
        """

        self._safe_send("update")
        events = self._safe_recv()
        if not isinstance(events, list):
            return list() # Fallback on incorrect recv
        return events

    def get_mode(self) -> PlanetView.Mode:
        """
        Returns the current mode of the planet view process.
        """

        self._safe_send("get_mode")
        return self._safe_recv()

    def reset_planet(self):
        """
        Calls reset_planet() on the planet view process.
        """

        self._safe_send("reset_planet")

    def can_finish_planet(self) -> bool:
        """
        Returns whether the planet view can parse and finish the planet that is currently being edited.
        """

        self._safe_send("can_finish_planet")
        return self._safe_recv()

    def finish_planet(self):
        """
        Schedules a planet view mode switch for the next update, provided that can_finish_planet() is true.
        """

        self._safe_send("finish_planet")

    def switch_to_edit(self):
        """
        Switches the planet view mode to EDIT.
        """

        self._safe_send("switch_to_edit")

    def get_planet(self) -> dict:
        """
        Returns the planet view's planet as a dict.
        """

        self._safe_send("get_planet")
        return self._safe_recv()

    @staticmethod
    def child_process_target(p2c: Queue, c2p: Queue, quit_event: Event):
        """
        This function is the starting point of the planet view process and acts as an adapter
        for process setup that planet_view.py is unaware of.
        """

        pygame.init()

        # TRY TO LOAD AND PARSE PLANET DATA, ELSE EXIT AND LET PARENT KNOW
        try:
            planet_loader = TileLoader(os.path.join(os.getcwd(), "planets"))
            planet_loader.load()
            planet_view = PlanetView(planet_loader.svg_tiles, planet_loader.tile_data)
        except Exception:
            traceback.print_exc()
            c2p.put("failure")
            return
        c2p.put("success")

        # COMMUNICATION LOOP
        while True:
            if planet_view.has_quit:
                quit_event.set()
                exit(0)

            msg = p2c.get()
            if msg == "exit":
                exit(0)

            if msg == "update":
                pv_events = planet_view.update()
                c2p.put(pv_events)

            elif msg == "get_mode":
                c2p.put(planet_view.mode)

            elif msg == "reset_planet":
                planet_view.reset_planet()

            elif msg == "can_finish_planet":
                c2p.put(planet_view.can_finish_planet())

            elif msg == "finish_planet":
                planet_view.finish_planet()

            elif msg == "switch_to_edit":
                planet_view.switch_mode(PlanetView.Mode.EDIT)

            elif msg == "get_planet":
                c2p.put(planet_view.planet.to_dict())