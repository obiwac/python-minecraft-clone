import math
import collider

FLYING = (0, 0, 0)
GRAVITY = (0, -32, 0)

class Entity:
	def __init__(self, world):
		self.world = world

		# physical variables

		self.jump_height = 1.25
		self.flying = False

		self.velocity = [0, 0, 0]
		self.position = [0, 80, 0]

		# collision variables

		self.height = 1.8
		self.width = 0.6

		self.collider = collider.Collider()
		self.grounded = False

		# input variables

		self.rotation = [-math.tau / 4, 0]

	def update_collider(self):
		x, y, z = self.position

		self.collider.x1 = x - self.width / 2
		self.collider.x2 = x + self.width / 2

		self.collider.y1 = y
		self.collider.y2 = y + self.height

		self.collider.z1 = z - self.width / 2
		self.collider.z2 = z + self.width / 2

	def teleport(self, pos):
		self.position = list(pos)
		self.velocity = [0, 0, 0] # to prevent collisions

	def jump(self, height = None):
		# obviously, we can't initiate a jump while in mid-air

		if not self.grounded:
			return

		if height is None:
			height = self.jump_height

		self.velocity[1] = math.sqrt(2 * height * -GRAVITY[1])

	def update(self, delta_time):
		# compute collisions

		self.update_collider()
		self.grounded = False

		for _ in range(3):
			adjusted_velocity = [v * delta_time or collider.PADDING for v in self.velocity]
			vx, vy, vz = adjusted_velocity

			# find all the blocks we could potentially be colliding with
			# this step is known as "broad-phasing"

			step_x = 1 if vx > 0 else -1
			step_y = 1 if vy > 0 else -1
			step_z = 1 if vz > 0 else -1

			steps_xz = int(self.width)
			steps_y  = int(self.height)

			x, y, z = map(int, self.position)
			cx, cy, cz = [int(x + v) for x, v in zip(self.position, adjusted_velocity)]

			potential_collisions = []

			for i in range(x - step_x * (steps_xz + 2), cx + step_x * (steps_xz + 3), step_x):
				for j in range(y - step_y * (steps_y + 2), cy + step_y * (steps_y + 3), step_y):
					for k in range(z - step_z * (steps_xz + 2), cz + step_z * (steps_xz + 3), step_z):
						pos = (i, j, k)
						num = self.world.get_block_number(pos)

						if not num:
							continue

						for _collider in self.world.block_types[num].colliders:
							shifted = _collider + pos
							entry_time, normal = self.collider.collide(shifted, (vx, vy, vz))

							if normal is None:
								continue

							potential_collisions.append((entry_time, normal))

			# get first collision

			if not potential_collisions:
				break

			entry_time, normal = min(potential_collisions, key = lambda x: x[0])

			if normal[0]:
				self.velocity[0] = 0
				self.position[0] += vx * entry_time - step_x * collider.PADDING
			
			if normal[1]:
				self.velocity[1] = 0
				self.position[1] += vy * entry_time - step_y * collider.PADDING

			if normal[2]:
				self.velocity[2] = 0
				self.position[2] += vz * entry_time - step_z * collider.PADDING

			if normal[1] == 1:
				self.grounded = True

		self.position = [x + v * delta_time for x, v in zip(self.position, self.velocity)]

		# process physics (apply acceleration, friction, & drag)

		acceleration = (GRAVITY, FLYING)[self.flying]
		self.velocity = [v + a * delta_time for v, a in zip(self.velocity, acceleration)]

		if self.grounded or self.flying:
			k = (1 - 0.95 * delta_time) ** 20 # takes 95% off of current velocity every 20th of a second

			self.velocity[0] *= k
			self.velocity[1] *= k
			self.velocity[2] *= k

		else:
			k = 0.98 ** (20 * delta_time) # takes 2% off of current velocity every 20th of a second

			self.velocity[0] *= k
			self.velocity[2] *= k

			if self.velocity[1] < 0:
				self.velocity[1] *= k