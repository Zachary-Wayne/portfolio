import heapq
import tkinter as tk
import numpy as np
import math
import random
from typing import Tuple

from utils import profiler_attach


def generate_perlin_noise_2d(shape: Tuple[int, int], res: Tuple[int, int], seed: int = 0) -> np.ndarray:
	np.random.seed(seed)

	def f(_t):
		return 6 * _t ** 5 - 15 * _t ** 4 + 10 * _t ** 3

	delta = (res[0] / shape[0], res[1] / shape[1])
	d = (shape[0] // res[0], shape[1] // res[1])
	grid = np.mgrid[0:res[0]:delta[0], 0:res[1]:delta[1]].transpose(1, 2, 0) % 1

	angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
	gradients = np.dstack((np.cos(angles), np.sin(angles)))

	g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
	g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
	g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
	g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)

	t = f(grid)

	n00 = np.sum(grid * g00, 2)
	n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
	n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
	n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)

	n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
	n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11

	return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)


def is_adjacent(entity: LivingEntity, tx: int, ty: int) -> bool:
	return abs(entity.x - tx) <= 1 and abs(entity.y - ty) <= 1 and (entity.x != tx or entity.y != ty)


class Tile:
	def __init__(self, name: str, colour: str):
		self.name = name
		self.colour = colour


class WallBlock(Tile):
	def __init__(self, name: str, colour: str, hardness: float = 1.0):
		super().__init__(name, colour)
		self.hardness = hardness


class FloorBlock(Tile):
	def __init__(self, name: str, colour: str, speed_buff: float = 1.0):
		super().__init__(name, colour)
		self.speed_buff = speed_buff


WallBlock.air = WallBlock("Air", "", hardness=0.0)
WallBlock.light_rock = WallBlock("Light Rock", "#9A9A9A", hardness=1.5)
WallBlock.rock = WallBlock("Rock", "#786b68", hardness=2.0)
WallBlock.granite = WallBlock("Granite", "#4B4B4B", hardness=5)

FloorBlock.dirt = FloorBlock("Dirt", "#16100f", speed_buff=1.0)
FloorBlock.mud = FloorBlock("Mud", "#433c3a", speed_buff=0.3)


class Item:
	def __init__(self, name: str):
		self.name = name


class BlockItem(Item):
	def __init__(self, block: WallBlock):
		super().__init__(name=block.name)
		self.block = block


class ActionModifier:
	def __init__(self, action_type: type[Action], name: str, multiplier: float):
		self.action_type = action_type
		self.name = name
		self.multiplier = multiplier


class ModifierContainer:
	def __init__(self):
		self.modifiers: list[ActionModifier] = []

	def append(self, action_type: type[Action], name: str, multiplier: float):
		self.modifiers.append(ActionModifier(action_type, name, multiplier))

	def get_multiplier(self, action: Action) -> float:
		total_mult = 1.0
		for mod in self.modifiers:
			if isinstance(action, mod.action_type):
				total_mult *= mod.multiplier
		return total_mult


class Action:
	def __init__(self, steps_per_action: float = 1.0):
		self.steps_per_action = steps_per_action

	def cost(self, entity, world) -> float:
		return self.steps_per_action // entity.action_modifier.get_multiplier(type(self))

	def execute(self, entity, world) -> bool:
		raise NotImplementedError

	@staticmethod
	def has_valid_speed_multiplier(action_cls, entity) -> bool:
		return entity.action_modifier.get_multiplier(action_cls) > 0


class MoveAction(Action):
	def __init__(self, dx: int = 0, dy: int = 0):
		super().__init__(steps_per_action=1.0)
		self.dx = dx
		self.dy = dy

	def cost(self, entity, world) -> float:
		if self.dx == 0 and self.dy == 0: return 0.0
		base_cost = ((abs(self.dx) + abs(self.dy)) * self.steps_per_action) // world.get_cell(entity.x, entity.y).floor_block.speed_buff

		return base_cost / entity.action_modifier.get_multiplier(self)

	def execute(self, entity, world) -> bool:
		nx, ny = entity.x + self.dx, entity.y + self.dy
		cell = world.get_cell(nx, ny)
		if cell.wall_block is WallBlock.air and cell.entity is None:
			entity.x, entity.y = nx, ny
			return True
		return False


