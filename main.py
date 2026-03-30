import math
import pygame
from units import Heavy, Light, Ranged, Worker
from buildings import Building, Base, Barracks, Tower
from recources import Minerals, Gas
from consts import *
import random


class Drawer:
    def __init__(self, game):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RTS")
        self.game = game
        self.font = pygame.font.Font(None, 20)
        self.big_font = pygame.font.Font(None, 30)

    def draw_grid(self):
        for x in range(0, GAME_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, LIGHT_GRAY, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, LIGHT_GRAY, (0, y), (GAME_WIDTH, y))

    def draw_move_ranges(self):
        if not self.game.show_move_range or not self.game.selected_units:
            return
        for unit in self.game.selected_units:
            if not unit.has_acted:
                for x, y in unit.get_possible_moves():
                    if not self.game.is_cell_occupied(x, y):
                        s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                        s.fill((0, 255, 0, 50))
                        self.screen.blit(s, (x * GRID_SIZE, y * GRID_SIZE))

    def draw_attack_ranges(self):
        if not self.game.show_attack_range or not self.game.selected_units:
            return
        for unit in self.game.selected_units:
            if not unit.has_acted:
                cx = unit.x * GRID_SIZE + GRID_SIZE // 2
                cy = unit.y * GRID_SIZE + GRID_SIZE // 2
                radius = int(unit.attack_range * GRID_SIZE)
                s = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 0, 0, 30), (cx, cy), radius)
                self.screen.blit(s, (0, 0))

    def draw_tower_ranges(self):
        if not self.game.show_tower_range:
            return
        s = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for bld in self.game.buildings:
            if isinstance(bld, Tower):
                cx = bld.x * GRID_SIZE + GRID_SIZE // 2
                cy = bld.y * GRID_SIZE + GRID_SIZE // 2
                radius = int(bld.attack_range * GRID_SIZE)
                color = (0, 200, 255, 35) if bld.player == 'blue' else (255, 100, 0, 35)
                border = (0, 200, 255, 160) if bld.player == 'blue' else (255, 100, 0, 160)
                pygame.draw.circle(s, color, (cx, cy), radius)
                pygame.draw.circle(s, border, (cx, cy), radius, 2)
        self.screen.blit(s, (0, 0))

    def draw_pending_builds(self):
        for (bx, by, btype), turns_left in self.game.pending_builds.items():
            px = bx * GRID_SIZE
            py = by * GRID_SIZE
            s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            s.fill((255, 200, 0, 80))
            self.screen.blit(s, (px, py))
            pygame.draw.rect(self.screen, ORANGE, (px, py, GRID_SIZE, GRID_SIZE), 2)
            txt = self.font.render(f"{turns_left}х", True, ORANGE)
            self.screen.blit(txt, (px + 4, py + 4))

    def draw_gather_lines(self):
        for unit in self.game.units:
            if isinstance(unit, Worker) and unit.player == 'blue' and unit.gather_target:
                ux = unit.x * GRID_SIZE + GRID_SIZE // 2
                uy = unit.y * GRID_SIZE + GRID_SIZE // 2
                tx = unit.gather_target.x * GRID_SIZE + GRID_SIZE // 2
                ty = unit.gather_target.y * GRID_SIZE + GRID_SIZE // 2
                pygame.draw.line(self.screen, GOLD, (ux, uy), (tx, ty), 1)

    def draw_info_panel(self):
        panel_rect = pygame.Rect(GAME_WIDTH, 0, INFO_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, LIGHT_GRAY, panel_rect)
        pygame.draw.line(self.screen, BLACK, (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2)

        y = 10
        title = self.big_font.render("Информация", True, BLACK)
        self.screen.blit(title, (GAME_WIDTH + 20, y)); y += 30

        turn_text = self.font.render(f"Ход: {self.game.turn_number}", True, BLACK)
        self.screen.blit(turn_text, (GAME_WIDTH + 20, y)); y += 20

        player_text = self.font.render(
            f"Сейчас: {'Игрок' if self.game.turn == 'player' else 'ВРАГ'}",
            True, BLUE if self.game.turn == 'player' else RED
        )
        self.screen.blit(player_text, (GAME_WIDTH + 20, y)); y += 25

        self.screen.blit(self.font.render("--- Ресурсы ---", True, BLACK), (GAME_WIDTH + 20, y)); y += 18
        self.screen.blit(self.font.render(
            f"Минералы: {self.game.player_resources['blue']['minerals']}", True, GOLD),
            (GAME_WIDTH + 20, y)); y += 18
        self.screen.blit(self.font.render(
            f"Газ: {self.game.player_resources['blue']['gas']}", True, CYAN),
            (GAME_WIDTH + 20, y)); y += 22

        self.screen.blit(self.font.render("--- Строить ---", True, BLACK), (GAME_WIDTH + 20, y)); y += 18
        for btn in self.game.build_buttons:
            color = GREEN if self.game.build_type == btn['type'] else GRAY
            pygame.draw.rect(self.screen, color, btn['rect'])
            pygame.draw.rect(self.screen, BLACK, btn['rect'], 1)
            line1 = self.font.render(btn['name'], True, BLACK)
            line2 = self.font.render(
                f"{btn['cost']['minerals']}м {btn['cost']['gas']}г", True, DARK_GRAY)
            self.screen.blit(line1, (btn['rect'].x + 5, btn['rect'].y + 4))
            self.screen.blit(line2, (btn['rect'].x + 5, btn['rect'].y + 20))

        prod_y = self.game.build_buttons[-1]['rect'].bottom + 10
        sel_bld = self.game.selected_building
        if sel_bld and isinstance(sel_bld, Barracks):
            self.screen.blit(self.font.render("--- Нанять ---", True, BLACK), (GAME_WIDTH + 20, prod_y))
            prod_y += 18
            for btn in self.game.recruit_buttons:
                color = LIGHT_BLUE if self.game.turn == 'player' else GRAY
                pygame.draw.rect(self.screen, color, btn['rect'])
                pygame.draw.rect(self.screen, BLACK, btn['rect'], 1)
                self.screen.blit(self.font.render(btn['name'], True, BLACK), (btn['rect'].x + 5, btn['rect'].y + 4))
                self.screen.blit(self.font.render(
                    f"{btn['cost']['minerals']}м {btn['cost']['gas']}г", True, DARK_GRAY),
                    (btn['rect'].x + 5, btn['rect'].y + 20))
        elif sel_bld and isinstance(sel_bld, Base) and sel_bld.player == 'blue':
            self.screen.blit(self.font.render("--- Нанять (база) ---", True, BLACK), (GAME_WIDTH + 20, prod_y))
            prod_y += 18
            btn = self.game.worker_button
            color = LIGHT_BLUE if self.game.turn == 'player' else GRAY
            pygame.draw.rect(self.screen, color, btn['rect'])
            pygame.draw.rect(self.screen, BLACK, btn['rect'], 1)
            self.screen.blit(self.font.render(btn['name'], True, BLACK), (btn['rect'].x + 5, btn['rect'].y + 4))
            self.screen.blit(self.font.render(
                f"{btn['cost']['minerals']}м {btn['cost']['gas']}г", True, DARK_GRAY),
                (btn['rect'].x + 5, btn['rect'].y + 20))

        sel_y = SCREEN_HEIGHT - 260
        if self.game.selected_building:
            bld = self.game.selected_building
            self.screen.blit(self.font.render(f"Здание: {bld.name}", True, BLACK), (GAME_WIDTH + 20, sel_y))
            sel_y += 18
            self.screen.blit(self.font.render(f"HP: {bld.hp}/{bld.max_hp}", True, BLACK), (GAME_WIDTH + 20, sel_y))
            sel_y += 18
            if bld.production_queue:
                self.screen.blit(
                    self.font.render(f"В очереди: {len(bld.production_queue)}", True, ORANGE),
                    (GAME_WIDTH + 20, sel_y))
        elif self.game.selected_units:
            self.screen.blit(self.font.render("Выбрано:", True, BLACK), (GAME_WIDTH + 20, sel_y))
            sel_y += 18
            for unit in self.game.selected_units[:4]:
                color = DARK_BLUE if unit.player == 'blue' else DARK_RED
                self.screen.blit(
                    self.font.render(f"{unit.name}: {unit.hp}/{unit.max_hp} HP", True, color),
                    (GAME_WIDTH + 20, sel_y))
                sel_y += 16

        tips_y = SCREEN_HEIGHT - 130
        self.screen.blit(self.font.render("--- Управление ---", True, BLACK), (GAME_WIDTH + 20, tips_y)); tips_y += 18
        tips = [
            "ЛКМ - выбрать / действие",
            "ПКМ - отмена выделения",
            "M - показать движение",
            "A - показать атаку юнита",
            "T - зоны атаки башен",
            "Space / кнопка - ход",
        ]
        for tip in tips:
            self.screen.blit(self.font.render(tip, True, DARK_GRAY), (GAME_WIDTH + 20, tips_y))
            tips_y += 16

        btn_color = GREEN if self.game.turn == 'player' else GRAY
        pygame.draw.rect(self.screen, btn_color, self.game.end_turn_button)
        pygame.draw.rect(self.screen, BLACK, self.game.end_turn_button, 2)
        btn_text = self.font.render("Завершить ход", True, BLACK)
        text_rect = btn_text.get_rect(center=self.game.end_turn_button.center)
        self.screen.blit(btn_text, text_rect)

    def draw_messages(self):
        for i, (msg, _) in enumerate(self.game.messages[-4:]):
            surf = self.font.render(msg, True, BLACK)
            self.screen.blit(surf, (10, SCREEN_HEIGHT - 80 + i * 18))

    def draw_game_over(self):
        if not self.game.game_over:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        if self.game.winner == 'blue':
            msg = "Вы уничтожили базу врага"
            color = BLUE
        else:
            msg = "Ваша база уничтожена"
            color = RED
        text = self.big_font.render(msg, True, color)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(text, rect)
        sub = self.font.render("Нажмите ESC для выхода", True, WHITE)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(sub, sub_rect)


class RTSGame:
    def __init__(self, headless=False):
        self.headless = headless
        self.clock = pygame.time.Clock() if not headless else None
        self.running = True
        self.units = []
        self.buildings = []
        self.resources = []
        self.selected_units = []
        self.selected_building = None

        self.player_resources = {
            'blue': {'minerals': 200, 'gas': 50},
            'red':  {'minerals': 200, 'gas': 50}
        }

        self.turn = 'player'
        self.turn_number = 1
        self.game_over = False
        self.winner = None

        self.show_move_range = False
        self.show_attack_range = False
        self.show_tower_range = False
        self.build_type = None

        self.pending_builds = {}

        self.messages = []

        self._setup_world()
        self.build_buttons = []
        self.recruit_buttons = []
        if not headless:
            self.end_turn_button = pygame.Rect(
                GAME_WIDTH + 20, SCREEN_HEIGHT - 50,
                INFO_PANEL_WIDTH - 40, 40
            )
            self._create_build_buttons()
            self._create_recruit_buttons()
        else:
            self.end_turn_button = None
            self._create_build_buttons_headless()
            self._create_recruit_buttons_headless()

    def _create_build_buttons_headless(self):
        self.build_buttons = [
            {'type': 'barracks', 'name': 'Казармы', 'cost': {'minerals': 150, 'gas': 0}},
            {'type': 'tower', 'name': 'Башня', 'cost': {'minerals': 100, 'gas': 50}},
        ]

    def _create_recruit_buttons_headless(self):
        self.recruit_buttons = [
            {'type': Light, 'name': 'Легкий', 'cost': {'minerals': 50, 'gas': 0}},
            {'type': Heavy, 'name': 'Тяжелый', 'cost': {'minerals': 100, 'gas': 25}},
            {'type': Ranged, 'name': 'Дальний', 'cost': {'minerals': 75, 'gas': 50}},
        ]
        self.worker_button = {
            'type': Worker, 'name': 'Рабочий', 'cost': {'minerals': 25, 'gas': 0}
        }

    def _setup_world(self):
        self.buildings.append(Base(2, 2, 'blue'))
        self.buildings.append(Base(GRID_WIDTH - 4, GRID_HEIGHT - 4, 'red'))

        self.units.append(Worker(random.randint(4, 6), random.randint(3, 5), 'blue'))
        self.units.append(Worker(random.randint(5, 8), random.randint(7, 9), 'blue'))
        self.units.append(Light(random.randint(7, 10), random.randint(3, 5),  'blue'))

        self.units.append(Worker(GRID_WIDTH - 6, GRID_HEIGHT - 5, 'red'))
        self.units.append(Worker(GRID_WIDTH - 6, GRID_HEIGHT - 7, 'red'))
        self.units.append(Light(GRID_WIDTH - 4, GRID_HEIGHT - 8,  'red'))

        occupied = set()

        self.units.append(Light(random.randint(4, 9), random.randint(3, 10), 'blue'))
        self.units.append(Light(random.randint(7, 12), random.randint(5, 11), 'blue'))
        for b in self.buildings:
            for dx in range(b.size):
                for dy in range(b.size):
                    occupied.add((b.x + dx, b.y + dy))
        for u in self.units:
            occupied.add((int(u.x), int(u.y)))
        self.units.append(Light(random.randint(4, 9), random.randint(3, 10), 'blue'))

        def too_close_to_base(x, y, min_dist=4):
            for b in self.buildings:
                if isinstance(b, Base):
                    if abs(x - b.x) < min_dist and abs(y - b.y) < min_dist:
                        return True
            return False

        def place_resources(cls, count, amount_range):
            placed = 0
            attempts = 0
            while placed < count and attempts < 500:
                attempts += 1
                x = random.randint(2, GRID_WIDTH - 3)
                y = random.randint(2, GRID_HEIGHT - 3)
                if (x, y) in occupied:
                    continue
                if too_close_to_base(x, y):
                    continue
                too_close = any(abs(x - rx) < 2 and abs(y - ry) < 2
                                for rx, ry in occupied)
                if too_close:
                    continue
                amount = random.randint(*amount_range)
                self.resources.append(cls(x, y, amount))
                occupied.add((x, y))
                placed += 1

        place_resources(Minerals, random.randint(7, 9), (80, 400))
        place_resources(Gas, random.randint(4, 6), (60, 250))

    def _create_build_buttons(self):
        defs = [
            ("barracks", "Казармы",  {'minerals': 150, 'gas': 0}),
            ("tower",    "Башня",    {'minerals': 100, 'gas': 50}),
        ]
        start_y = 175
        for i, (btype, name, cost) in enumerate(defs):
            rect = pygame.Rect(GAME_WIDTH + 10, start_y + i * 45, INFO_PANEL_WIDTH - 20, 40)
            self.build_buttons.append({'rect': rect, 'type': btype, 'name': name, 'cost': cost})

    def _create_recruit_buttons(self):
        barracks_defs = [
            (Light,  "Легкий",  {'minerals': 50,  'gas': 0}),
            (Heavy,  "Тяжелый", {'minerals': 100, 'gas': 25}),
            (Ranged, "Дальний", {'minerals': 75,  'gas': 50}),
        ]
        start_y = self.build_buttons[-1]['rect'].bottom + 28
        for i, (utype, name, cost) in enumerate(barracks_defs):
            rect = pygame.Rect(GAME_WIDTH + 10, start_y + i * 45, INFO_PANEL_WIDTH - 20, 40)
            self.recruit_buttons.append({'rect': rect, 'type': utype, 'name': name, 'cost': cost})

        worker_y = start_y
        self.worker_button = {
            'rect': pygame.Rect(GAME_WIDTH + 10, start_y, INFO_PANEL_WIDTH - 20, 40),
            'type': Worker,
            'name': "Рабочий",
            'cost': {'minerals': 25, 'gas': 0}
        }

    def log(self, msg):
        self.messages.append((msg, 120))

    def _tick_messages(self):
        self.messages = [(m, t - 1) for m, t in self.messages if t > 1]

    def is_cell_occupied(self, x, y, exclude_unit=None):
        for unit in self.units:
            if unit is exclude_unit:
                continue
            if int(unit.x) == x and int(unit.y) == y:
                return True
        for building in self.buildings:
            if building.x <= x < building.x + building.size and \
               building.y <= y < building.y + building.size:
                return True
        return False

    def get_unit_at(self, x, y):
        for unit in self.units:
            if int(unit.x) == x and int(unit.y) == y:
                return unit
        return None

    def get_building_at(self, x, y):
        for building in self.buildings:
            if building.x <= x < building.x + building.size and \
               building.y <= y < building.y + building.size:
                return building
        return None

    def get_resource_at(self, x, y):
        for resource in self.resources:
            if resource.x == x and resource.y == y:
                return resource
        return None

    def _find_spawn_cell(self, building):
        cx, cy = building.x, building.y
        for r in range(1, 5):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if abs(dx) + abs(dy) == r:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                            if not self.is_cell_occupied(nx, ny):
                                return nx, ny
        return None

    def _worker_adjacent(self, x, y):
        for unit in self.units:
            if isinstance(unit, Worker) and unit.player == 'blue' and not unit.has_acted:
                if abs(unit.x - x) <= 1 and abs(unit.y - y) <= 1:
                    return unit
        return None

    def try_build_building(self, x, y):
        if not self.build_type:
            return
        cost = next((b['cost'] for b in self.build_buttons if b['type'] == self.build_type), None)
        if cost is None:
            return

        key = (x, y, self.build_type)

        worker = self._worker_adjacent(x, y)
        if not worker:
            self.log("Нужен рабочий рядом с местом постройки")
            self.build_type = None
            return

        res = self.player_resources['blue']
        if res['minerals'] < cost['minerals'] or res['gas'] < cost['gas']:
            self.log("Недостаточно ресурсов")
            self.build_type = None
            return

        type_map = {'barracks': Barracks, 'tower': Tower}
        cls = type_map[self.build_type]
        candidate = cls(x, y, 'blue')

        if not candidate.can_build_here(x, y, self):
            self.log("Нельзя построить здесь")
            self.build_type = None
            return

        if key not in self.pending_builds:
            res['minerals'] -= cost['minerals']
            res['gas']      -= cost['gas']
            self.pending_builds[key] = 2
            worker.has_acted = True
            self.log(f"Строительство {candidate.name} начато (осталось 2 хода)")
        else:
            self.log(f"Строительство уже идёт ({self.pending_builds[key]} хода)")

        self.build_type = None

    def _advance_pending_builds(self):
        finished = []
        for key, turns_left in list(self.pending_builds.items()):
            bx, by, btype = key
            worker = self._worker_adjacent(bx, by)
            if not worker:
                self.log("Рабочий ушёл — стройка приостановлена")
                continue
            new_turns = turns_left - 1
            worker.has_acted = True
            if new_turns <= 0:
                type_map = {'barracks': Barracks, 'tower': Tower}
                cls = type_map[btype]
                new_building = cls(bx, by, 'blue')
                self.buildings.append(new_building)
                self.log(f"{new_building.name} построено")
                finished.append(key)
            else:
                self.pending_builds[key] = new_turns
                self.log(f"Строительство: осталось {new_turns} хода")
        for key in finished:
            del self.pending_builds[key]

    def try_recruit_unit(self, unit_type, cost, building):
        res = self.player_resources['blue']
        if res['minerals'] < cost['minerals'] or res['gas'] < cost['gas']:
            self.log("Недостаточно ресурсов")
            return
        res['minerals'] -= cost['minerals']
        res['gas']      -= cost['gas']
        if isinstance(building, Barracks):
            building.start_production(unit_type, cost)
            self.log(f"Начато производство: {unit_type.__name__}")
        elif isinstance(building, Base):
            cell = self._find_spawn_cell(building)
            if cell:
                self.units.append(unit_type(*cell, 'blue'))
                self.log("Рабочий нанят")
            else:
                self.log("Нет места для рабочего")
                res['minerals'] += cost['minerals']
                res['gas']      += cost['gas']

    def _deselect_all(self):
        for u in self.units:
            u.selected = False
        if self.selected_building:
            self.selected_building.selected = False
        self.selected_units.clear()
        self.selected_building = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_over:
                        self.running = False
                    else:
                        self._deselect_all()
                        self.build_type = None
                elif event.key == pygame.K_SPACE:
                    if self.turn == 'player' and not self.game_over:
                        self.end_player_turn()
                elif event.key == pygame.K_m:
                    self.show_move_range = not self.show_move_range
                elif event.key == pygame.K_a:
                    self.show_attack_range = not self.show_attack_range
                elif event.key == pygame.K_t:
                    self.show_tower_range = not self.show_tower_range

            elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                if event.button == 1:
                    self._on_left_click(event.pos)
                elif event.button == 3:
                    self._deselect_all()
                    self.build_type = None

    def _on_left_click(self, pos):
        if self.end_turn_button.collidepoint(pos):
            if self.turn == 'player':
                self.end_player_turn()
            return

        for btn in self.build_buttons:
            if btn['rect'].collidepoint(pos) and self.turn == 'player':
                self.build_type = btn['type']
                self._deselect_all()
                self.log(f"Выбрано строительство: {btn['name']}")
                return

        if self.selected_building and isinstance(self.selected_building, Barracks):
            for btn in self.recruit_buttons:
                if btn['rect'].collidepoint(pos) and self.turn == 'player':
                    self.try_recruit_unit(btn['type'], btn['cost'], self.selected_building)
                    return
        if self.selected_building and isinstance(self.selected_building, Base) and self.selected_building.player == 'blue':
            btn = self.worker_button
            if btn['rect'].collidepoint(pos) and self.turn == 'player':
                self.try_recruit_unit(btn['type'], btn['cost'], self.selected_building)
                return

        if pos[0] < GAME_WIDTH:
            gx = pos[0] // GRID_SIZE
            gy = pos[1] // GRID_SIZE
            self._handle_grid_click(gx, gy)

    def _handle_grid_click(self, gx, gy):
        if self.turn != 'player':
            return

        if self.build_type:
            self.try_build_building(gx, gy)
            return

        building = self.get_building_at(gx, gy)
        unit_here = self.get_unit_at(gx, gy)
        resource = self.get_resource_at(gx, gy)

        if self.selected_units:
            if unit_here and unit_here.player == 'red':
                for unit in self.selected_units:
                    if not unit.has_acted:
                        if unit.can_attack(unit_here):
                            unit.action_type = 'attack'
                            unit.action_target = unit_here
                            self.log(f"{unit.name} атакует {unit_here.name}")
                        else:
                            self.log(f"{unit.name} слишком далеко для атаки")
                return

            if building and building.player == 'red':
                for unit in self.selected_units:
                    if not unit.has_acted:
                        dist = math.sqrt((unit.x - building.x)**2 + (unit.y - building.y)**2)
                        if dist <= unit.attack_range + 1:
                            unit.action_type = 'attack_building'
                            unit.action_target = building
                            self.log(f"{unit.name} атакует здание {building.name}")
                        else:
                            self.log(f"{unit.name} слишком далеко для атаки здания")
                return

            if resource:
                workers = [u for u in self.selected_units if isinstance(u, Worker)]
                for w in workers:
                    if not w.has_acted:
                        w.gather_target = resource
                        self.log("Рабочий идёт за ресурсами")
                return

            if not unit_here and not building:
                for unit in self.selected_units:
                    if not unit.has_acted:
                        if (gx, gy) in unit.get_possible_moves():
                            if not self.is_cell_occupied(gx, gy):
                                unit.action_type = 'move'
                                unit.action_target = (gx, gy)
                        else:
                            self.log(f"{unit.name} не может туда")
                return

        if unit_here and unit_here.player == 'blue' and not unit_here.has_acted:
            self._deselect_all()
            self.selected_units.append(unit_here)
            unit_here.selected = True
            return

        if building and building.player == 'blue':
            self._deselect_all()
            self.selected_building = building
            building.selected = True
            return

        self._deselect_all()

    def execute_player_turn(self):
        for unit in list(self.units):
            if unit.player == 'blue' and unit.action_type == 'move' and unit.action_target:
                nx, ny = unit.action_target
                if not self.is_cell_occupied(nx, ny, exclude_unit=unit):
                    unit.x, unit.y = nx, ny
                unit.has_acted = True

        for unit in list(self.units):
            if unit.player == 'blue' and isinstance(unit, Worker) and not unit.has_acted:
                target = unit.gather_target
                if target and not target.is_depleted():
                    dist = unit.distance_to(target)
                    if dist <= 1.5:
                        gathered = target.gather(unit.gather_rate)
                        if isinstance(target, Gas):
                            self.player_resources['blue']['gas'] += gathered
                            self.log(f"Рабочий добыл {gathered} газа")
                        else:
                            self.player_resources['blue']['minerals'] += gathered
                            self.log(f"Рабочий добыл {gathered} минералов")
                        unit.has_acted = True
                    else:
                        self._move_unit_toward(unit, target.x, target.y)
                        unit.has_acted = True

        for unit in list(self.units):
            if unit.player == 'blue' and unit.action_type == 'attack' and unit.action_target:
                target = unit.action_target
                if target in self.units and unit.can_attack(target):
                    target.take_damage(unit.attack)
                    self.log(f"{unit.name} атакует: -{unit.attack} HP")
                unit.has_acted = True

        for unit in list(self.units):
            if unit.player == 'blue' and unit.action_type == 'attack_building' and unit.action_target:
                bld = unit.action_target
                if bld in self.buildings:
                    bld.hp -= unit.attack
                    self.log(f"{unit.name} атакует {bld.name}: -{unit.attack} HP")
                    if bld.hp <= 0:
                        self.buildings.remove(bld)
                        self.log(f"{bld.name} уничтожено")
                unit.has_acted = True

        for bld in self.buildings:
            if isinstance(bld, Tower) and bld.player == 'blue':
                enemies = [u for u in self.units if u.player == 'red']
                for enemy in enemies:
                    dist = math.sqrt((bld.x - enemy.x)**2 + (bld.y - enemy.y)**2)
                    if dist <= bld.attack_range:
                        enemy.take_damage(bld.attack)
                        self.log(f"Башня атакует {enemy.name}")
                        break

        for bld in self.buildings:
            if isinstance(bld, Barracks) and bld.player == 'blue':
                result = bld.update_production()
                if result:
                    cell = self._find_spawn_cell(bld)
                    if cell:
                        new_unit = result['type'](*cell, 'blue')
                        self.units.append(new_unit)
                        self.log(f"Создан юнит: {result['type'].__name__}")

        self._advance_pending_builds()

        self.units = [u for u in self.units if u.hp > 0]
        self.resources = [r for r in self.resources if not r.is_depleted()]

    def execute_enemy_turn(self):
        res = self.player_resources['red']
        red_workers  = [u for u in self.units if u.player == 'red' and isinstance(u, Worker)]
        red_fighters = [u for u in self.units if u.player == 'red' and not isinstance(u, Worker)]
        blue_units   = [u for u in self.units if u.player == 'blue']
        blue_buildings = [b for b in self.buildings if b.player == 'blue']
        red_bases    = [b for b in self.buildings if isinstance(b, Base)     and b.player == 'red']
        red_barracks = [b for b in self.buildings if isinstance(b, Barracks) and b.player == 'red']
        red_towers   = [b for b in self.buildings if isinstance(b, Tower)    and b.player == 'red']

        for worker in red_workers:
            if worker.carrying >= 40 and red_bases:
                base = min(red_bases, key=lambda b: worker.distance_to(b))
                dist = math.sqrt((worker.x - base.x)**2 + (worker.y - base.y)**2)
                if dist <= 2.5:
                    res['minerals'] += worker.carrying
                    worker.carrying = 0
                else:
                    self._move_unit_toward(worker, base.x + 1, base.y + 1)
            elif self.resources:
                closest_res = min(self.resources, key=lambda r: worker.distance_to(r))
                dist = worker.distance_to(closest_res)
                if dist <= 1.5:
                    gathered = closest_res.gather(worker.gather_rate)
                    worker.carrying += gathered
                else:
                    self._move_unit_toward(worker, closest_res.x, closest_res.y)

        if res['minerals'] >= 1150 and not red_barracks and red_bases:
            base = red_bases[0]
            for dx_off, dy_off in [(-3, 0), (0, -3), (-3, -3), (-4, 0), (0, -4)]:
                bx, by = base.x + dx_off, base.y + dy_off
                if 0 <= bx < GRID_WIDTH and 0 <= by < GRID_HEIGHT:
                    cand = Barracks(bx, by, 'red')
                    if cand.can_build_here(bx, by, self):
                        self.buildings.append(cand)
                        res['minerals'] -= 150
                        red_barracks.append(cand)
                        break

        fighter_count = len(red_fighters)
        heavy_count   = sum(1 for u in red_fighters if isinstance(u, Heavy))
        ranged_count  = sum(1 for u in red_fighters if isinstance(u, Ranged))

        for bld in red_barracks:
            result = bld.update_production()
            if result:
                cell = self._find_spawn_cell(bld)
                if cell:
                    self.units.append(result['type'](*cell, 'red'))

            if bld.production_queue:
                continue

            if res['minerals'] >= 100 and res['gas'] >= 25 and \
               (fighter_count == 0 or heavy_count / max(fighter_count, 1) < 0.40):
                res['minerals'] -= 100
                res['gas']      -= 25
                bld.start_production(Heavy, {'minerals': 100, 'gas': 25})
            elif res['minerals'] >= 75 and res['gas'] >= 50 and \
                 (fighter_count == 0 or ranged_count / max(fighter_count, 1) < 0.30):
                res['minerals'] -= 75
                res['gas']      -= 50
                bld.start_production(Ranged, {'minerals': 75, 'gas': 50})
            elif res['minerals'] >= 50:
                res['minerals'] -= 50
                bld.start_production(Light, {'minerals': 50, 'gas': 0})

        if len(red_workers) < 3 and res['minerals'] >= 25 and red_bases:
            cell = self._find_spawn_cell(red_bases[0])
            if cell:
                self.units.append(Worker(*cell, 'red'))
                res['minerals'] -= 25

        for bld in self.buildings:
            if isinstance(bld, Tower) and bld.player == 'red':
                for bu in blue_units:
                    dist = math.sqrt((bld.x - bu.x)**2 + (bld.y - bu.y)**2)
                    if dist <= bld.attack_range:
                        bu.take_damage(bld.attack)
                        break

        if len(red_fighters) >= 4:
            priority = None
            blue_towers = [b for b in blue_buildings if isinstance(b, Tower)]
            if blue_towers:
                priority = min(blue_towers,
                               key=lambda b: math.sqrt((red_bases[0].x - b.x)**2 +
                                                        (red_bases[0].y - b.y)**2) if red_bases else 0)
            elif blue_buildings:
                priority = min(blue_buildings,
                               key=lambda b: math.sqrt(
                                   (b.x - GRID_WIDTH//2)**2 + (b.y - GRID_HEIGHT//2)**2))

        for unit in red_fighters:
            if unit.hp / unit.max_hp < 0.25 and red_bases:
                self._move_unit_toward(unit, red_bases[0].x + 1, red_bases[0].y + 1)
                continue

            if isinstance(unit, Ranged) and blue_units:
                closest_enemy = min(blue_units,
                                    key=lambda u: math.sqrt((unit.x - u.x)**2 + (unit.y - u.y)**2))
                dist = math.sqrt((unit.x - closest_enemy.x)**2 + (unit.y - closest_enemy.y)**2)
                if dist < 3:
                    self._move_unit_toward(unit, unit.x * 2 - closest_enemy.x,
                                           unit.y * 2 - closest_enemy.y)
                elif unit.can_attack(closest_enemy):
                    closest_enemy.take_damage(unit.attack)
                    if closest_enemy.hp <= 0 and closest_enemy in blue_units:
                        blue_units.remove(closest_enemy)
                else:
                    self._move_unit_toward(unit, closest_enemy.x, closest_enemy.y)
                continue

            targets = blue_units if blue_units else blue_buildings
            if not targets:
                break
            closest = min(targets, key=lambda t: math.sqrt((unit.x - t.x)**2 + (unit.y - t.y)**2))
            dist = math.sqrt((unit.x - closest.x)**2 + (unit.y - closest.y)**2)

            if isinstance(closest, Building):
                if dist <= unit.attack_range + 1:
                    closest.hp -= unit.attack
                    if closest.hp <= 0 and closest in self.buildings:
                        self.buildings.remove(closest)
                        if closest in blue_buildings:
                            blue_buildings.remove(closest)
                else:
                    self._move_unit_toward(unit, closest.x, closest.y)
            else:
                if unit.can_attack(closest):
                    closest.take_damage(unit.attack)
                    if closest.hp <= 0 and closest in blue_units:
                        blue_units.remove(closest)
                else:
                    self._move_unit_toward(unit, closest.x, closest.y)

        self.units     = [u for u in self.units     if u.hp > 0]
        self.resources = [r for r in self.resources if not r.is_depleted()]

    def _move_unit_toward(self, unit, tx, ty):
        dx = tx - unit.x
        dy = ty - unit.y
        dist = max(abs(dx), abs(dy), 1)
        step = unit.speed
        nx = unit.x + max(-step, min(step, int(round(dx / dist * step))))
        ny = unit.y + max(-step, min(step, int(round(dy / dist * step))))
        nx = max(0, min(GRID_WIDTH - 1, nx))
        ny = max(0, min(GRID_HEIGHT - 1, ny))
        if not self.is_cell_occupied(nx, ny, exclude_unit=unit):
            unit.x, unit.y = nx, ny
        elif not self.is_cell_occupied(nx, unit.y, exclude_unit=unit):
            unit.x = nx
        elif not self.is_cell_occupied(unit.x, ny, exclude_unit=unit):
            unit.y = ny

    def end_player_turn(self):
        if self.turn != 'player' or self.game_over:
            return
        self.execute_player_turn()
        if self.check_game_over():
            return
        self.turn = 'enemy'
        self.execute_enemy_turn()
        if self.check_game_over():
            return
        self.turn = 'player'
        self.turn_number += 1
        for unit in self.units:
            unit.reset_turn()
        self._deselect_all()
        self._tick_messages()

    def _auto_deposit(self):
        pass

    def check_game_over(self):
        blue_bases = [b for b in self.buildings if b.player == 'blue' and isinstance(b, Base)]
        blue_units = [b for b in self.units if b.player == 'blue']
        red_bases  = [b for b in self.buildings if b.player == 'red'  and isinstance(b, Base)]
        red_units = [b for b in self.units if b.player == 'red']
        if not blue_bases or len(blue_units) == 0:
            self.game_over = True
            self.winner = 'red'
            return True
        if not red_bases or len(red_units) == 0:
            self.game_over = True
            self.winner = 'blue'
            return True
        return False