import pygame

# Initialize Pygame
pygame.init()

# Create a font object. You can use a system font or load a specific font file.
font_size = 30
font = pygame.font.SysFont(None, 18)  # None uses the default font. You can also specify a font name.

# Define the text you want to measure
text = "beltix"

# Use the Font.size() method to get the width and height of the text
text_width, text_height = font.size(text)

print(f"Width of '{text}' when rendered: {text_width} pixels")
print(f"Height of '{text}' when rendered: {text_height} pixels")

# Quit Pygame when done
pygame.quit()