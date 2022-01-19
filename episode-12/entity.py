import math
import collider

WALKING_SPEED = 7

FLYING = (0, 0, 0)
GRAVITY = (0, -32, 0)

class Entity:
	def __init__(self, world):
		self.world = world

		# physical variables

		self.height = 1.8
		self.width = 0.6
		self.jump_height = 1.25
		self.flying = False

		self.collider = collider.Collider()
		self.velocity = (0, 0, 0)

		self.set_position((0, 80, 0))
		self.prev_pos = list(self.position)

		# input variables

		self.rotation = [-math.tau / 4, 0]
		self.speed = WALKING_SPEED

	def set_position(self, position):
		self.position = list(position)
		x, y, z = position

		self.collider.x1 = x - self.width / 2
		self.collider.x2 = x + self.width / 2

		self.collider.y1 = y
		self.collider.y2 = y + self.height

		self.collider.z1 = z - self.width / 2
		self.collider.z2 = z + self.width / 2

	def ground(self):
		self.velocity[1] = 0

	def teleport(self, pos):
		self.position = list(pos)
		self.prev_pos = list(self.position) # to prevent collisions
		self.velocity = (0, 0, 0)

	def jump(self):
		# obviously, we can't initiate a jump while in mid-air
		# TODO this isn't technically correct, as we could have 0 velocity, whilst not being grounded

		if self.velocity[1]:
			return

		self.velocity[1] = math.sqrt(2 * self.jump_height * -GRAVITY[1])

	def update(self, delta_time):
		# process physics

		acceleration = (GRAVITY, FLYING)[self.flying]

		self.velocity = [v + a * delta_time for v, a in zip(self.velocity, acceleration)]
		self.set_position([p + v * delta_time for p, v in zip(self.position, self.velocity)])

		# compute collisions

		for _ in range(3):
			vx, vy, vz = (a - b for a, b in zip(self.position, self.prev_pos))

			# find all the blocks we could potentially be colliding with
			# this step is known as "broad-phasing"

			step_x = 1 if vx > 0 else -1
			step_y = 1 if vy > 0 else -1
			step_z = 1 if vz > 0 else -1

			steps_xz = int(self.width)
			steps_y  = int(self.height)

			x,   y,  z = map(int, self.prev_pos)
			cx, cy, cz = map(int, self.position)

			potential_collisions = []

			for i in range(x - step_x * (steps_xz + 2), cx + step_x * (steps_xz + 3), step_x):
				for j in range(y - step_y * (steps_y + 2), cy + step_y * (steps_y + 3), step_y):
					for k in range(z - step_z * (steps_xz + 2), cz + step_z * (steps_xz + 3), step_z):
						pos = (i, j, k)
						num = self.world.get_block_number(pos)

						if not num:
							continue

						for collider in self.world.block_types[num].colliders:
							entry_time, normal = self.collider.collide(collider + pos, (vx, vy, vz))

							if entry_time > 1:
								continue

							potential_collisions.append((entry_time, normal))

			# get first collision

			if not potential_collisions:
				break

			# TODO use entry_time
			entry_time, normal = min(potential_collisions, key = lambda x: x[0])

			self.position[0] -= vx * abs(normal[0])
			self.position[1] -= vy * abs(normal[1])
			self.position[2] -= vz * abs(normal[2])

			# TODO cancel the velocity in any case where we collide on an axis

			if normal[1] == 1:
				self.ground()

			self.set_position(self.position)

		self.prev_pos = list(self.position)