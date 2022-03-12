import math
import collider

FLYING_ACCEL  = (0,   0, 0)
GRAVITY_ACCEL = (0, -32, 0)

# these values all come (losely) from Minecraft, but are multiplied by 20 (since Minecraft runs at 20 TPS)

FRICTION  = ( 20,  20,  20)

DRAG_FLY  = (  5,   5,   5)
DRAG_JUMP = (1.8,   0, 1.8)
DRAG_FALL = (1.8, 0.4, 1.8)

class Entity:
	def __init__(self, world):
		self.world = world

		# physical variables

		self.jump_height = 1.25
		self.flying = False

		self.position = [0, 80, 0]
		self.rotation = [-math.tau / 4, 0]

		self.velocity = [0, 0, 0]
		self.accel = [0, 0, 0]

		# collision variables

		self.width = 0.6
		self.height = 1.8

		self.collider = collider.Collider()
		self.grounded = False

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

		self.velocity[1] = math.sqrt(-2 * GRAVITY_ACCEL[1] * height)

	@property
	def friction(self):
		if self.flying:
			return DRAG_FLY

		elif self.grounded:
			return FRICTION

		elif self.velocity[1] > 0:
			return DRAG_JUMP

		return DRAG_FALL

	def update(self, delta_time):
		# apply input acceleration, and adjust for friction/drag

		self.velocity = [v + a * f * delta_time for v, a, f in zip(self.velocity, self.accel, self.friction)]
		self.accel = [0, 0, 0]

		# compute collisions

		self.update_collider()
		self.grounded = False

		for _ in range(3):
			adjusted_velocity = [v * delta_time for v in self.velocity]
			vx, vy, vz = adjusted_velocity

			# find all the blocks we could potentially be colliding with
			# this step is known as "broad-phasing"

			step_x = 1 if vx > 0 else -1
			step_y = 1 if vy > 0 else -1
			step_z = 1 if vz > 0 else -1

			steps_xz = int(self.width / 2)
			steps_y  = int(self.height)

			x, y, z = map(int, self.position)
			cx, cy, cz = [int(x + v) for x, v in zip(self.position, adjusted_velocity)]

			potential_collisions = []

			for i in range(x - step_x * (steps_xz + 1), cx + step_x * (steps_xz + 2), step_x):
				for j in range(y - step_y * (steps_y + 2), cy + step_y * (steps_y + 3), step_y):
					for k in range(z - step_z * (steps_xz + 1), cz + step_z * (steps_xz + 2), step_z):
						pos = (i, j, k)
						num = self.world.get_block_number(pos)

						if not num:
							continue

						for _collider in self.world.block_types[num].colliders:
							entry_time, normal = self.collider.collide(_collider + pos, adjusted_velocity)

							if normal is None:
								continue

							potential_collisions.append((entry_time, normal))

			# get first collision

			if not potential_collisions:
				break

			entry_time, normal = min(potential_collisions, key = lambda x: x[0])
			entry_time -= 0.001

			if normal[0]:
				self.velocity[0] = 0
				self.position[0] += vx * entry_time
			
			if normal[1]:
				self.velocity[1] = 0
				self.position[1] += vy * entry_time

			if normal[2]:
				self.velocity[2] = 0
				self.position[2] += vz * entry_time

			if normal[1] == 1:
				self.grounded = True

		self.position = [x + v * delta_time for x, v in zip(self.position, self.velocity)]

		# apply gravity acceleration

		gravity = FLYING_ACCEL if self.flying else GRAVITY_ACCEL
		self.velocity = [v + a * delta_time for v, a in zip(self.velocity, gravity)]

		# apply friction/drag

		self.velocity = [v - min(v * f * delta_time, v, key = abs) for v, f in zip(self.velocity, self.friction)]

		# make sure we can rely on the entity's collider outside of this function

		self.update_collider()