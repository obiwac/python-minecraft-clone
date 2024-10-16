import math
import matrix

class Camera:
	def __init__(self, shader, width, height):
        # Existing attributes
		self.width = width
		self.height = height
		self.mv_matrix = matrix.Matrix()
		self.p_matrix = matrix.Matrix()
		self.shader = shader
		self.shader_matrix_location = self.shader.find_uniform(b"matrix")
		self.input = [0, 0, 0]
		self.position = [0, 81.5, 0]
		self.rotation = [-math.tau / 4, 0]
        
        # New attribute for vertical velocity
		self.velocity_y = 0.0
		self.is_jumping = False  # To check if the player is in the middle of a jump


	def round_position(self, position):
		return [round(coord) for coord in position]

	def update_camera(self, delta_time, sprinting, world, flying):
		base_speed = 8
		sprint_multiplier = 2.0 if sprinting else 1.0
		multiplier = base_speed * sprint_multiplier * delta_time

		gravity = -20.0 * delta_time

		# Calculate movement vector for all directions (X, Y, Z)
		movement_vector = [0, 0, 0]

		if flying:
			movement_vector[1] = self.input[1] * multiplier
			self.velocity_y = 0  # Reset vertical velocity when flying
			self.is_jumping = False
		else:
			if self.is_jumping:
				# Apply velocity to the Y-axis during the jump
				movement_vector[1] = self.velocity_y
				self.velocity_y = -gravity  # Apply gravity to velocity

				# Stop the jump if the player reaches the max height or hits an obstacle
				if self.velocity_y <= 0 or not self.check_collision(world, [self.position[0], self.position[1] + movement_vector[1], self.position[2]]):
					self.is_jumping = False
					self.velocity_y = gravity
			else:
				movement_vector[1] = gravity

		# XZ-Axis Movement (left/right/forward/backward)
		if self.input[0] != 0 or self.input[2] != 0:
			angle = self.rotation[0] - math.atan2(self.input[2], self.input[0]) + math.tau / 4
			movement_vector[0] = math.cos(angle) * multiplier
			movement_vector[2] = math.sin(angle) * multiplier

		# Calculate the next position
		next_position = [
			self.position[0] + movement_vector[0],
			self.position[1] + movement_vector[1],
			self.position[2] + movement_vector[2],
		]

		# Check for collisions along each axis separately
		if self.check_collision(world, [next_position[0], self.position[1], self.position[2]]):
			self.position[0] = next_position[0]

		if self.check_collision(world, [self.position[0], next_position[1], self.position[2]]):
			self.position[1] = next_position[1]
		else:
			if movement_vector[1] < 0:
				self.velocity_y = 0
				self.is_jumping = False

		if self.check_collision(world, [self.position[0], self.position[1], next_position[2]]):
			self.position[2] = next_position[2]



	def check_collision(self, world, position):
		# Player's bounding box is 1x1x2 blocks, centered on the player's position.
		x, y, z = position
		corners_to_check = [
			(x - 0.5, y - 1.5, z - 0.5),  # bottom block, front left
			(x + 0.5, y - 1.5, z - 0.5),  # bottom block, front right
			(x - 0.5, y - 1.5, z + 0.5),  # bottom block, back left
			(x + 0.5, y - 1.5, z + 0.5),  # bottom block, back right

			(x - 0.5, y - 0.5, z - 0.5),  # top block, front left
			(x + 0.5, y - 0.5, z - 0.5),  # top block, front right
			(x - 0.5, y - 0.5, z + 0.5),  # top block, back left
			(x + 0.5, y - 0.5, z + 0.5),  # top block, back right
		]
		
		for corner in corners_to_check:
			if world.get_block_number(self.round_position(corner)) != 0:
				return False
		return True




	def update_matrices(self):
        # create projection matrix
		self.p_matrix.load_identity()
		self.p_matrix.perspective(90, float(self.width) / self.height, 0.1, 500)

        # create modelview matrix
		self.mv_matrix.load_identity()
		self.mv_matrix.rotate_2d(self.rotation[0] + math.tau / 4, self.rotation[1])
		self.mv_matrix.translate(-self.position[0], -self.position[1], -self.position[2])

        # modelviewprojection matrix
		mvp_matrix = self.mv_matrix * self.p_matrix
		self.shader.uniform_matrix(self.shader_matrix_location, mvp_matrix)
