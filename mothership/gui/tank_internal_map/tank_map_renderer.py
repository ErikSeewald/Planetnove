import math

import numpy as np
import pygame
from pygame import Vector2
from planets.code.planet import Planet
from planets.code.route import Route
from util.direction import Direction


class TankMapRenderer:
    """
    Class rendering the internal map of the tank robot. Unlike 'PlanetView', displaying the rendered image is not
    handled here but instead in the corresponding SubGUI.
    """

    # COLORS
    WHITE = (255, 255, 255)
    GREY = (90, 90, 90)
    BACKGROUND_COL = (25, 25, 25)
    NODE_COL_RED = (150, 50, 40)
    NODE_COL_GREEN = (10, 60, 35)
    TARGET_COLOR = (20, 70, 130)
    TARGET_PATH_COLOR = (60, 115, 245)

    COORD_TO_PIXEL = 100

    @staticmethod
    def render_map_image(planet: Planet, cur_node: str, target_node: str,
                         target_route: Route, depart_dir: Direction) -> np.ndarray:
        """
        Renders an image of the given data. The rendered image can have different scaling based
        on the coordinates of the planet nodes.
        Assumes pygame is initialized.

        :return: np.ndarray of the rendered image.
        """

        # FONT
        pygame.font.init()
        font = pygame.font.SysFont(None, 18)

        # SURFACE
        # Find min and max coordinates among all nodes
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        for node in planet.nodes.values():
            min_x = min(min_x, node.coord.x)
            min_y = min(min_y, node.coord.y)
            max_x = max(max_x, node.coord.x)
            max_y = max(max_y, node.coord.y)

        # Calculate width and height needed for the image, including a margin on either side
        min_size = 400
        width = max(min_size, int((max_x - min_x) * TankMapRenderer.COORD_TO_PIXEL) + 200)
        height = max(min_size, int((max_y - min_y) * TankMapRenderer.COORD_TO_PIXEL) + 200)

        image_surface: pygame.Surface = pygame.Surface((width, height))
        image_surface.fill(TankMapRenderer.BACKGROUND_COL)

        # UNEXPLORED NODE PATHS (Separate from both paths and node loops for rendering order)
        for node_id, node in planet.nodes.items():
            pos = TankMapRenderer._position_adjusted(node.coord, min_x, min_y, height)

            for direction in node.available_paths:
                if node.direction_to_path_id[direction] == "None":
                    path_pos = TankMapRenderer._offset_path_coord(pos, direction, is_unexplored=True)

                    color = TankMapRenderer.GREY
                    if node_id == cur_node and direction == depart_dir:
                        color = TankMapRenderer.NODE_COL_RED
                    pygame.draw.line(image_surface, color, pos, path_pos, width=2)

        # PATHS
        for path_id, path in planet.paths.items():
            node_a = planet.nodes.get(path.node_a)
            node_pos_a = TankMapRenderer._position_adjusted(node_a.coord, min_x, min_y, height)
            path_pos_a = TankMapRenderer._offset_path_coord(node_pos_a, path.direction_a, is_unexplored=False)

            node_b = planet.nodes.get(path.node_b)
            node_pos_b = TankMapRenderer._position_adjusted(node_b.coord, min_x, min_y, height)
            path_pos_b = TankMapRenderer._offset_path_coord(node_pos_b, path.direction_b, is_unexplored=False)

            color = TankMapRenderer.WHITE if path_id not in target_route.path_id_list \
                else TankMapRenderer.TARGET_PATH_COLOR
            pygame.draw.line(image_surface, color, node_pos_a, path_pos_a, width=2)
            pygame.draw.line(image_surface, color, path_pos_a, path_pos_b, width=2)
            pygame.draw.line(image_surface, color, path_pos_b, node_pos_b, width=2)

            # Special case for blocked paths: Draw X in the center
            if math.isinf(path.length):
                # Calculate midpoint
                mid_pos_x = (path_pos_a[0] + path_pos_b[0]) // 2
                mid_pos_y = (path_pos_a[1] + path_pos_b[1]) // 2

                # Draw X
                offset = 10
                pygame.draw.line(image_surface, TankMapRenderer.NODE_COL_RED, (mid_pos_x - offset, mid_pos_y - offset),
                                 (mid_pos_x + offset, mid_pos_y + offset), width=3)
                pygame.draw.line(image_surface, TankMapRenderer.NODE_COL_RED, (mid_pos_x - offset, mid_pos_y + offset),
                                 (mid_pos_x + offset, mid_pos_y - offset), width=3)

            # Special cases for non-inf loop-back paths that cannot be drawn well
            elif path.node_a == path.node_b:
                if path.direction_a == path.direction_b:
                    abbr = path.direction_a.abbreviation()
                    pos = (path_pos_a[0] - 15, path_pos_a[1] - 5)
                    TankMapRenderer._draw_loop_path_text(pos, f"{abbr}->{abbr}", font, image_surface)

                if path.direction_a.is_inverse_of(path.direction_b):
                    text = f"{path.direction_a.abbreviation()}->{path.direction_b.abbreviation()}"
                    pos = (path_pos_a[0] - 15, path_pos_a[1] - 5)
                    TankMapRenderer._draw_loop_path_text(pos, text, font, image_surface)

                    text = f"{path.direction_b.abbreviation()}->{path.direction_a.abbreviation()}"
                    pos = (path_pos_b[0] - 15, path_pos_b[1] - 5)
                    TankMapRenderer._draw_loop_path_text(pos, text, font, image_surface)

        # NODES
        for node_id, node in planet.nodes.items():
            pos = TankMapRenderer._position_adjusted(node.coord, min_x, min_y, height)

            # Text surfaces
            node_text = TankMapRenderer.limit_text_to_width(node_id.lower(),
                                                            min_width=32, max_width=43, font=font)
            name_surface = font.render(node_text, True, TankMapRenderer.WHITE)

            coord_text = TankMapRenderer.limit_text_to_width(node.coord.__str__(),
                                                             min_width=32, max_width=43, font=font)
            coord_surface = font.render(coord_text, True, TankMapRenderer.WHITE)

            # Bounding box
            name_size = name_surface.get_size()
            coord_size = coord_surface.get_size()
            background_width = max(name_size[0], coord_size[0]) + 10
            background_height = name_size[1] + coord_size[1] + 10

            background_top_left = (pos[0] - 20, pos[1] - 20)

            color = TankMapRenderer.NODE_COL_GREEN
            if node_id == cur_node:
                color = TankMapRenderer.NODE_COL_RED
            elif node_id == target_node:
                color = TankMapRenderer.TARGET_COLOR

            pygame.draw.rect(image_surface, color,
                             (*background_top_left, background_width, background_height))

            # Blit text surfaces on top of the bounding box
            image_surface.blit(name_surface, (background_top_left[0] + 5, background_top_left[1] + 5))
            image_surface.blit(coord_surface, (background_top_left[0] + 5, background_top_left[1] + name_size[1] + 5))

        return TankMapRenderer._surface_to_numpy(image_surface)

    @staticmethod
    def limit_text_to_width(text: str, min_width: int, max_width: int, font: pygame.font) -> str:
        """
        Limits the given string to a minimum and maximum width based on the given font.
        Strings with too much width get abbreviated using '-' while strings with too little width get
        whitespace appended to them.
        """

        text_width, _ = font.size(text)
        while text_width > max_width:
            text = f"{text[:len(text) - 2]}-"
            text_width, _ = font.size(text)

        while text_width < min_width:
            text = f"{text} "
            text_width, _ = font.size(text)

        return text

    @staticmethod
    def _draw_loop_path_text(pos: (int, int), text: str, font: pygame.font, image_surface: pygame.surface):
        """
        Draws text indicating a looping path at the given position with the given font on the given image surface.
        """

        text_surface = font.render(text, True, TankMapRenderer.WHITE)
        pygame.draw.rect(image_surface, TankMapRenderer.BACKGROUND_COL,
                         (*pos, *text_surface.get_size()))
        image_surface.blit(text_surface, pos)

    @staticmethod
    def _offset_path_coord(position: (int, int), direction: Direction, is_unexplored: bool) -> (int, int):
        """
        Offsets the coordinate of a path's joint position (from where it attaches to another path's joint)
        based on which direction it is in. Additionally, it considers whether the path is still unexplored to
        display unexplored stubs differently.
        """

        extra_offset = 25 if is_unexplored else 0

        if direction == Direction.NORTH:
            return position[0], position[1] - 40
        elif direction == Direction.EAST:
            return position[0] + 65 - extra_offset, position[1]
        elif direction == Direction.SOUTH:
            return position[0], position[1] + 35
        elif direction == Direction.WEST:
            return position[0] - 40, position[1]
        else:
            return -1, -1

    @staticmethod
    def _position_adjusted(coord: Vector2, min_x: int, min_y: int, height: int) -> (int, int):
        """
        Adjusts the given node coordinates based on the given minimum x and y coordinates of nodes on the planet
        as well as the given image height.
        This way all nodes are positioned relative to the lowest and furthest left node and none exit the screen space.
        """

        node_x = int((coord.x - min_x) * TankMapRenderer.COORD_TO_PIXEL) + 100
        node_y = height - (int((coord.y - min_y) * TankMapRenderer.COORD_TO_PIXEL) + 100)

        return node_x, node_y

    @staticmethod
    def _surface_to_numpy(surface: pygame.Surface) -> np.ndarray:
        """
        Converts the given pygame surface to a numpy array.
        """

        image_data: bytes = pygame.image.tostring(surface, "RGBA")
        image_array: np.ndarray = np.frombuffer(image_data, dtype=np.uint8)
        return image_array.reshape((surface.get_height(), surface.get_width(), 4))
