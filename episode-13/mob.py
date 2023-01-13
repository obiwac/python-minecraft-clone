import random
import math

import entity

class Mob(entity.Entity):
	def __init__(self, world, entity_type):
		super().__init__(world, entity_type)

		self.heading = 0
		self.select_target()

		self.reset()

	def select_target(self):
		self.target = [x + random.randint(-5, 5) for x in self.position]

	def update(self, delta_time):
		if not random.randint(0, int(3 / delta_time)): # change target every 3 seconds on average
			self.select_target()

		delta_x = self.position[0] - self.target[0]
		delta_y = self.position[2] - self.target[2]

		self.heading = -math.atan2(delta_y, delta_x) + math.tau / 4
		self.heading += math.modf((self.rotation[0] - math.tau / 4) / math.tau)[1] * math.tau

		if delta_time * 5 > 1:
			self.rotation[0] = self.heading

		else:
			self.rotation[0] += (self.heading - self.rotation[0]) * delta_time * 5

		target_dist = math.sqrt(delta_x ** 2 + delta_y ** 2)

		if target_dist > 1:
			self.accel[0] =  math.cos(self.rotation[0] + math.tau / 4) * 3
			self.accel[2] = -math.sin(self.rotation[0] + math.tau / 4) * 3

		super().update(delta_time)

		if self.wall and self.grounded:
			if random.randint(0, 3):
				self.jump()

			else:
				self.select_target()

		if self.position[1] < 0:
			self.teleport((0, 80, 0))
