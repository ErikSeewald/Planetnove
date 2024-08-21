from abc import ABC, abstractmethod


class SubGUI(ABC):
    """
    Abstract class representing a sub-window of the dearpygui viewport
    """

    tag: str # The dpg tag

    def __init__(self, tag: str, gui_core) -> None:
        self.tag = tag
        self._gui_core = gui_core

    @abstractmethod
    def update(self) -> None:
        """
        Update the local state of the sub-window.
        """
        pass
