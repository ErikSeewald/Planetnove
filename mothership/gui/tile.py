import pygame
from pygame.math import Vector2
import cairosvg
import io
from util.direction import Direction


class DraggableTile:
    """
    Draggable image class representing a single map tile. Created from svg and data files.
    Keeps track of rotation and joint connections to other tiles.
    """

    tile_id: str # e.g. 'tile_a'

    # DISPLAY
    blank_image: pygame.Surface
    detailed_image: pygame.Surface
    blank_mode: bool

    # CONNECTING
    joints: dict[Direction, list[str]] # Direction: list of 'None' or joint id (e.g. 'tile_b_joint_W2')
    snapped_in_place: bool

    # While rotate_right() is -90 degrees in screen space, it is +90 for rotation_deg so that it matches
    # the degree pattern used by global directions (e.g. EAST = 90, SOUTH = 180)
    rotation_deg: int

    #DRAGGING
    is_dragging: bool
    waiting_to_attach: bool # Used to let the main loop know that it should check for new joint attachments
    rect: pygame.Rect
    offset_x: float
    offset_y: float

    def __init__(self, tile_id: str, svg_file: str, svg_blank_file: str, pos: Vector2, scale: float = 1.0):

        self.tile_id = tile_id
        self.joints = {direction: ["None"] * 3
                       for direction in [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]}
        self.snapped_in_place = False

        # Assumes that the user has created the tile svg with the correct resolution :)
        original_size = 1000
        scaled_width = int(original_size * scale)
        scaled_height = int(original_size * scale)

        # DISPLAY
        png_data = cairosvg.svg2png(url=svg_file, output_width=scaled_width, output_height=scaled_height)
        self.detailed_image = pygame.image.load(io.BytesIO(png_data))

        png_blank_data = cairosvg.svg2png(url=svg_blank_file, output_width=scaled_width, output_height=scaled_height)
        self.blank_image = pygame.image.load(io.BytesIO(png_blank_data))
        self.blank_mode = False

        # DRAGGING
        self.rect = self.detailed_image.get_rect(topleft=(pos.x, pos.y))
        self.rotation_deg = 0
        self.is_dragging = False
        self.snapped_pos = False
        self.waiting_to_attach = False

    def set_blank_mode(self, mode: bool):
        """
        Sets the tiles blank mode.
        blank_mode = True -> Hide details
        """
        self.blank_mode = mode

    def snap_to_pos(self, x: float, y: float):
        self.rect.x = x
        self.rect.y = y
        self.snapped_in_place = True

    def detach_joints(self):
        """
        Detaches all of the tile's joints.
        """

        for joints in self.joints.values():
            for i in range(3):
                joints[i] = "None"

    def global_direction_to_local(self, global_dir: Direction):
        """
        Returns the local direction corresponding to the given global direction.
        For example, if the tile has been rotated by 90 degrees to the right, global NORTH is
        WEST locally because the tile's local NORTH is now facing the global EAST.
        """

        return global_dir.rotated(-self.rotation_deg)

    def local_direction_to_global(self, local_dir: Direction):
        """
        Returns the global direction corresponding to the given local direction.
        For example, if the tile has been rotated by 90 degrees to the right, local NORTH is global EAST.
        """

        return local_dir.rotated(self.rotation_deg)

    def is_joint_free(self, joint_dir: Direction, joint_num: int) -> bool:
        """
        Returns whether the given joint is free from any attachments.
        :param joint_dir: The direction of the joint
        :param joint_num: Which of the three joints at this direction (range [1-3])
        """

        return self.joints.get(joint_dir)[joint_num-1] == "None"

    def attach_joint(self, joint_dir: Direction, joint_num: int, attach: str):
        """
        Attaches the given foreign joint to the specified tile joint without updating the waiting_to_attach
        variable.
        :param joint_dir: The direction of the joint where the foreign joint is to be attached
        :param joint_num: Which of the three joints at this direction to attach the foreign joint to (range [1-3])
        :param attach: The joint id (e.g. 'tile_b_joint_N2') of the foreign joint to attach
        """

        self.joints.get(joint_dir)[joint_num-1] = attach

    def detach_joint(self, joint_dir: Direction, joint_num: int):
        """
        Detaches specified tile joint.
        :param joint_dir: The direction of the joint to detach
        :param joint_num: Which of the three joints at this direction to detach (range [1-3])
        """

        self.joints.get(joint_dir)[joint_num-1] = "None"

    def finish_attaching(self):
        """
        Finalizes the attachment process started by releasing the tile after dragging.
        If this method is not called, the tile will keep waiting for attachment calculations indefinitely.
        """

        self.waiting_to_attach = False

    def draw(self, screen: pygame.Surface):
        """
        Draws the tile to the given screen.
        """

        image: pygame.Surface
        if self.blank_mode:
            image = self.blank_image.copy()
            screen.blit(self.blank_image, self.rect)
        else:
            image = self.detailed_image.copy()

        image.set_alpha(255 if self.snapped_in_place else 128)
        screen.blit(image, self.rect)

    def rotate_right(self):
        """
        Rotates the tile to the right by 90 degrees.
        """

        self.detailed_image = pygame.transform.rotate(self.detailed_image, -90)
        self.blank_image = pygame.transform.rotate(self.blank_image, -90)

        # Use +90 to match the degree mapping of the direction class (e.g. EAST = 90)
        self.rotation_deg = (self.rotation_deg + 90) % 360

    def handle_drag_event(self, event: pygame.event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self.snapped_in_place = False
                self.detach_joints()
                mouse_x, mouse_y = event.pos
                self.offset_x = self.rect.x - mouse_x
                self.offset_y = self.rect.y - mouse_y

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.waiting_to_attach = True

            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self.rect.x = event.pos[0] + self.offset_x
                self.rect.y = event.pos[1] + self.offset_y
