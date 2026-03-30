import pygame
from consts import *

class Building:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player
        self.selected = False
        self.production_queue = []  # очередь производства юнитов
        self.production_progress = 0
        self.max_hp = 500
        self.hp = 500
        self.color = (0, 100, 200) if player == 'blue' else (200, 0, 0)
        self.name = "База"
        self.size = 2

    def get_occupied_cells(self): #Возвращает все клетки, занятые зданием
        cells = []
        for dx in range(self.size):
            for dy in range(self.size):
                cells.append((self.x + dx, self.y + dy))
        return cells

    def can_build_here(self, x, y, game): #Проверяет, можно ли построить здание здесь
        for dx in range(self.size):
            for dy in range(self.size):
                nx, ny = x + dx, y + dy
                # Проверяем границы
                if nx >= GRID_WIDTH or ny >= GRID_HEIGHT:
                    return False
                # Проверяем, не занято ли
                if game.is_cell_occupied(nx, ny):
                    return False
        return True

    def draw(self, screen, font):
        #Рисуем здание (может занимать несколько клеток)
        if screen is None:
            return
        for dx in range(self.size):
            for dy in range(self.size):
                x = (self.x + dx) * GRID_SIZE
                y = (self.y + dy) * GRID_SIZE
                # Основной цвет
                color = self.color
                if self.selected:
                    # Рисуем рамку выделения
                    pygame.draw.rect(screen, YELLOW, (x, y, GRID_SIZE * self.size, GRID_SIZE * self.size), 3)
                # Рисуем клетку здания
                pygame.draw.rect(screen, color, (x + 2, y + 2, GRID_SIZE - 4, GRID_SIZE - 4))
                pygame.draw.rect(screen, BLACK, (x, y, GRID_SIZE, GRID_SIZE), 1)
        # Название здания
        text = font.render(self.name, True, BLACK)
        screen.blit(text, (self.x * GRID_SIZE + 5, self.y * GRID_SIZE - 15))
        # Полоска здоровья (рисуем над зданием)
        health_width = GRID_SIZE * self.size - 10
        health_height = 5
        health_x = self.x * GRID_SIZE + 5
        health_y = self.y * GRID_SIZE - 10
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        current_health_width = health_width * (self.hp / self.max_hp)
        pygame.draw.rect(screen, GREEN, (health_x, health_y, current_health_width, health_height))
        # Если есть очередь производства, показываем прогресс
        if self.production_queue:
            prog_text = font.render(f" {len(self.production_queue)}", True, BLACK)
            screen.blit(prog_text, (self.x * GRID_SIZE + 5, self.y * GRID_SIZE + 25))

class Base(Building):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 500
        self.hp = 500
        self.color = (0, 100, 200) if player == 'blue' else (200, 0, 0)
        self.name = "База"
        self.size = 2

class Barracks(Building):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 200
        self.hp = 200
        self.color = (100, 100, 200) if player == 'blue' else (200, 100, 100)
        self.name = "Казармы"
        self.size = 1

    def start_production(self, unit_type, cost): # Начинает производство юнита
        self.production_queue.append({
            'type': unit_type,
            'progress': 0,
            'cost': cost,
            'turns_needed': 3
        })

    def update_production(self): # Обновляет прогресс производства
        if self.production_queue:
            self.production_progress += 1
            if self.production_progress >= 3:
                return self.production_queue.pop(0)
        return None

class Factory(Building):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 250
        self.hp = 250
        self.color = (150, 150, 200) if player == 'blue' else (200, 150, 150)
        self.name = "Фабрика"
        self.size = 1

class Tower(Building):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.max_hp = 150
        self.hp = 150
        self.attack = 20
        self.attack_range = 2
        self.color = (0, 200, 200) if player == 'blue' else (200, 0, 200)
        self.name = "Башня"
        self.size = 1