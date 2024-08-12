import pygame
import cairosvg
import io


class DraggableTile:
    """
    Draggable image class representing a single map tile. Created from svg and data files.
    """

    image: pygame.Surface
    rect: pygame.Rect

    #DRAGGING
    is_dragging: bool
    mouse_x: float
    mouse_y: float
    offset_x: float
    offset_y: float

    def __init__(self, svg_file: str, x: float, y: float, scale: float = 1.0):

        # Assumes that the user has created the tile svg with the correct resolution :)
        original_size = 1000
        scaled_width = int(original_size * scale)
        scaled_height = int(original_size * scale)

        # CONVERT TO PNG AND SCALE
        png_data = cairosvg.svg2png(url=svg_file, output_width=scaled_width, output_height=scaled_height)
        image = pygame.image.load(io.BytesIO(png_data))

        # CREATE PYGAME SURFACE
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_dragging = False

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

    def handle_event(self, event: pygame.event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self.mouse_x, self.mouse_y = event.pos
                self.offset_x = self.rect.x - self.mouse_x
                self.offset_y = self.rect.y - self.mouse_y

        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self.rect.x = event.pos[0] + self.offset_x
                self.rect.y = event.pos[1] + self.offset_y

