import random
import player
import hit

from enum import IntEnum

class Controller:
	class InteractMode(IntEnum):
		PLACE = 0
		BREAK = 1
		PICK = 2

	class MiscMode(IntEnum):
		RANDOM = 0
		SAVE = 1
		ESCAPE = 2
		SPEED_TIME = 3
		FULLSCREEN = 4

	class MoveMode(IntEnum):
		LEFT = 0
		RIGHT = 1
		DOWN = 2
		UP = 3
		BACKWARD = 4
		FORWARD = 5

	class ModifierMode(IntEnum):
		SPRINT = 0

	def __init__(self, game):
		self.game = game

	def interact(self, mode):
		def hit_callback(current_block, next_block):
			if mode == self.InteractMode.PLACE: self.game.world.set_block(current_block, self.game.holding)
			elif mode == self.InteractMode.BREAK: self.game.world.set_block(next_block, 0)
			elif mode == self.InteractMode.PICK: self.game.holding = self.game.world.get_block_number(next_block)

		x, y, z = self.game.player.position
		y += self.game.player.eyelevel

		hit_ray = hit.Hit_ray(self.game.world, self.game.player.rotation, (x, y, z))

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
		elif mode == self.MiscMode.SPEED_TIME:
			self.game.world.speed_daytime()
		elif mode == self.MiscMode.FULLSCREEN:
			self.game.toggle_fullscreen()

	def update_move(self, axis):
		self.game.player.input[axis] = round(max(-1, min(self.game.controls[axis], 1)))

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
			self.game.player.target_speed = player.SPRINTING_SPEED

	def end_modifier(self, mode):
		if mode == self.ModifierMode.SPRINT:
			self.game.player.target_speed = player.WALKING_SPEED