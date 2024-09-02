from abc import ABC, abstractmethod
from mothership.update_event import UpdateEvent


class SubGUI(ABC):
    """
    Abstract base class representing a sub-window of the dearpygui viewport
    """

    tag: str # The dpg tag

    def __init__(self, tag: str, gui_core) -> None:
        self.tag = tag
        self._gui_core = gui_core

    @abstractmethod
    def update(self) -> list[UpdateEvent]:
        """
        Update the local state of the sub-window.
        """
        pass
