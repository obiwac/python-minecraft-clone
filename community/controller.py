import random
import camera
import hit

class Controller:
	class InteractMode:
		Place = 0
		Break = 1
		Pick = 2

	class MiscMode:
		Random = 0
		Save = 1
		Escape = 2

	class MoveMode:
		Left = 0
		Right = 1
		Down = 2
		Up = 3
		Backward = 4
		Forward = 5

	class ModifierMode:
		Sprint = 0

	def __init__(self, game):
		self.game = game

	def interact(self, mode):
		def hit_callback(current_block, next_block):
			if mode == self.InteractMode.Place: self.game.world.set_block(current_block, self.game.holding)
			elif mode == self.InteractMode.Break: self.game.world.set_block(next_block, 0)
			elif mode == self.InteractMode.Pick: self.game.holding = self.game.world.get_block_number(next_block)

		hit_ray = hit.Hit_ray(self.game.world, self.game.camera.rotation, self.game.camera.position)

		while hit_ray.distance < hit.HIT_RANGE:
			if hit_ray.step(hit_callback):
				break

	def misc(self, mode):
		if mode == self.MiscMode.Random:
			self.game.holding = random.randint(1, len(self.game.world.block_types) - 1)
		elif mode == self.MiscMode.Save:
			self.game.world.save.save()
		elif mode == self.MiscMode.Escape:
			self.game.mouse_captured = False
			self.game.set_exclusive_mouse(False)

	def update_move(self, axis):
		if self.game.controls[axis] > 0:
			self.game.camera.input[axis] = 1
		elif self.game.controls[axis] < 0:
			self.game.camera.input[axis] = -1
		elif self.game.controls[axis] == 0:
			self.game.camera.input[axis] = 0

	def start_move(self, mode):
		axis = int((mode if mode % 2 == 0 else mode - 1) / 2)
		self.game.controls[axis] += (-1 if mode % 2 == 0 else 1)
		self.update_move(axis)

	def end_move(self, mode):
		axis = int((mode if mode % 2 == 0 else mode - 1) / 2)
		self.game.controls[axis] -= (-1 if mode % 2 == 0 else 1)
		self.update_move(axis)

	def start_modifier(self, mode):
		if mode == self.ModifierMode.Sprint:
			self.game.camera.target_speed = camera.SPRINTING_SPEED

	def end_modifier(self, mode):
		if mode == self.ModifierMode.Sprint:
			self.game.camera.target_speed = camera.WALKING_SPEED