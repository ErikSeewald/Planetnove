"""
Module defining the dearpygui theme used for the mothership gui.
"""

import dearpygui.dearpygui as dpg


def apply_window_theme(window_id: int | str) -> None:
    with dpg.theme() as window_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (80, 85, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (60, 150, 80, 255))

    dpg.bind_item_theme(window_id, window_theme)


def apply_button_theme(button_id: int | str) -> None:
    with dpg.theme() as button_theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 110, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 150, 110, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (110, 180, 140, 255))

        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (80, 80, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (80, 80, 80, 255))

    dpg.bind_item_theme(button_id, button_theme)


def apply_header_theme(header_id: int | str) -> None:
    with dpg.theme() as header_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (70, 130, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (100, 160, 110, 255))

    dpg.bind_item_theme(header_id, header_theme)


def apply_text_theme(text_id: int | str) -> None:
    with dpg.theme() as text_theme:
        with dpg.theme_component(dpg.mvText):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

    dpg.bind_item_theme(text_id, text_theme)


def apply_error_msg_theme(text_id: int | str) -> None:
    with dpg.theme() as msg_theme:
        with dpg.theme_component(dpg.mvText):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 100, 80, 255))

    dpg.bind_item_theme(text_id, msg_theme)


def apply_input_theme(input_id: int | str) -> None:
    pass
