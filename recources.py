
import pygame
from consts import *

class ResourceNode:
    def __init__(self, x, y, amount):
        self.x = x
        self.y = y
        self.amount = amount
        self.max_amount = amount

    def gather(self, amount):
        gathered = min(amount, self.amount)
        self.amount -= gathered
        return gathered

    def is_depleted(self):
        return self.amount <= 0

class Minerals(ResourceNode):
    def __init__(self, x, y, amount):
        super().__init__(x, y, amount)
        self.color = GOLD
        self.name = "Минералы"

    def draw(self, screen, font):
        if screen is None:
            return
        x = self.x * GRID_SIZE
        y = self.y * GRID_SIZE
        pygame.draw.rect(screen, self.color, (x + 5, y + 5, GRID_SIZE - 10, GRID_SIZE - 10))
        for i in range(3):
            cx = x + 10 + i * 8
            cy = y + GRID_SIZE // 2
            pygame.draw.polygon(screen, WHITE, [
                (cx, cy - 8),
                (cx - 4, cy),
                (cx + 4, cy)
            ])
        amount_text = font.render(str(self.amount), True, BLACK)
        screen.blit(amount_text, (x + 5, y + 25))


class Gas(ResourceNode):
    def __init__(self, x, y, amount):
        super().__init__(x, y, amount)
        self.color = CYAN
        self.name = "Газ"

    def draw(self, screen, font):
        if screen is None:
            return
        x = self.x * GRID_SIZE
        y = self.y * GRID_SIZE
        pygame.draw.rect(screen, self.color, (x + 5, y + 5, GRID_SIZE - 10, GRID_SIZE - 10))
        pygame.draw.circle(screen, WHITE, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), 8)
        pygame.draw.circle(screen, self.color, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), 6)
        amount_text = font.render(str(self.amount), True, BLACK)
        screen.blit(amount_text, (x + 5, y + 25))
