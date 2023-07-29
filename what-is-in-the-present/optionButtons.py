import pygame

class OptionButton:
    def __init__(self, text, sound_file, pos):
        self.text = text
        self.sound_file = sound_file
        self.rect = pygame.Rect(pos[0], pos[1], 200, 30)
        self.selected = False