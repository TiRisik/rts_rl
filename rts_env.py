import math
import sys
import os
import random
from typing import Optional
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from consts import GRID_WIDTH, GRID_HEIGHT
from units import Heavy, Light, Ranged, Worker
from buildings import Base, Barracks, Tower
from recources import Minerals, Gas
import pygame

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

pygame.init()

GH = GRID_HEIGHT
GW = GRID_WIDTH
N_FEATURES = 22
N_ACTIONS = 14
MAX_TURNS = 100

def _make_game():
    from main import RTSGame
    return RTSGame(headless=True)

class RTSEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(
            low=0.0, high=1.0,
            shape=(GH * GW * N_FEATURES,),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(N_ACTIONS)
        self.game: Optional[object] = None

        self._prev_blue_units     = 0
        self._prev_blue_fighters  = 0
        self._prev_red_units      = 0
        self._prev_blue_buildings = 0
        self._prev_red_buildings  = 0
        self._prev_blue_minerals  = 0
        self._prev_blue_gas       = 0
        self._prev_avg_dist_to_base = 30.0
        self._prev_red_base_hp    = 500
        self._prev_red_total_hp   = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        self.game = _make_game()
        self._sync_prev_state()
        obs = self._get_obs()
        return obs, {}

    def step(self, action: int):
        assert self.game is not None, "call reset() first"
        g = self.game
        self._last_action = int(action)
        self._apply_action(action)
        g.end_player_turn()
        terminated = g.game_over
        truncated  = g.turn_number > MAX_TURNS
        if truncated and not terminated:
            g.game_over = True
            g.winner    = None
        reward = self._compute_reward()
        self._sync_prev_state()
        obs = self._get_obs()
        info = {
            "turn":          g.turn_number,
            "winner":        g.winner,
            "blue_units":    len([u for u in g.units    if u.player == 'blue']),
            "red_units":     len([u for u in g.units    if u.player == 'red']),
            "blue_minerals": g.player_resources['blue']['minerals'],
            "blue_gas":      g.player_resources['blue']['gas'],
        }
        return obs, reward, terminated, truncated, info

    def render(self):
        pass

    def close(self):
        pass

    def _get_obs(self) -> np.ndarray:
        g = self.game
        N_FEAT = 22
        grid = np.zeros((GH, GW, N_FEAT), dtype=np.float32)
        grid[:, :, 17] = np.clip(g.player_resources['blue']['minerals'] / 500.0, 0, 1)
        grid[:, :, 18] = np.clip(g.player_resources['blue']['gas'] / 200.0, 0, 1)
        grid[:, :, 21] = np.clip(g.player_resources['red']['minerals'] / 500.0, 0, 1)
        blue_barracks_busy = any(
            isinstance(b, Barracks) and b.player == 'blue' and b.production_queue
            for b in g.buildings
        )
        if blue_barracks_busy:
            grid[:, :, 20] = 1.0

        for (bx, by, btype), turns_left in g.pending_builds.items():
            if 0 <= bx < GW and 0 <= by < GH:
                grid[by, bx, 19] = turns_left / 3.0
        for u in g.units:
            x, y = int(u.x), int(u.y)
            if not (0 <= x < GW and 0 <= y < GH):
                continue
            grid[y, x, 0] = u.hp / u.max_hp
            grid[y, x, 2 if u.player == 'blue' else 3] = 1.0
            if isinstance(u, Worker):
                grid[y, x, 12] = 1.0
            elif isinstance(u, Light):
                grid[y, x, 13] = 1.0
            elif isinstance(u, Heavy):
                grid[y, x, 14] = 1.0
            elif isinstance(u, Ranged):
                grid[y, x, 15] = 1.0
            if u.has_acted:
                grid[y, x, 16] = 1.0

        for b in g.buildings:
            hp = b.hp / b.max_hp
            for dx in range(b.size):
                for dy in range(b.size):
                    x, y = b.x + dx, b.y + dy
                    if not (0 <= x < GW and 0 <= y < GH):
                        continue
                    grid[y, x, 1] = hp
                    if isinstance(b, Base) and b.player == 'blue':
                        grid[y, x, 4] = 1.0
                    elif isinstance(b, Base) and b.player == 'red':
                        grid[y, x, 5] = 1.0
                    elif isinstance(b, Barracks) and b.player == 'blue':
                        grid[y, x, 6] = 1.0
                    elif isinstance(b, Barracks) and b.player == 'red':
                        grid[y, x, 7] = 1.0
                    elif isinstance(b, Tower) and b.player == 'blue':
                        grid[y, x, 8] = 1.0
                    elif isinstance(b, Tower) and b.player == 'red':
                        grid[y, x, 9] = 1.0

        for r in g.resources:
            x, y = r.x, r.y
            if not (0 <= x < GW and 0 <= y < GH):
                continue
            if isinstance(r, Minerals):
                grid[y, x, 10] = r.amount / 400.0
            else:
                grid[y, x, 11] = r.amount / 400.0

        return grid.flatten()

    def _apply_action(self, action: int):
        g = self.game
        blue_units    = [u for u in g.units if u.player == 'blue']
        blue_workers  = [u for u in blue_units if isinstance(u, Worker) and not u.has_acted]
        blue_fighters = [u for u in blue_units if not isinstance(u, Worker) and not u.has_acted]
        red_units     = [u for u in g.units if u.player == 'red']
        blue_blds     = [b for b in g.buildings if b.player == 'blue']
        red_blds      = [b for b in g.buildings if b.player == 'red']
        blue_bases    = [b for b in blue_blds if isinstance(b, Base)]
        red_bases     = [b for b in red_blds  if isinstance(b, Base)]
        red_barracks  = [b for b in red_blds  if isinstance(b, Barracks)]
        blue_barracks = [b for b in blue_blds if isinstance(b, Barracks)]

        if action == 0:
            cost = {'minerals': 100, 'gas': 50}
            res  = g.player_resources['blue']
            if res['minerals'] >= cost['minerals'] and res['gas'] >= cost['gas']:
                worker = next((w for w in blue_workers), None)
                if worker:
                    placed = self._place_building(g, worker, 'tower', cost, res)

        elif action == 1:
            cost = {'minerals': 150, 'gas': 0}
            res  = g.player_resources['blue']
            if res['minerals'] >= cost['minerals'] and blue_bases:
                worker = next((w for w in blue_workers), None)
                if worker:
                    placed = self._place_building(g, worker, 'barracks', cost, res)

        elif action == 2:
            if blue_bases:
                cost = {'minerals': 25, 'gas': 0}
                res  = g.player_resources['blue']
                if res['minerals'] >= cost['minerals']:
                    cell = g._find_spawn_cell(blue_bases[0])
                    if cell:
                        res['minerals'] -= cost['minerals']
                        g.units.append(Worker(*cell, 'blue'))

        elif action == 3:
            self._recruit_in_barracks(g, Ranged, {'minerals': 75, 'gas': 50}, blue_barracks)

        elif action == 4:
            self._recruit_in_barracks(g, Light, {'minerals': 50, 'gas': 0}, blue_barracks)

        elif action == 5:
            self._recruit_in_barracks(g, Heavy, {'minerals': 100, 'gas': 25}, blue_barracks)

        elif action == 6:
            if red_bases:
                target = red_bases[0]
                for u in blue_fighters:
                    self._queue_move_toward(u, target.x, target.y)

        elif action == 7:
            if red_barracks:
                for u in blue_fighters:
                    nearest_bar = min(red_barracks, key=lambda b: _dist_xy(u.x, u.y, b.x, b.y))
                    self._queue_move_toward(u, nearest_bar.x, nearest_bar.y)
            elif red_bases:
                target = red_bases[0]
                for u in blue_fighters:
                    self._queue_move_toward(u, target.x, target.y)

        elif action == 8:
            for u in blue_fighters:
                if red_units:
                    nearest = min(red_units, key=lambda e: _dist(u, e))
                    self._queue_move_toward(u, nearest.x, nearest.y)

        elif action == 9:
            for u in blue_fighters + blue_workers:
                if not u.has_acted and red_units:
                    nearest = min(red_units, key=lambda e: _dist(u, e))
                    if u.can_attack(nearest):
                        u.action_type   = 'attack'
                        u.action_target = nearest

        elif action == 10:
            if red_bases:
                target = red_bases[0]
                for u in blue_fighters:
                    dist = math.sqrt((u.x - target.x)**2 + (u.y - target.y)**2)
                    if dist <= u.attack_range + 1:
                        u.action_type   = 'attack_building'
                        u.action_target = target
                    else:
                        self._queue_move_toward(u, target.x, target.y)

        elif action == 11:
            if red_barracks:
                for u in blue_fighters:
                    nearest_bar = min(red_barracks, key=lambda b: _dist_xy(u.x, u.y, b.x, b.y))
                    dist = math.sqrt((u.x - nearest_bar.x)**2 + (u.y - nearest_bar.y)**2)
                    if dist <= u.attack_range + 1:
                        u.action_type   = 'attack_building'
                        u.action_target = nearest_bar
                    else:
                        self._queue_move_toward(u, nearest_bar.x, nearest_bar.y)
            elif red_bases:
                target = red_bases[0]
                for u in blue_fighters:
                    dist = math.sqrt((u.x - target.x)**2 + (u.y - target.y)**2)
                    if dist <= u.attack_range + 1:
                        u.action_type   = 'attack_building'
                        u.action_target = target
                    else:
                        self._queue_move_toward(u, target.x, target.y)
            else:
                for u in blue_fighters + blue_workers:
                    if not u.has_acted and red_units:
                        nearest = min(red_units, key=lambda e: _dist(u, e))
                        if u.can_attack(nearest):
                            u.action_type = 'attack'
                            u.action_target = nearest

        elif action == 12:
            resources = g.resources
            for w in blue_workers:
                if resources:
                    nearest_res = min(
                        (r for r in resources if not r.is_depleted() and isinstance(r, Minerals)),
                        key=lambda r: _dist_xy(w.x, w.y, r.x, r.y),
                        default=None
                    )
                    if nearest_res:
                        w.gather_target = nearest_res

        elif action == 13:
            resources = g.resources
            for w in blue_workers:
                if resources:
                    nearest_res = min(
                        (r for r in resources if not r.is_depleted() and isinstance(r, Gas)),
                        key=lambda r: _dist_xy(w.x, w.y, r.x, r.y),
                        default=None
                    )
                    if nearest_res:
                        w.gather_target = nearest_res

    def _queue_move_toward(self, unit, tx: int, ty: int):
        moves = unit.get_possible_moves()
        if not moves:
            return
        best = min(moves, key=lambda m: _dist_xy(m[0], m[1], tx, ty))
        if not self.game.is_cell_occupied(best[0], best[1], exclude_unit=unit):
            unit.action_type   = 'move'
            unit.action_target = best

    def _recruit_in_barracks(self, g, utype, cost: dict, barracks_list: list):
        if not barracks_list:
            return
        res = g.player_resources['blue']
        if res['minerals'] < cost['minerals'] or res['gas'] < cost['gas']:
            return
        b = barracks_list[0]
        res['minerals'] -= cost['minerals']
        res['gas']      -= cost['gas']
        b.start_production(utype, cost)

    def _place_building(self, g, worker, btype: str, cost: dict, res: dict) -> bool:
        for r in range(2, 6):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    nx = int(worker.x) + dx
                    ny = int(worker.y) + dy
                    if 0 <= nx < GW and 0 <= ny < GH:
                        if not g.is_cell_occupied(nx, ny):
                            key = (nx, ny, btype)
                            if key not in g.pending_builds:
                                res['minerals'] -= cost['minerals']
                                res['gas']      -= cost.get('gas', 0)
                                g.pending_builds[key] = 2
                                worker.has_acted = True
                                return True
        return False

    def _compute_reward(self) -> float:
        g = self.game
        action = getattr(self, '_last_action', -1)
        res = g.player_resources['blue']
        blue_units    = [u for u in g.units if u.player == 'blue']
        red_units     = [u for u in g.units if u.player == 'red']
        blue_blds     = [b for b in g.buildings if b.player == 'blue']
        red_blds      = [b for b in g.buildings if b.player == 'red']
        blue_workers  = [u for u in blue_units if isinstance(u, Worker)]
        blue_barracks = [b for b in blue_blds if isinstance(b, Barracks)]
        blue_fighters = [u for u in blue_units if not isinstance(u, Worker)]
        red_bases     = [b for b in red_blds if isinstance(b, Base)]
        n_blue_units    = len(blue_units)
        n_red_units     = len(red_units)
        n_blue_blds     = len(blue_blds)
        n_red_blds      = len(red_blds)
        n_blue_fighters = len(blue_fighters)

        reward = -0.01

        red_killed  = max(0, self._prev_red_units  - n_red_units)
        blue_killed = max(0, self._prev_blue_units - n_blue_units)
        reward += 1.5 * red_killed
        reward -= 0.3 * blue_killed

        red_base_hp_now = sum(b.hp for b in red_bases) if red_bases else 0
        base_dmg_dealt  = max(0, self._prev_red_base_hp - red_base_hp_now)
        reward += 0.01 * base_dmg_dealt

        red_total_hp_now = sum(u.hp for u in red_units) + sum(b.hp for b in red_blds)
        hp_dmg_dealt     = max(0, self._prev_red_total_hp - red_total_hp_now)
        reward += 0.005 * hp_dmg_dealt

        red_bld_lost  = max(0, self._prev_red_buildings - n_red_blds)
        blue_bld_lost = max(0, self._prev_blue_buildings - n_blue_blds)
        reward += 3.0 * red_bld_lost
        reward -= 1.0 * blue_bld_lost

        blue_new_fighters = max(0, n_blue_fighters - self._prev_blue_fighters)
        reward += 0.4 * blue_new_fighters

        minerals_gained = max(0, res['minerals'] - self._prev_blue_minerals)
        gas_gained      = max(0, res['gas']      - self._prev_blue_gas)
        minerals_minus = min(0, res['minerals'] - self._prev_blue_minerals)
        gas_minus = min(0, res['gas'] - self._prev_blue_gas)
        economy_scale   = max(0.05, 1.0 - 0.2 * n_blue_fighters)
        reward += economy_scale * 0.005 * minerals_gained
        reward += economy_scale * 0.01 * gas_gained
        reward += 0.01 * minerals_minus
        reward += 0.015 * gas_minus

        if red_bases and blue_fighters:
            target  = red_bases[0]
            avg_dist = (
                sum(math.sqrt((u.x - target.x)**2 + (u.y - target.y)**2)
                    for u in blue_fighters)
                / len(blue_fighters)
            )
            prev_dist        = self._prev_avg_dist_to_base
            dist_improvement = prev_dist - avg_dist
            reward += 0.06 * dist_improvement
            self._prev_avg_dist_to_base = avg_dist

        invalid = False
        if action == 13 and not blue_workers:               invalid = True
        if action in (4, 5, 6) and not blue_barracks:       invalid = True
        if action in (7, 8, 9, 10, 11, 12) and not blue_fighters: invalid = True
        if action == 5 and res['minerals'] < 50:            invalid = True
        if invalid:
            reward -= 0.05

        if g.game_over:
            if g.winner == 'blue':
                reward += 20.0
            elif g.winner == 'red':
                reward -= 10.0
            else:
                reward -= 5.0

        return float(reward)

    def _sync_prev_state(self):
        g = self.game
        self._prev_blue_units     = len([u for u in g.units if u.player == 'blue'])
        self._prev_blue_fighters  = len([u for u in g.units if u.player == 'blue' and not isinstance(u, Worker)])
        self._prev_red_units      = len([u for u in g.units if u.player == 'red'])
        self._prev_blue_buildings = len([b for b in g.buildings if b.player == 'blue'])
        self._prev_red_buildings  = len([b for b in g.buildings if b.player == 'red'])
        self._prev_blue_minerals  = g.player_resources['blue']['minerals']
        self._prev_blue_gas       = g.player_resources['blue']['gas']
        red_bases = [b for b in g.buildings if b.player == 'red' and isinstance(b, Base)]
        self._prev_red_base_hp = sum(b.hp for b in red_bases) if red_bases else 0
        red_units = [u for u in g.units if u.player == 'red']
        red_blds  = [b for b in g.buildings if b.player == 'red']
        self._prev_red_total_hp = (
            sum(u.hp for u in red_units) + sum(b.hp for b in red_blds)
        )
        blue_fighters = [u for u in g.units if u.player == 'blue' and not isinstance(u, Worker)]
        if red_bases and blue_fighters:
            target = red_bases[0]
            self._prev_avg_dist_to_base = (
                sum(math.sqrt((u.x - target.x)**2 + (u.y - target.y)**2)
                    for u in blue_fighters)
                / len(blue_fighters)
            )

def _dist(a, b) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

def _dist_xy(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

ACTION_NAMES = [
    "0  Постройка башни",
    "1  Постройка казармы",
    "2  Создание рабочего",
    "3  Создание дальнобойного",
    "4  Создание лёгкого",
    "5  Создание тяжёлого",
    "6  Бойцы → база врага",
    "7  Бойцы → казарма врага",
    "8  Бойцы → ближайший враг",
    "9 Атака врага в радиусе",
    "10 Атака базы врага",
    "11 Атака казарм врага",
    "12 Рабочие → минералы",
    "13 Рабочие → газ"
]