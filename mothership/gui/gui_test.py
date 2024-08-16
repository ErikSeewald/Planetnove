import pygame
import sys
import os
from mothership.gui.tile import DraggableTile


def main():
    pygame.init()

    # SCREEN
    screen: pygame.Surface = pygame.display.set_mode((1400, 1000))
    pygame.display.set_caption("Tile viewer")

    clock = pygame.time.Clock()
    svg_file = os.path.join(os.getcwd(), "planets", "svg", "tile_a.svg")
    image = DraggableTile(svg_file, x=500, y=500, scale=0.35)

    while True:
        screen.fill((26, 26, 26))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            image.handle_event(event)

        # RENDER
        image.draw(screen)
        pygame.display.flip()
        clock.tick(60)
