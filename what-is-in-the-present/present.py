import pygame

class Present():
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('data/assets/present.png')
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.x = 420
        self.rect.y = 60




