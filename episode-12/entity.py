
import math
import operator

WALKING_SPEED = 7
GRAVITY = (0, -32, 0)

class Box:
	def __init__(self, pos1 = (None,) * 3, pos2 = (None,) * 3):
		# pos1: position of the box vertex in the -X, -Y, -Z direction
		# pos2: position of the box vertex in the +X, +Y, +Z direction

		self.x1, self.y1, self.z1 = pos1
		self.x2, self.y2, self.z2 = pos2

class Entity:
	def __init__(self, world):
		self.world = world

		# physical variables

		self.height = 1.8
		self.width = 0.6
		self.jump_height = 1.25

		self.box = Box()

		self.acceleration = GRAVITY
		self.set_velocity((0, 0, 0))

		self.set_position((0, 80, 0))
		self.prev_pos = list(self.position)

		# input variables

		self.rotation = [-math.tau / 4, 0]
		self.speed = WALKING_SPEED

	def set_velocity(self, velocity): # TODO useful?
		self.velocity = velocity

	def set_position(self, position):
		self.position = list(position)
		x, y, z = position

		self.box.x1 = x - self.width / 2
		self.box.x2 = x + self.width / 2

		self.box.y1 = y
		self.box.y2 = y + self.height

		self.box.z1 = z - self.width / 2
		self.box.z2 = z + self.width / 2

	def ground(self):
		self.velocity[1] = 0

	def jump(self):
		# obviously, we can't initiate a jump while in mid-air

		if self.velocity[1]:
			return

		self.velocity[1] = math.sqrt(2 * self.jump_height * -GRAVITY[1])

	def collide(self, a, b, velocity):
		# a: the collider box, which moves
		# b: the static box, which stays put

		# TODO I shouldn't actually need this?

		x_overlap = min(a.x2, b.x2) - max(a.x1, b.x1)
		y_overlap = min(a.y2, b.y2) - max(a.y1, b.y1)
		z_overlap = min(a.z2, b.z2) - max(a.z1, b.z1)

		if any((x_overlap < 0, y_overlap < 0, z_overlap < 0)):
			return 1, (0,) * 3

		# find entry & exit times for each axis

		vx, vy, vz = velocity

		def div(x, y, default):
			if not y:
				return default
			
			return x / y

		x_entry = div(b.x1 - a.x2 if vx > 0 else b.x2 - a.x1, vx, -1)
		x_exit  = div(b.x2 - a.x1 if vx > 0 else b.x1 - a.x2, vx,  1)

		y_entry = div(b.y1 - a.y2 if vy > 0 else b.y2 - a.y1, vy, -1)
		y_exit  = div(b.y2 - a.y1 if vy > 0 else b.y1 - a.y2, vy,  1)

		z_entry = div(b.z1 - a.z2 if vz > 0 else b.z2 - a.z1, vz, -1)
		z_exit  = div(b.z2 - a.z1 if vz > 0 else b.z1 - a.z2, vz,  1)

		# on which axis did we collide first?

		entry = max(x_entry, y_entry, z_entry)
		exit_ = min(x_exit,  y_exit,  z_exit )

		# make sure we actually got a collision

		if entry > exit_ or entry < -1:
			return 1, (0,) * 3

		# find normal of surface we collided with

		nx = (0, -1 if vx > 0 else 1)[entry == x_entry]
		ny = (0, -1 if vy > 0 else 1)[entry == y_entry]
		nz = (0, -1 if vz > 0 else 1)[entry == z_entry]

		return entry, (nx, ny, nz)

	def update(self, delta_time):
		# process physics

		self.set_velocity([v + a * delta_time for v, a in zip(self.velocity, self.acceleration)])
		self.set_position([p + v * delta_time for p, v in zip(self.position, self.velocity)])

		# compute collisions

		for _ in range(3):
			x, y, z = self.prev_pos
			cx, cy, cz = self.position
			
			vx, vy, vz = (a - b for a, b in zip(self.position, self.prev_pos))

			# find all the blocks we could potentially be colliding with
			# this step is known as "broad-phasing"

			step_x = 1 if vx > 0 else -1
			step_y = 1 if vy > 0 else -1
			step_z = 1 if vz > 0 else -1

			potential_collisions = []

			for i in range(int(x) - step_x * 2, int(cx) + step_x * 3, step_x):
				for j in range(int(y) - step_y * 2, int(cy) + step_y * 4, step_y):
					for k in range(int(z) - step_z * 2, int(cz) + step_z * 3, step_z):
						pos = (i, j, k)
						num = self.world.get_block_number(pos)

						if not num:
							continue

						colliders = self.world.block_types[num].colliders

						for collider in colliders:
							collider = Box(
								(x + y for x, y in zip(collider[0], pos)),
								(x + y for x, y in zip(collider[1], pos))
							)

							entry_time, normal = self.collide(self.box, collider, (vx, vy, vz))

							if entry_time > 1:
								continue

							potential_collisions.append((entry_time, normal))

			# get first collision

			if not potential_collisions:
				break

			entry_time, normal = min(potential_collisions, key = lambda x: x[0])

			# TODO push back based on entry time so that this is still perfect when there's a shitton of lag

			if normal[0]:
				self.position[0] = self.prev_pos[0]# + vx * entry_time

			if normal[1]:
				self.position[1] = self.prev_pos[1]# + vy * entry_time
				self.ground()

			if normal[2]:
				self.position[2] = self.prev_pos[2]# + vz * entry_time

			self.set_position(self.position)

		self.prev_pos = list(self.position)