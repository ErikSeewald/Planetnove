import numpy as np
import pygame
from pygame import Vector2

from planets.code.planet import Planet
from util.direction import Direction


class TankMapRenderer:
    """
    Class rendering the internal map of the tank robot. Unlike 'PlanetView', displaying the rendered image is not
    handled here but instead in the corresponding SubGUI.
    """

    WHITE = (255, 255, 255)
    BACKGROUND_COL = (25, 25, 25)
    NODE_COL_BRIGHT = (60, 130, 90)
    NODE_COL_DARK = (10, 60, 35)

    COORD_TO_PIXEL = 100

    @staticmethod
    def render_map_image(planet: Planet, cur_node: str) -> np.ndarray:
        """
        Assumes pygame is initialized.
        """

        if not planet:
            image_surface = pygame.Surface((100, 100))
            image_surface.fill(TankMapRenderer.BACKGROUND_COL)
            return TankMapRenderer._surface_to_numpy(image_surface)

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
        width = max(min_size, int((max_x - min_x) * TankMapRenderer.COORD_TO_PIXEL) + 100)
        height = max(min_size, int((max_y - min_y) * TankMapRenderer.COORD_TO_PIXEL) + 100)

        image_surface: pygame.Surface = pygame.Surface((width, height))
        image_surface.fill(TankMapRenderer.BACKGROUND_COL)

        # PATHS
        for path_id, path in planet.paths.items():
            node_a = planet.nodes.get(path.node_a)
            node_pos_a = TankMapRenderer._position_adjusted(node_a.coord, min_x, min_y, height)
            path_pos_a = TankMapRenderer._offset_path_coord(node_pos_a, path.direction_a)

            node_b = planet.nodes.get(path.node_b)
            node_pos_b = TankMapRenderer._position_adjusted(node_b.coord, min_x, min_y, height)
            path_pos_b = TankMapRenderer._offset_path_coord(node_pos_b, path.direction_b)

            pygame.draw.line(image_surface, TankMapRenderer.WHITE, node_pos_a, path_pos_a, width=2)
            pygame.draw.line(image_surface, TankMapRenderer.WHITE, path_pos_a, path_pos_b, width=2)
            pygame.draw.line(image_surface, TankMapRenderer.WHITE, path_pos_b, node_pos_b, width=2)

            # Special cases for loop-back paths that cannot be drawn well
            if path.node_a == path.node_b:
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
            if len(node_id) > 7:
                node_id = f"{node_id[:7]}-"
            name_surface = font.render(node_id, True, TankMapRenderer.WHITE)
            coord_surface = font.render(node.coord.__str__(), True, TankMapRenderer.WHITE)

            # Bounding box
            name_size = name_surface.get_size()
            coord_size = coord_surface.get_size()
            background_width = max(name_size[0], coord_size[0]) + 10
            background_height = name_size[1] + coord_size[1] + 10

            background_top_left = (pos[0] - 20, pos[1] - 20)

            color = TankMapRenderer.NODE_COL_BRIGHT if node_id == cur_node else TankMapRenderer.NODE_COL_DARK
            pygame.draw.rect(image_surface, color,
                             (*background_top_left, background_width, background_height))

            # Blit text surfaces on top of the bounding box
            image_surface.blit(name_surface, (background_top_left[0] + 5, background_top_left[1] + 5))
            image_surface.blit(coord_surface, (background_top_left[0] + 5, background_top_left[1] + name_size[1] + 5))

        return TankMapRenderer._surface_to_numpy(image_surface)

    @staticmethod
    def _draw_loop_path_text(pos: (int, int), text: str, font: pygame.font, image_surface: pygame.surface):
        text_surface = font.render(text, True, TankMapRenderer.WHITE)
        pygame.draw.rect(image_surface, TankMapRenderer.BACKGROUND_COL,
                         (*pos, *text_surface.get_size()))
        image_surface.blit(text_surface, pos)

    @staticmethod
    def _offset_path_coord(position: (int, int), direction: Direction) -> (int, int):
        if direction == Direction.NORTH:
            return position[0], position[1] - 45
        elif direction == Direction.EAST:
            return position[0] + 65, position[1]
        elif direction == Direction.SOUTH:
            return position[0], position[1] + 45
        elif direction == Direction.WEST:
            return position[0] - 45, position[1]
        else:
            return -1, -1

    @staticmethod
    def _position_adjusted(coord: Vector2, min_x: int, min_y: int, height: int) -> (int, int):
        node_x = int((coord.x - min_x) * TankMapRenderer.COORD_TO_PIXEL) + 50
        node_y = height - (int((coord.y - min_y) * TankMapRenderer.COORD_TO_PIXEL) + 50)

        return node_x, node_y

    @staticmethod
    def _surface_to_numpy(surface: pygame.Surface) -> np.ndarray:
        """
        Converts the given pygame surface to a numpy array.
        """

        image_data: bytes = pygame.image.tostring(surface, "RGBA")
        image_array: np.ndarray = np.frombuffer(image_data, dtype=np.uint8)
        return image_array.reshape((surface.get_height(), surface.get_width(), 4))