class BreakBlockAction(Action):
	def __init__(self, tx: int = 0, ty: int = 0):
		super().__init__(steps_per_action=5.0)
		self.tx = tx
		self.ty = ty

	def cost(self, entity, world) -> float:
		cell = world.get_cell(self.tx, self.ty)
		return (self.steps_per_action * cell.wall_block.hardness) / entity.action_modifier.get_multiplier(self)

	def execute(self, entity, world) -> bool:
		if is_adjacent(entity, self.tx, self.ty) and world.get_cell(self.tx, self.ty) is not WallBlock.air:
			world.set_cell(self.tx, self.ty, None, WallBlock.air)
			return True
		return False


class PlaceBlockAction(Action):
	def __init__(self, tx: int = 0, ty: int = 0):
		super().__init__(steps_per_action=2.0)
		self.tx = tx
		self.ty = ty

	def execute(self, entity, world) -> bool:
		if is_adjacent(entity, self.tx, self.ty):
			if world.is_cell_walkable(self.tx, self.ty) and not world.get_entity_at(self.tx, self.ty):
				item = entity.inventory.remove_by_type(BlockItem)
				if isinstance(item, BlockItem):
					world.set_block(self.tx, self.ty, item.block)
					return True
		return False


class Inventory:
	def __init__(self, capacity: int = 10):
		self.items: list[Item] = []
		self.capacity = capacity

	def add(self, item: Item) -> bool:
		if len(self.items) < self.capacity:
			self.items.append(item)
			return True
		return False

	def remove_by_type(self, item_type: type[Item] = Item) -> Item | None:
		items = self.items
		for idx in range(len(items)):
			item = items[idx]
			if isinstance(item, item_type):
				return items.pop(idx)
		return None

	def has_any(self) -> bool:
		return bool(self.items)


class PathfindingAgent:
	@staticmethod
	def evaluate_step(entity, world, current_pos: tuple[int, int], target_pos: tuple[int, int]):
		tx, ty = target_pos
		cx, cy = current_pos
		cell = world.get_terrain_cell(tx, ty)
		if cell.entity is not None:
			return MoveAction(0, 0), float(1)

		if cell.wall_block is WallBlock.air:
			action = MoveAction(tx - cx, ty - cy)
		else:
			action = BreakBlockAction(tx, ty)
		return action, action.cost(entity, world)

	@staticmethod
	def actions_to_target(
			entity: LivingEntity,
			start_x: int,
			start_y: int,
			target_x: int,
			target_y: int,
			world,
			max_depth: int = 50
	) -> list[Action]:
		if (start_x, start_y) == (target_x, target_y):
			return []

		dx_total = target_x - start_x
		dy_total = target_y - start_y
		if abs(dx_total) <= 1 and abs(dy_total) <= 1:
			step_action, _ = PathfindingAgent.evaluate_step(entity, world, (start_x, start_y), (target_x, target_y))
			if step_action is not None:
				return [step_action]

		visited_tile_costs = {(start_x, start_y): 0.0}
		counter = 0
		priority_queue = [(0.0, start_x, start_y, 0, counter)]
		predecessors = {}
		action_map = {}
		direction_offsets = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]

		while priority_queue:
			c_cost, c_x, c_y, c_depth, _ = heapq.heappop(priority_queue)

			if c_x == target_x and c_y == target_y:
				_actions = []
				target_pos = (target_x, target_y)
				while target_pos in predecessors:
					_actions.append(action_map[target_pos])
					target_pos = predecessors[target_pos]
				_actions.reverse()
				return _actions

			if c_depth >= max_depth:
				continue

			pos = (c_x, c_y)
			if visited_tile_costs.get(pos, float('inf')) < c_cost:
				continue

			for dx, dy in direction_offsets:
				n_x, n_y = c_x + dx, c_y + dy
				n_pos = (n_x, n_y)

				step_action, step_cost = PathfindingAgent.evaluate_step(entity, world, pos, n_pos)
				if step_action is None:
					continue

				t_cost = c_cost + step_cost
				t_depth = c_depth + 1

				if n_pos not in visited_tile_costs or t_cost < visited_tile_costs[n_pos]:
					visited_tile_costs[n_pos] = t_cost
					predecessors[n_pos] = pos
					action_map[n_pos] = step_action
					counter += 1
					heapq.heappush(priority_queue, (t_cost, n_x, n_y, t_depth, counter))
		return []


class Behaviour:
	@staticmethod
	def chase(entity: LivingEntity, target: LivingEntity, world) -> Action | None:
		if not entity.current_path:
			entity.current_path = PathfindingAgent.actions_to_target(entity, entity.x, entity.y, target.x, target.y, world)
		if not entity.current_path:
			return None
		return entity.current_path.pop(0)


