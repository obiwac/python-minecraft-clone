import math
import pyrr

WALKING_SPEED = 7
SPRINTING_SPEED = 21

class Camera:
	def __init__(self, shader, width, height):
		self.width = width
		self.height = height

		# create matrices

		# shaders

		self.shader = shader
		self.shader_matrix_location = self.shader.find_uniform(b"matrix")

		# camera variables

		self.input = [0, 0, 0]

		self.position = [0, 80, 0]
		self.rotation = [-math.tau / 4, 0]

		self.target_speed = WALKING_SPEED
		self.speed = self.target_speed
	
	def update_camera(self, delta_time):
		self.speed += (self.target_speed - self.speed) * delta_time * 20
		multiplier = self.speed * delta_time

		self.position[1] += self.input[1] * multiplier 

		if self.input[0] or self.input[2]:
			angle = self.rotation[0] - math.atan2(self.input[2], self.input[0]) + math.tau / 4

			self.position[0] += math.cos(angle) * multiplier
			self.position[2] += math.sin(angle) * multiplier

	# this a helper method to avoid puting all of this in update_matrices
	def rotate_matrix(self, baseMatrix, angle, x, y, z):
		magnitude = math.sqrt(x * x + y * y + z * z)

		x /= -magnitude
		y /= -magnitude
		z /= -magnitude

		sin_angle = math.sin(angle)
		cos_angle = math.cos(angle)
		one_minus_cos = 1.0 - cos_angle

		xx = x * x
		yy = y * y
		zz = z * z

		xy = x * y
		yz = y * z
		zx = z * x

		xs = x * sin_angle
		ys = y * sin_angle
		zs = z * sin_angle

		rotation_matrix = pyrr.Matrix44.identity()

		rotation_matrix[0][0] = (one_minus_cos * xx) + cos_angle
		rotation_matrix[0][1] = (one_minus_cos * xy) - zs
		rotation_matrix[0][2] = (one_minus_cos * zx) + ys

		rotation_matrix[1][0] = (one_minus_cos * xy) + zs
		rotation_matrix[1][1] = (one_minus_cos * yy) + cos_angle
		rotation_matrix[1][2] = (one_minus_cos * yz) - xs

		rotation_matrix[2][0] = (one_minus_cos * zx) - ys
		rotation_matrix[2][1] = (one_minus_cos * yz) + xs
		rotation_matrix[2][2] = (one_minus_cos * zz) + cos_angle

		rotation_matrix[3][3] = 1.0

		baseMatrix *= rotation_matrix

		return baseMatrix

	def update_matrices(self):
		# create projection matrix

		p_matrix = pyrr.Matrix44.perspective_projection(90 + 20 * (self.speed - WALKING_SPEED) / (SPRINTING_SPEED - WALKING_SPEED), float(self.width) / self.height, 0.1, 500)

		# create modelview matrix

		x = -(self.rotation[0] - math.tau / 4)

		mv_matrix = self.rotate_matrix(pyrr.Matrix44.identity(), x, 0, 1.0, 0)
		mv_matrix = self.rotate_matrix(mv_matrix, -self.rotation[1], math.cos(x), 0, math.sin(x))
		mv_matrix *= pyrr.Matrix44.from_translation((-self.position[0], -self.position[1], self.position[2]))

		# modelviewprojection matrix

		mvp_matrix = p_matrix * mv_matrix
		self.shader.uniform_matrix(self.shader_matrix_location, mvp_matrix)
