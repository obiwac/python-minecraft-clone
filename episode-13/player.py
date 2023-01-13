import math
import entity

WALKING_SPEED = 4.317
SPRINTING_SPEED = 7 # faster than in Minecraft, feels better

class Player(entity.Entity):
	def __init__(self, world, width, height):
		super().__init__(world, world.entity_types["Player"])

		self.view_width = width
		self.view_height = height

		# camera variables

		self.eyelevel = self.entity_type.height - 0.2
		self.input = [0, 0, 0]

		self.target_speed = WALKING_SPEED
		self.speed = self.target_speed

	def update(self, delta_time):
		# process input

		if delta_time * 20 > 1:
			self.speed = self.target_speed

		else:
			self.speed += (self.target_speed - self.speed) * delta_time * 20

		multiplier = self.speed * (1, 2)[self.flying]

		if self.flying and self.input[1]:
			self.accel[1] = self.input[1] * multiplier

		if self.input[0] or self.input[2]:
			angle = self.rotation[0] - math.atan2(self.input[2], self.input[0]) + math.tau / 4

			self.accel[0] = math.cos(angle) * multiplier
			self.accel[2] = math.sin(angle) * multiplier

		if not self.flying and self.input[1] > 0:
			self.jump()

		# process physics & collisions &c

		super().update(delta_time)

	def update_matrices(self):
		# create projection matrix

		self.world.p_matrix.load_identity()

		self.world.p_matrix.perspective(
			90 + 10 * (self.speed - WALKING_SPEED) / (SPRINTING_SPEED - WALKING_SPEED),
			float(self.view_width) / self.view_height, 0.1, 500)

		# create modelview matrix

		self.world.mv_matrix.load_identity()
		self.world.mv_matrix.rotate_2d(self.rotation[0] + math.tau / 4, self.rotation[1])
		self.world.mv_matrix.translate(-self.position[0], -self.position[1] - self.eyelevel, -self.position[2])

		# modelviewprojection matrix

		self.world.mvp_matrix = self.world.p_matrix * self.world.mv_matrix