# return PathfindingAgent.actions_to_target(entity, entity.x, entity.y, target.x, target.y, world)[0]


class LivingEntity:
	def __init__(self, x: int, y: int, hp: int = 10, colour: str = "#FFFFFF"):
		self.x: int = x
		self.y: int = y
		self.colour = colour

		self.hp = hp
		self.max_hp = hp
		self.inventory = Inventory(capacity=5)
		self.is_alive = True

		self.action_modifier = ModifierContainer()
		self.active_action: Action | None = None
		self.action_steps_remaining = 0.0

		self.current_path: list[Action] = []

	def take_damage(self, amount: int):
		self.hp -= amount
		if self.hp <= 0:
			self.is_alive = False

	def update_turn(self, world):
		if not self.is_alive: return
		if self.active_action is not None:
			self.action_steps_remaining -= 1.0
			if self.action_steps_remaining <= 0:
				action = self.active_action
				self.active_action = None
				action.execute(self, world)
			return
		action = self.choose_action(world)
		if action: self.begin_action(action, world)

	def choose_action(self, world) -> Action | None:
		raise NotImplementedError(self.__class__.__name__)

	def begin_action(self, action: Action, world):
		cost = action.cost(self, world)
		if cost <= 1:
			action.execute(self, world)
		else:
			self.active_action = action
			self.action_steps_remaining = cost - 1

	def draw(self, canvas, center_x, center_y, camera_x, camera_y, tile_size):
		sx = center_x + (self.x - camera_x) * tile_size
		sy = center_y + (self.y - camera_y) * tile_size
		t = tile_size - 2
		canvas.create_rectangle(sx + 2, sy + 2, sx + t, sy + t, fill=self.colour, outline="")


class NonPlayerEntity(LivingEntity):
	def __init__(self, x, y):
		super().__init__(x, y, hp=10, colour="#FF4444")
		self.action_modifier.append(MoveAction, "Slow Moving", 0.5)
		self.action_modifier.append(BreakBlockAction, "Fast Digging", 2)

	def choose_action(self, world) -> Action | None:
		return Behaviour.chase(self, world.player, world)


class Player(LivingEntity):
	def __init__(self, x, y):
		super().__init__(x, y, hp=20, colour="#00FFCC")
		self.pending_action: Action | None = None

	def queue_move(self, event, dx: int, dy: int, world):
		if self.pending_action is not None or self.action_steps_remaining > 0:
			return
		self.pending_action = MoveAction(dx=dx, dy=dy)

	def queue_break_block(self, event, world):
		if self.pending_action is not None or self.action_steps_remaining > 0:
			return

		center_x = world.canvas_width // 2 + world.tile_size // 2
		center_y = world.canvas_height // 2 + world.tile_size // 2

		dx = event.x - center_x
		dy = event.y - center_y

		if dx == 0 and dy == 0:
			return

		angle = math.atan2(dy, dx)
		octant = int(round(4 * angle / math.pi) + 4) % 8
		direction_map = ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1))

		off_x, off_y = direction_map[octant]
		target_x = self.x + off_x
		target_y = self.y + off_y

		cell = world.get_cell(target_x, target_y)
		if cell.wall_block is not WallBlock.air:
			self.pending_action = BreakBlockAction(tx=target_x, ty=target_y)

	def choose_action(self, world) -> Action | None:
		action = self.pending_action
		self.pending_action = None
		return action


class Cell:
	def __init__(self, floor_block: FloorBlock, wall_block: WallBlock, entity: LivingEntity | None = None):
		self.floor_block = floor_block
		self.wall_block = wall_block
		self.entity = entity

	def set_floor(self, floor_block: FloorBlock):
		self.floor_block = floor_block

	def set_wall(self, wall_block: WallBlock):
		self.wall_block = wall_block


