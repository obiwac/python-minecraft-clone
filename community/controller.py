import random
import camera
import hit

iota_counter = 0

def iota(reset=False):
	if reset: iota_counter = 0
	return (iota_counter := iota_counter + 1)

class Controller:
	class InteractMode:
		PLACE = iota()
		BREAK = iota()
		PICK = iota()
	iota(True)

	class MiscMode:
		RANDOM = iota()
		SAVE = iota()
		ESCAPE = iota()
	iota(True)

	class MoveMode:
		LEFT = iota()
		RIGHT = iota()
		DOWN = iota()
		UP = iota()
		BACKWARD = iota()
		FORWARD = iota()
	iota(True)

	class ModifierMode:
		SPRINT = iota()
	iota(True)

	def __init__(self, game):
		self.game = game

	def interact(self, mode):
		def hit_callback(current_block, next_block):
			if mode == self.InteractMode.PLACE: self.game.world.set_block(current_block, self.game.holding)
			elif mode == self.InteractMode.BREAK: self.game.world.set_block(next_block, 0)
			elif mode == self.InteractMode.PICK: self.game.holding = self.game.world.get_block_number(next_block)

		hit_ray = hit.Hit_ray(self.game.world, self.game.camera.rotation, self.game.camera.position)

		while hit_ray.distance < hit.HIT_RANGE:
			if hit_ray.step(hit_callback):
				break

	def misc(self, mode):
		if mode == self.MiscMode.RANDOM:
			self.game.holding = random.randint(1, len(self.game.world.block_types) - 1)
		elif mode == self.MiscMode.SAVE:
			self.game.world.save.save()
		elif mode == self.MiscMode.ESCAPE:
			self.game.mouse_captured = False
			self.game.set_exclusive_mouse(False)

	def update_move(self, axis):
		self.game.camera.input[axis] = round(max(-1, min(self.game.controls[axis], 1))) / (9.87 * 4.25)  # 9.87 gravity hehe (4.25 to make effect noticable)

	def start_move(self, mode):
		axis = int((mode if mode % 2 == 0 else mode - 1) / 2)
		self.game.controls[axis] += (-1 if mode % 2 == 0 else 1)
		self.update_move(axis)

	def end_move(self, mode):
		axis = int((mode if mode % 2 == 0 else mode - 1) / 2)
		self.game.controls[axis] -= (-1 if mode % 2 == 0 else 1)
		self.update_move(axis)

	def start_modifier(self, mode):
		if mode == self.ModifierMode.SPRINT:
			self.game.camera.target_speed = camera.SPRINTING_SPEED

	def end_modifier(self, mode):
		if mode == self.ModifierMode.SPRINT:
			self.game.camera.target_speed = camera.WALKING_SPEED
