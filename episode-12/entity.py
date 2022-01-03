import math

WALKING_SPEED = 7
GRAVITY = [0, -9.81, 0]

class Entity:
	def __init__(self):
		# physical variables

		self.acceleration = GRAVITY

		self.set_position((0, 80, 0))
		self.set_velocity((0,  0, 0))

		# input variables

		self.rotation = [-math.tau / 4, 0]
		self.speed = WALKING_SPEED

	def set_velocity(self, velocity):
		self.velocity = velocity

	def set_position(self, position):
		self.position = position

	def update(self, delta_time):
		# process physics
		
		self.set_velocity((v + a * delta_time for v, a in zip(self.velocity, self.acceleration)))
		self.set_position((p + v * delta_time for p, v in zip(self.position, self.velocity)))

		# compute collisions

		if self.position[1] < 70:
			self.position[1] = 70
			self.velocity[1] = 10