class World:
	def __init__(self, root):
		self.root = root
		self.root.title("Procedural Map Generation")

		self.tile_size = 16
		self.chunk_size = 32
		self.canvas_width = 800
		self.canvas_height = 600

		self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="black")
		self.canvas.pack(fill='both', expand=True)

		self.chunks = {}
		self.entities = []
		self.entity_positions = {}

		self.current_step = 0
		self.tick_rate = 30
		self.noise_seed = random.randint(0, 10000)

		self.generate_chunk(0, 0)
		self._cached_chunk_coords = None
		self._cached_chunk = None

		self.player = Player(16, 16)
		self.ensure_player_spawn()
		self.spawn_initial_entities()

		self.canvas.bind("<Button-1>", lambda e: self.player.queue_break_block(e, self))
		self.canvas.bind("w", lambda e: self.player.queue_move(e, 0, -1, self))
		self.canvas.bind("s", lambda e: self.player.queue_move(e, 0, 1, self))
		self.canvas.bind("a", lambda e: self.player.queue_move(e, -1, 0, self))
		self.canvas.bind("d", lambda e: self.player.queue_move(e, 1, 0, self))
		self.canvas.bind("<Shift-A>", lambda e: self.player.queue_move(e, -1, -1, self))
		self.canvas.bind("<Shift-D>", lambda e: self.player.queue_move(e, 1, -1, self))
		self.canvas.bind("<Control-a>", lambda e: self.player.queue_move(e, -1, 1, self))
		self.canvas.bind("<Control-d>", lambda e: self.player.queue_move(e, 1, 1, self))

		self.canvas.focus_set()

		self.game_loop()
		self.render()

	def spawn_initial_entities(self):
		for dx, dy in [(5, 0), (-5, 0), (0, 5), (0, -5), (5, 5), (-5, 5), (5, -5), (-5, -5), ]:
			ex, ey = self.player.x + dx, self.player.y + dy
			self.set_cell(ex, ey, wall=WallBlock.air)
			self.entities.append(NonPlayerEntity(ex, ey))
		self.update_entity_positions()

	@profiler_attach(condition=lambda self: (self.player.pending_action is not None or self.player.active_action is not None))
	def game_loop(self):
		if self.player.pending_action is not None or self.player.active_action is not None:
			self.current_step += 1
			self.player.update_turn(self)

			for entity in self.entities:
				entity.update_turn(self)

			self.update_entity_positions()

		self.render()
		self.root.after(self.tick_rate, self.game_loop)

	def update_entity_positions(self):
		self.entity_positions = {(e.x, e.y): e for e in self.entities if e.is_alive}

	def get_chunk_coords(self, grid_x: int, grid_y: int):
		size = self.chunk_size
		return grid_x // size, grid_y // size

	def get_terrain_cell(self, grid_x: int, grid_y: int) -> Cell:
		size = self.chunk_size
		cx, cy = grid_x // size, grid_y // size

		if (cx, cy) != self._cached_chunk_coords:
			key = (cx, cy)
			chunk = self.chunks.get(key)

			if chunk is None:
				self.generate_chunk(cx, cy)
				chunk = self.chunks[key]

			self._cached_chunk_coords = (cx, cy)
			self._cached_chunk = chunk

		return self._cached_chunk[grid_y % size][grid_x % size]

	def get_cell(self, grid_x: int, grid_y: int) -> Cell:
		cell = self.get_terrain_cell(grid_x, grid_y)

		if self.player.is_alive and self.player.x == grid_x and self.player.y == grid_y:
			cell.entity = self.player
		else:
			cell.entity = self.entity_positions.get((grid_x, grid_y))

		return cell

	def set_cell(self, grid_x: int, grid_y: int, floor: FloorBlock | None = None, wall: WallBlock | None = None, entity: LivingEntity | None = None):
		cx, cy = self.get_chunk_coords(grid_x, grid_y)
		if (cx, cy) not in self.chunks:
			self.generate_chunk(cx, cy)
		lx = grid_x % self.chunk_size
		ly = grid_y % self.chunk_size

		cell = self.chunks[(cx, cy)][ly][lx]

		if floor is not None:
			cell.floor_block = floor
		if wall is not None:
			cell.wall_block = wall
		if entity is not None:
			cell.entity = entity

	def generate_chunk(self, cx, cy):
		seed_f = hash((cx, cy, self.noise_seed, "floor")) % (2 ** 32)
		seed_w = hash((cx, cy, self.noise_seed, "wall")) % (2 ** 32)

		floor_noise = generate_perlin_noise_2d((self.chunk_size, self.chunk_size), (4, 4), seed=seed_f)
		wall_noise = generate_perlin_noise_2d((self.chunk_size, self.chunk_size), (4, 4), seed=seed_w)

		grid: list[list[Cell]] = []
		for ly in range(self.chunk_size):
			row: list[Cell] = []
			for lx in range(self.chunk_size):
				fn = floor_noise[ly, lx]
				wn = wall_noise[ly, lx]

				if fn < -0.5:
					floor = FloorBlock.mud
				else:
					floor = FloorBlock.dirt

				if wn < -0.9:
					wall = WallBlock.granite
				elif wn < 0.5:
					wall = WallBlock.rock
				else:
					wall = WallBlock.light_rock

				row.append(Cell(floor, wall))
			grid.append(row)

		self.chunks[(cx, cy)] = grid
		mid = self.chunk_size // 2

		tunnelers = [{
			'x': mid,
			'y': mid,
			'dx': random.choice([-1, 0, 1]),
			'dy': random.choice([-1, 0, 1]),
			'width': random.choice([1, 2]),
			'life': random.randint(30, 60)
		}]

		rooms_to_dig = random.randint(2, 4)
		for _ in range(rooms_to_dig):
			rw = random.randint(4, 12)
			rh = random.randint(4, 12)
			rx = random.randint(1, max(1, self.chunk_size - rw - 1))
			ry = random.randint(1, max(1, self.chunk_size - rh - 1))

			# Rooms build stone paths over whatever floor is beneath
			for y in range(ry, min(self.chunk_size, ry + rh)):
				for x in range(rx, min(self.chunk_size, rx + rw)):
					grid[y][x] = Cell(FloorBlock.dirt, WallBlock.air)

		while tunnelers:
			t = tunnelers.pop(0)
			while t['life'] > 0:
				for w_x in range(t['width']):
					for w_y in range(t['width']):
						tx, ty = t['x'] + w_x, t['y'] + w_y
						if 0 <= tx < self.chunk_size and 0 <= ty < self.chunk_size:
							cell = grid[ty][tx]
							grid[ty][tx] = Cell(cell.floor_block, WallBlock.air)

				t['x'] += t['dx']
				t['y'] += t['dy']
				t['life'] -= 1

				if not (0 <= t['x'] < self.chunk_size and 0 <= t['y'] < self.chunk_size):
					break

				if random.random() < 0.15:
					t['dx'], t['dy'] = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

				if random.random() < 0.05:
					rw = random.randint(3, 5)
					rh = random.randint(3, 5)
					for y in range(t['y'], min(self.chunk_size, t['y'] + rh)):
						for x in range(t['x'], min(self.chunk_size, t['x'] + rw)):
							if 0 <= x < self.chunk_size and 0 <= y < self.chunk_size:
								grid[y][x] = Cell(FloorBlock.dirt, WallBlock.air)

				if random.random() < 0.08 and len(tunnelers) < 3:
					tunnelers.append({
						'x': t['x'],
						'y': t['y'],
						'dx': random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])[0],
						'dy': random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])[1],
						'width': random.choice([1, 2]),
						'life': random.randint(15, 30)
					})

		for i in range(self.chunk_size):
			if mid - 1 <= i <= mid + 1:
				grid[mid][i].wall_block = WallBlock.air
				grid[i][mid].wall_block = WallBlock.air

	def render(self):
		self.canvas.delete("all")

		center_x = self.canvas_width // 2
		center_y = self.canvas_height // 2

		visible_tiles_x = (self.canvas_width // self.tile_size) // 2 + 2
		visible_tiles_y = (self.canvas_height // self.tile_size) // 2 + 2

		min_gx = self.player.x - visible_tiles_x
		max_gx = self.player.x + visible_tiles_x
		min_gy = self.player.y - visible_tiles_y
		max_gy = self.player.y + visible_tiles_y

		for gy in range(min_gy, max_gy):
			for gx in range(min_gx, max_gx):
				cell = self.get_cell(gx, gy)

				screen_x = center_x + (gx - self.player.x) * self.tile_size
				screen_y = center_y + (gy - self.player.y) * self.tile_size

				is_solid_wall = cell.wall_block is not WallBlock.air
				outline_colour = "#111111" if is_solid_wall else ""
				active_tile = cell.wall_block if is_solid_wall else cell.floor_block

				self.canvas.create_rectangle(
					screen_x, screen_y,
					screen_x + self.tile_size, screen_y + self.tile_size,
					fill=active_tile.colour, outline=outline_colour
				)

		for entity in self.entities:
			entity.draw(self.canvas, center_x, center_y, self.player.x, self.player.y, self.tile_size)

		self.player.draw(self.canvas, center_x, center_y, self.player.x, self.player.y, self.tile_size)

		self.canvas.create_text(
			10, 10,
			text=f"World Step: {self.current_step}",
			fill="#00FFCC",
			anchor="nw",
			font=("Consolas", 12, "bold")
		)

	def ensure_player_spawn(self):
		self.set_cell(self.player.x, self.player.y, wall=WallBlock.air)


if __name__ == "__main__":
	game_root = tk.Tk()
	game_app = World(game_root)
	game_root.mainloop()
