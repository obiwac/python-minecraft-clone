
import math
import matrix

class Camera:
	def __init__(self, shader, width, height):
		self.width = width
		self.height = height

		# create matrices

		self.mv_matrix = matrix.Matrix()
		self.p_matrix = matrix.Matrix()

		# shaders

		self.shader = shader
		self.shader_matrix_location = self.shader.find_uniform(b"matrix")

		# camera variables

		self.input = [0, 0, 0]

		self.position = [0, 0, -3]
		self.rotation = [math.tau / 4, 0] # our starting x rotation needs to be tau / 4 since our 0 angle is on the positive x axis while what we consider "forwards" is the negative z axis
	
	def update_camera(self, delta_time):
		speed = 7
		multiplier = speed * delta_time

		self.position[1] += self.input[1] * multiplier
		
		if self.input[0] or self.input[2]: # important to check this because atan2(0, 0) is undefined
			angle = self.rotation[0] + math.atan2(self.input[2], self.input[0]) - math.tau / 4 # we need to subtract tau / 4 to move in the positive z direction instead of the positive x direction
			
			self.position[0] += math.cos(angle) * multiplier
			self.position[2] += math.sin(angle) * multiplier

	def update_matrices(self):
		# create projection matrix

		self.p_matrix.load_identity()
		self.p_matrix.perspective(90, float(self.width) / self.height, 0.1, 500)
		 
		# create modelview matrix

		self.mv_matrix.load_identity()

		self.mv_matrix.rotate_2d(-(self.rotation[0] - math.tau / 4), self.rotation[1]) # this needs to come first for a first person view and we need to play around with the x rotation angle a bit since our 0 angle is on the positive x axis while the matrix library's 0 angle is on the negative z axis (because of normalized device coordinates)
		self.mv_matrix.translate(-self.position[0], -self.position[1], self.position[2]) # this needs to be negative because if you remember from episode 4, we're technically moving the scene around the camera and not the camera around the scene (except for the z axis because of normalized device coordinates)

		# modelviewprojection matrix

		mvp_matrix = self.mv_matrix * self.p_matrix
		self.shader.uniform_matrix(self.shader_matrix_location, mvp_matrix)