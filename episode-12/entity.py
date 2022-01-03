import math

WALKING_SPEED = 7
GRAVITY = [0, -9.81, 0]

class Entity:
	def __init__(self):
		# physical variables

		self.position = [0, 80, 0]
		self.velocity = [0, 0, 0]
		self.acceleration = GRAVITY

		# input variables

		self.rotation = [-math.tau / 4, 0]
		self.speed = WALKING_SPEED

	def update(self, delta_time):
		# process physics
		
		self.velocity = [v + a * delta_time for v, a in zip(self.velocity, self.acceleration)]
		self.position = [p + v * delta_time for p, v in zip(self.position, self.velocity)]

		# compute collisions

		if self.position[1] < 70:
			self.position[1] = 70
			self.velocity[1] = 10