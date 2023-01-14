import random
import player
import chunk
import hit
import mob

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
		FLY = 5
		TELEPORT = 6
		TOGGLE_F3 = 7
		TOGGLE_AO = 8
		SPAWN = 9

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
			if mode == self.InteractMode.PLACE: self.game.world.try_set_block(current_block, self.game.holding, self.game.player.collider)
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

		elif mode == self.MiscMode.SPAWN:
			# _mob = mob.Mob(self.game.world, random.choice([*self.game.world.entity_types.values()]))
			_mob = mob.Mob(self.game.world, random.choice([self.game.world.entity_types["Zombie"], self.game.world.entity_types["Creeper"], self.game.world.entity_types["Skeleton"]]))
			self.game.world.entities.append(_mob)

			_mob.teleport(self.game.player.position)

		elif mode == self.MiscMode.SAVE:
			self.game.world.save.save()
		elif mode == self.MiscMode.ESCAPE:
			self.game.mouse_captured = False
			self.game.set_exclusive_mouse(False)
		elif mode == self.MiscMode.SPEED_TIME:
			self.game.world.speed_daytime()
		elif mode == self.MiscMode.FULLSCREEN:
			self.game.toggle_fullscreen()
		elif mode == self.MiscMode.FLY:
			self.game.player.flying = not self.game.player.flying
		elif mode == self.MiscMode.TELEPORT:
			# how large is the world?

			max_y = 0

			max_x, max_z = (0, 0)
			min_x, min_z = (0, 0)

			for pos in self.game.world.chunks:
				x, y, z = pos

				max_y = max(max_y, (y + 1) * chunk.CHUNK_HEIGHT)

				max_x = max(max_x, (x + 1) * chunk.CHUNK_WIDTH)
				min_x = min(min_x,  x      * chunk.CHUNK_WIDTH)

				max_z = max(max_z, (z + 1) * chunk.CHUNK_LENGTH)
				min_z = min(min_z,  z      * chunk.CHUNK_LENGTH)

			# get random X & Z coordinates to teleport the player to

			x = random.randint(min_x, max_x)
			z = random.randint(min_z, max_z)

			# find height at which to teleport to, by finding the first non-air block from the top of the world

			for y in range(chunk.CHUNK_HEIGHT - 1,  -1, -1):
				if not self.game.world.get_block_number((x, y, z)):
					continue

				self.game.player.teleport((x, y + 1, z))
				break
		elif mode == self.MiscMode.TOGGLE_F3:
			self.game.show_f3 = not self.game.show_f3
		elif mode == self.MiscMode.TOGGLE_AO:
			self.game.world.toggle_AO()

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
