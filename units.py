import math
import pygame
from consts import *

class Unit:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player
        self.hp = 50
        self.attack_range = 2
        self.speed = 2
        self.selected = False
        self.has_acted = False
        self.action_type = None
        self.action_target = None

    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0

    def distance_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def can_attack(self, target):
        return self.distance_to(target) <= self.attack_range

    def get_possible_moves(self):
        moves = []
        for dx in range(-self.speed, self.speed + 1):
            for dy in range(-self.speed, self.speed + 1):
                if abs(dx) + abs(dy) <= self.speed:
                    new_x = self.x + dx
                    new_y = self.y + dy
                    if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                        moves.append((new_x, new_y))
        return moves

    def reset_turn(self):
        self.has_acted = False
        self.action_type = None
        self.action_target = None


class Heavy(Unit):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 120
        self.hp = 120
        self.attack = 30
        self.attack_range = 1
        self.speed = 1
        self.color = (0, 0, 150) if player == 'blue' else (150, 0, 0)
        self.name = "Тяжелый"
        self.cost = {'minerals': 100, 'gas': 25}

    def draw(self, screen, font, show_actions=True):
        if screen is None:
            return
        screen_x = self.x * GRID_SIZE + GRID_SIZE // 2
        screen_y = self.y * GRID_SIZE + GRID_SIZE // 2
        if self.selected:
            pygame.draw.circle(screen, YELLOW, (screen_x, screen_y), GRID_SIZE // 2 + 3, 3)
        color = self.color
        if self.has_acted:
            color = tuple(c // 2 for c in color)
        radius = GRID_SIZE // 2 - 2
        rect = pygame.Rect(screen_x - radius, screen_y - radius, radius * 2, radius * 2)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        health_width = 30
        health_height = 4
        health_x = screen_x - health_width // 2
        health_y = screen_y - radius - 8
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        current_health_width = health_width * (self.hp / self.max_hp)
        pygame.draw.rect(screen, GREEN, (health_x, health_y, current_health_width, health_height))
        type_letter = self.name[0]
        text = font.render(type_letter, True, BLACK)
        text_rect = text.get_rect(center=(screen_x, screen_y))
        screen.blit(text, text_rect)

class Light(Unit):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 50
        self.hp = 50
        self.attack = 15
        self.attack_range = 2
        self.speed = 3
        self.color = (150, 150, 255) if player == 'blue' else (255, 150, 150)
        self.name = "Легкий"
        self.cost = {'minerals': 50, 'gas': 0}

    def draw(self, screen, font, show_actions=True):
        if screen is None:
            return
        screen_x = self.x * GRID_SIZE + GRID_SIZE // 2
        screen_y = self.y * GRID_SIZE + GRID_SIZE // 2
        if self.selected:
            pygame.draw.circle(screen, YELLOW, (screen_x, screen_y), GRID_SIZE // 2 + 3, 3)
        color = self.color
        if self.has_acted:
            color = tuple(c // 2 for c in color)
        radius = GRID_SIZE // 2 - 2
        pygame.draw.circle(screen, color, (screen_x, screen_y), radius)
        pygame.draw.circle(screen, BLACK, (screen_x, screen_y), radius, 2)
        health_width = 30
        health_height = 4
        health_x = screen_x - health_width // 2
        health_y = screen_y - radius - 8
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        current_health_width = health_width * (self.hp / self.max_hp)
        pygame.draw.rect(screen, GREEN, (health_x, health_y, current_health_width, health_height))
        type_letter = self.name[0]
        text = font.render(type_letter, True, BLACK)
        text_rect = text.get_rect(center=(screen_x, screen_y))
        screen.blit(text, text_rect)


class Ranged(Unit):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 40
        self.hp = 40
        self.attack = 20
        self.attack_range = 4
        self.speed = 2
        self.color = (50, 50, 255) if player == 'blue' else (255, 50, 50)
        self.name = "Дальний"
        self.cost = {'minerals': 75, 'gas': 50}

    def draw(self, screen, font, show_actions=True):
        if screen is None:
            return
        screen_x = self.x * GRID_SIZE + GRID_SIZE // 2
        screen_y = self.y * GRID_SIZE + GRID_SIZE // 2
        if self.selected:
            pygame.draw.circle(screen, YELLOW, (screen_x, screen_y), GRID_SIZE // 2 + 3, 3)
        color = self.color
        if self.has_acted:
            color = tuple(c // 2 for c in color)
        radius = GRID_SIZE // 2 - 2
        points = [
            (screen_x, screen_y - radius),
            (screen_x - radius, screen_y + radius // 2),
            (screen_x + radius, screen_y + radius // 2)
        ]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, BLACK, points, 2)
        health_width = 30
        health_height = 4
        health_x = screen_x - health_width // 2
        health_y = screen_y - radius - 8
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        current_health_width = health_width * (self.hp / self.max_hp)
        pygame.draw.rect(screen, GREEN, (health_x, health_y, current_health_width, health_height))
        type_letter = self.name[0]
        text = font.render(type_letter, True, BLACK)
        text_rect = text.get_rect(center=(screen_x, screen_y))
        screen.blit(text, text_rect)


class Worker(Unit):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 30
        self.hp = 30
        self.attack = 5
        self.attack_range = 1
        self.speed = 2
        self.color = (100, 100, 255) if player == 'blue' else (255, 100, 100)
        self.name = "Рабочий"
        self.cost = {'minerals': 25, 'gas': 0}
        self.gather_rate = 10
        self.carrying = 0
        self.gather_target = None

    def draw(self, screen, font, show_actions=True):
        if screen is None:
            return
        screen_x = self.x * GRID_SIZE + GRID_SIZE // 2
        screen_y = self.y * GRID_SIZE + GRID_SIZE // 2
        if self.selected:
            pygame.draw.circle(screen, YELLOW, (screen_x, screen_y), GRID_SIZE // 2 + 3, 3)
        color = self.color
        if self.has_acted:
            color = tuple(c // 2 for c in color)
        radius = GRID_SIZE // 2 - 2
        points = [
            (screen_x, screen_y - radius),
            (screen_x + radius, screen_y),
            (screen_x, screen_y + radius),
            (screen_x - radius, screen_y)
        ]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, BLACK, points, 2)
        health_width = 30
        health_height = 4
        health_x = screen_x - health_width // 2
        health_y = screen_y - radius - 8
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        current_health_width = health_width * (self.hp / self.max_hp)
        pygame.draw.rect(screen, GREEN, (health_x, health_y, current_health_width, health_height))
        if self.carrying > 0:
            carry_text = font.render(str(self.carrying), True, GOLD)
            screen.blit(carry_text, (screen_x - 5, screen_y - 20))
        type_letter = self.name[0]
        text = font.render(type_letter, True, BLACK)
        text_rect = text.get_rect(center=(screen_x, screen_y))
        screen.blit(text, text_rect)