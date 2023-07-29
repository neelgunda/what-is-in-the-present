import pygame

class Lives():
    def __init__(self):
        super().__init__()
        self.fullLife = pygame.transform.scale(pygame.image.load('data/assets/filled-heart.png'), (65, 65))
        self.noLife = pygame.transform.scale(pygame.image.load('data/assets/unfilled-heart.png'), (44, 44))
    