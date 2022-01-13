import math
import glm
import options

WALKING_SPEED = 7
SPRINTING_SPEED = 21

class Camera:
	def __init__(self, shader, width, height):
		self.width = width
		self.height = height

		# create matrices

		self.mv_matrix = glm.mat4()
		self.p_matrix = glm.mat4()
		
		# shaders

		self.shader = shader
		self.mv_matrix_location = self.shader.find_uniform(b"u_ModelViewMatrix")
		self.p_matrix_location = self.shader.find_uniform(b"u_ProjMatrix")

		# camera variables

		self.input = [0, 0, 0]

		self.position = glm.vec3(0, 80, 0)
		self.rotation = glm.vec2(-math.tau / 4, 0)

		self.target_speed = WALKING_SPEED
		self.speed = self.target_speed
	
	def update_camera(self, delta_time):
		self.speed += (self.target_speed - self.speed) * delta_time * 20
		multiplier = self.speed * delta_time

		self.position.y += self.input[1] * multiplier

		if self.input[0] or self.input[2]:
			angle = self.rotation[0] - math.atan2(self.input[2], self.input[0]) + math.tau / 4

			self.position[0] += math.cos(angle) * multiplier
			self.position[2] += math.sin(angle) * multiplier
	
	def update_matrices(self):
		# create projection matrix
		
		self.p_matrix = glm.perspective(
			glm.radians(options.FOV + 20 * (self.speed - WALKING_SPEED) / (SPRINTING_SPEED - WALKING_SPEED)),
			float(self.width) / self.height, 0.1, 500)

		# create modelview matrix
		self.mv_matrix = glm.mat4(1.0)
		self.mv_matrix = glm.rotate(self.mv_matrix, self.rotation[1], -glm.vec3(1.0, 0.0, 0.0))
		self.mv_matrix = glm.rotate(self.mv_matrix, -(self.rotation[0] + math.tau / 4), -glm.vec3(0.0, 1.0, 0.0))
		self.mv_matrix = glm.translate(self.mv_matrix, -self.position)

		# modelviewprojection matrix


		self.shader.uniform_matrix(self.mv_matrix_location, self.mv_matrix)
		self.shader.uniform_matrix(self.p_matrix_location, self.p_matrix)
