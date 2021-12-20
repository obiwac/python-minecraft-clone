import math

HIT_RANGE = 3

class Hit_ray:
	def __init__(self, world, rotation, starting_position):
		self.world = world

		# get the ray unit vector based on rotation angles
		# sqrt(ux ^ 2 + uy ^ 2 + uz ^ 2) must always equal 1

		self.vector = (
			math.cos(rotation[0]) * math.cos(rotation[1]),
			math.sin(rotation[1]),
			math.sin(rotation[0]) * math.cos(rotation[1]))
		
		# point position
		self.position = list(starting_position)

		# block position in which point currently is
		self.block = tuple(map(lambda x: int(round(x)), self.position))

		# current distance the point has travelled
		self.distance = 0
	
	# 'check' and 'step' both return 'True' if something is hit, and 'False' if not

	def check(self, hit_callback, distance, current_block, next_block):
		if self.world.get_block_number(next_block):
			hit_callback(current_block, next_block)
			return True
		
		else:
			self.position = list(map(lambda x: self.position[x] + self.vector[x] * distance, range(3)))
			
			self.block = next_block
			self.distance += distance

			return False

	def step(self, hit_callback):
		bx, by, bz = self.block

		# point position relative to block centre
		local_position = list(map(lambda x: self.position[x] - self.block[x], range(3)))

		# we don't want to deal with negatives, so remove the sign
		# this is also cool because it means we don't need to take into account the sign of our ray vector
		# we do need to remember which components were negative for later on, however

		sign = [1, 1, 1] # '1' for positive, '-1' for negative
		absolute_vector = list(self.vector)

		for component, element in enumerate(self.vector):
			sign[component] = 2 * (element >= 0) - 1
			absolute_vector[component] *= sign[component]
			local_position[component] *= sign[component]
		
		lx, ly, lz = local_position
		vx, vy, vz = absolute_vector

		# calculate intersections
		# I only detail the math for the first component (X) because the rest is pretty self-explanatory

		# ray line (passing through the point) r ≡ (x - lx) / vx = (y - ly) / lz = (z - lz) / vz (parametric equation)

		# +x face fx ≡ x = 0.5 (y & z can be any real number)
		# r ∩ fx ≡ (0.5 - lx) / vx = (y - ly) / vy = (z - lz) / vz

		# x: x = 0.5
		# y: (y - ly) / vy = (0.5 - lx) / vx IFF y = (0.5 - lx) / vx * vy + ly
		# z: (z - lz) / vz = (0.5 - lx) / vx IFF z = (0.5 - lx) / vx * vz + lz

		if vx:
			x = 0.5
			y = (0.5 - lx) / vx * vy + ly
			z = (0.5 - lx) / vx * vz + lz

			if y >= -0.5 and y <= 0.5 and z >= -0.5 and z <= 0.5:
				distance = math.sqrt((x - lx) ** 2 + (y - ly) ** 2 + (z - lz) ** 2)
				
				# we can return straight away here
				# if we intersect with one face, we know for a fact we're not intersecting with any of the others

				return self.check(hit_callback, distance, (bx, by, bz), (bx + sign[0], by, bz))

		if vy:
			x = (0.5 - ly) / vy * vx + lx
			y = 0.5
			z = (0.5 - ly) / vy * vz + lz

			if x >= -0.5 and x <= 0.5 and z >= -0.5 and z <= 0.5:
				distance = math.sqrt((x - lx) ** 2 + (y - ly) ** 2 + (z - lz) ** 2)
				return self.check(hit_callback, distance, (bx, by, bz), (bx, by + sign[1], bz))
		
		if vz:
			x = (0.5 - lz) / vz * vx + lx
			y = (0.5 - lz) / vz * vy + ly
			z = 0.5

			if x >= -0.5 and x <= 0.5 and y >= -0.5 and y <= 0.5:
				distance = math.sqrt((x - lx) ** 2 + (y - ly) ** 2 + (z - lz) ** 2)
				return self.check(hit_callback, distance, (bx, by, bz), (bx, by, bz + sign[2]))