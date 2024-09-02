from __future__ import annotations
import dearpygui.dearpygui as dpg
import numpy as np
from mothership.gui import theme
from mothership.gui.sub_gui import SubGUI
from mothership.update_event import UpdateEvent


class TankMapSubGUI(SubGUI):

    MAX_FRAMES = 3
    frame_tags: list[str]
    cur_frame_index: int

    def __init__(self, tag: str, gui_core):
        super().__init__(tag, gui_core)
        self.frame_tags = list()
        self.cur_frame_index = 0

        # WINDOW
        with dpg.window(label="Tank internal map", width=630, height=650, no_close=True, tag=self.tag, no_move=True,
                        pos=[430, 10], horizontal_scrollbar=True) as window_id:
            theme.apply_window_theme(window_id)
            with dpg.group(tag="image_container"):
                pass  # Placeholder for the image container

    def update(self) -> list[UpdateEvent]:
        return list()

    @staticmethod
    def remove_image():
        if dpg.does_item_exist("image"):
            dpg.delete_item("image")

    def update_image(self, image: np.ndarray):
        texture_tag = f"frame_{self.cur_frame_index}"

        # Normalize image format
        if image.dtype != np.float32:
            image = image.astype(np.float32) / 255.0

        # Delete the oldest frame if necessary
        if len(self.frame_tags) >= self.MAX_FRAMES:
            oldest_tag = self.frame_tags.pop(0)
            dpg.delete_item(oldest_tag)

        # Add new texture to the texture registry
        with dpg.texture_registry(show=False):
            height, width = image.shape[:2]
            dpg.add_static_texture(width, height, image.flatten(), tag=texture_tag)

        # Update the image display
        if dpg.does_item_exist("image"):
            dpg.delete_item("image")
        dpg.add_image(texture_tag, parent="image_container", tag="image")

        # Update frames
        self.frame_tags.append(texture_tag)
        self.cur_frame_index = (self.cur_frame_index + 1) % self.MAX_FRAMES
