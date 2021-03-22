
import copy
import ctypes
import math

def copy_matrix(matrix):
	return copy.deepcopy(matrix) # we need to use deepcopy since we're dealing with 2D arrays

clean_matrix = [[0.0 for x in range(4)] for x in range(4)]
identity_matrix = copy_matrix(clean_matrix)

identity_matrix[0][0] = 1.0
identity_matrix[1][1] = 1.0
identity_matrix[2][2] = 1.0
identity_matrix[3][3] = 1.0

def multiply_matrices(x_matrix, y_matrix):
	result_matrix = copy_matrix(clean_matrix)
	
	for i in range(4):
		result_matrix[i][0] = \
			(x_matrix[i][0] * y_matrix[0][0]) + \
			(x_matrix[i][1] * y_matrix[1][0]) + \
			(x_matrix[i][2] * y_matrix[2][0]) + \
			(x_matrix[i][3] * y_matrix[3][0])
		
		result_matrix[i][1] = \
			(x_matrix[i][0] * y_matrix[0][1]) + \
			(x_matrix[i][1] * y_matrix[1][1]) + \
			(x_matrix[i][2] * y_matrix[2][1]) + \
			(x_matrix[i][3] * y_matrix[3][1])
		
		result_matrix[i][2] = \
			(x_matrix[i][0] * y_matrix[0][2]) + \
			(x_matrix[i][1] * y_matrix[1][2]) + \
			(x_matrix[i][2] * y_matrix[2][2]) + \
			(x_matrix[i][3] * y_matrix[3][2])
		
		result_matrix[i][3] = \
			(x_matrix[i][0] * y_matrix[0][3]) + \
			(x_matrix[i][1] * y_matrix[1][3]) + \
			(x_matrix[i][2] * y_matrix[2][3]) + \
			(x_matrix[i][3] * y_matrix[3][3])
	
	return result_matrix

class Matrix:
	def __init__(self, base = None):
		if type(base) == Matrix: self.data = copy_matrix(base.data)
		elif type(base) == list: self.data = copy_matrix(base)
		else: self.data = copy_matrix(clean_matrix)
	
	def load_identity(self):
		self.data = copy_matrix(identity_matrix)
	
	def __mul__(self, matrix):
		return Matrix(multiply_matrices(self.data, matrix.data))
	
	def __imul__(self, matrix):
		self.data = multiply_matrices(self.data, matrix.data)
	
	def scale(self, x, y, z):
		for i in range(4): self.data[0][i] *= x
		for i in range(4): self.data[1][i] *= y
		for i in range(4): self.data[2][i] *= z
	
	def translate(self, x, y, z):
		translation_matrix = copy_matrix(identity_matrix)

		translation_matrix[3][0] = x
		translation_matrix[3][1] = y
		translation_matrix[3][2] = z

		self.data = multiply_matrices(translation_matrix, self.data)
	
	def rotate(self, angle, x, y, z):
		magnitude = math.sqrt(x * x + y * y + z * z)
		
		x /= magnitude
		y /= magnitude
		z /= magnitude
		
		sin_angle = math.sin(angle)
		cos_angle = math.cos(angle)
		one_minus_cos = 1.0 - cos_angle
		
		rotation_matrix = copy_matrix(clean_matrix)
		
		rotation_matrix[0][0] = one_minus_cos * x * x + cos_angle
		rotation_matrix[0][1] = one_minus_cos * x * y + sin_angle * z
		rotation_matrix[0][2] = one_minus_cos * z * x - sin_angle * y
		
		rotation_matrix[1][0] = one_minus_cos * x * y - sin_angle * z
		rotation_matrix[1][1] = one_minus_cos * y * y + cos_angle
		rotation_matrix[1][2] = one_minus_cos * y * z + sin_angle * x
		
		rotation_matrix[2][0] = one_minus_cos * z * x + sin_angle * y
		rotation_matrix[2][1] = one_minus_cos * y * z - sin_angle * x
		rotation_matrix[2][2] = one_minus_cos * z * z + cos_angle
		
		rotation_matrix[3][3] = 1.0
		self.data = multiply_matrices(rotation_matrix, self.data)
	
	def rotate_2d(self, x, y):
		self.rotate(x, 0, 1.0, 0)
		self.rotate(-y, math.cos(x), 0, math.sin(x))
	
	def frustum(self, left, right, bottom, top, near, far):
		frustum_matrix = copy_matrix(clean_matrix)
		
		frustum_matrix[0][0] = 2 * near / (right - left)
		frustum_matrix[1][1] = 2 * near / (top - bottom)
		
		frustum_matrix[2][0] = (right + left) / (right - left)
		frustum_matrix[2][1] = (top + bottom) / (top - bottom)
		frustum_matrix[2][2] = -(far + near)  / (far - near)
		frustum_matrix[2][3] = -1.0
		
		frustum_matrix[3][2] = -2 * far * near / (far - near)
		
		self.data = multiply_matrices(frustum_matrix, self.data)
	
	def perspective(self, fovy, aspect, near, far):
		frustum_y = near * math.tan(math.radians(fovy) / 2)
		frustum_x = frustum_y * aspect

		self.frustum(-frustum_x, frustum_x, -frustum_y, frustum_y, near, far)
	
	def orthographic(self, left, right, bottom, top, near, far):
		orthographic_matrix = copy_matrix(identity_matrix)
		
		orthographic_matrix[0][0] = 2.0 / (right - left)
		orthographic_matrix[3][0] = -(right + left) / (right - left)
		
		orthographic_matrix[1][1] = 2.0 / (top - bottom)
		orthographic_matrix[3][1] = -(top + bottom) / (top - bottom)
		
		orthographic_matrix[2][2] = 2.0 / (far - near)
		orthographic_matrix[3][2] = -(near + far) / (far - near)
		
		self.data = multiply_matrices(orthographic_matrix, self.data)
