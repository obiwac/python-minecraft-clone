class Collider:
	def __init__(self, pos1 = (None,) * 3, pos2 = (None,) * 3):
		# pos1: position of the collider vertex in the -X, -Y, -Z direction
		# pos2: position of the collider vertex in the +X, +Y, +Z direction

		self.x1, self.y1, self.z1 = pos1
		self.x2, self.y2, self.z2 = pos2

	def __add__(self, pos):
		x, y, z = pos

		return Collider(
			(self.x1 + x, self.y1 + y, self.z1 + z),
			(self.x2 + x, self.y2 + y, self.z2 + z)
		)

	def intersect(self, collider):
		x = min(self.x2, collider.x2) - max(self.x1, collider.x1)
		y = min(self.y2, collider.y2) - max(self.y1, collider.y1)
		z = min(self.z2, collider.z2) - max(self.z1, collider.z1)

		return all((x > 0, y > 0, z > 0))
	
	def collide(self, collider, velocity):
		# a: the dynamic collider, which moves
		# b: the static collider, which stays put

		if not self.intersect(collider):
			return 1, (0,) * 3

		# find entry & exit times for each axis

		vx, vy, vz = velocity

		def div(x, y, default):
			if not y:
				return default
			
			return x / y

		x_entry = div(collider.x1 - self.x2 if vx > 0 else collider.x2 - self.x1, vx, -1)
		x_exit  = div(collider.x2 - self.x1 if vx > 0 else collider.x1 - self.x2, vx,  1)

		y_entry = div(collider.y1 - self.y2 if vy > 0 else collider.y2 - self.y1, vy, -1)
		y_exit  = div(collider.y2 - self.y1 if vy > 0 else collider.y1 - self.y2, vy,  1)

		z_entry = div(collider.z1 - self.z2 if vz > 0 else collider.z2 - self.z1, vz, -1)
		z_exit  = div(collider.z2 - self.z1 if vz > 0 else collider.z1 - self.z2, vz,  1)

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