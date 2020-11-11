import ctypes

import pyglet.gl as gl

CHUNK_WIDTH = 16
CHUNK_HEIGHT = 16
CHUNK_LENGTH = 16

class Chunk:
	def __init__(self, world, position):
		self.world = world
		self.position = position
		self.base_position = (self.position[0] * CHUNK_WIDTH, self.position[1] * CHUNK_HEIGHT, self.position[2] * CHUNK_LENGTH)

		self.blocks = []

		# mesh variables

		self.has_mesh = False

		self.mesh_vertex_positions = []
		self.mesh_tex_coords = []
		self.mesh_shading_values = []
		
		self.mesh_index_counter = 0
		self.mesh_indices = []
		
		# create vertex array object

		self.vao = gl.GLuint(0)
		gl.glGenVertexArrays(1, self.vao)
		gl.glBindVertexArray(self.vao)

		# create vertex position vbo

		self.vertex_position_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.vertex_position_vbo)
		
		# create tex coord vbo

		self.tex_coord_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.tex_coord_vbo)

		# create shading values vbo

		self.shading_values_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.shading_values_vbo)

		# create index buffer object

		self.ibo = gl.GLuint(0)
		gl.glGenBuffers(1, self.ibo)
	
	def update_mesh(self):
		self.has_mesh = True

		self.mesh_vertex_positions = []
		self.mesh_tex_coords = []
		self.mesh_shading_values = []

		self.mesh_index_counter = 0
		self.mesh_indices = []

		def add_face(face):
			vertex_positions = block.vertex_positions[face].copy()

			for i in range(4):
				vertex_positions[i * 3 + 0] += x
				vertex_positions[i * 3 + 1] += y
				vertex_positions[i * 3 + 2] += z

			self.mesh_vertex_positions.extend(vertex_positions)

			indices = [0, 1, 2, 0, 2, 3]
			for i in range(6):
				indices[i] += self.mesh_index_counter
			
			self.mesh_indices.extend(indices)
			self.mesh_index_counter += 4

			self.mesh_tex_coords.extend(block.tex_coords[face])
			self.mesh_shading_values.extend(block.shading_values[face])

		for local_x in range(CHUNK_WIDTH):
			for local_y in range(CHUNK_HEIGHT):
				for local_z in range(CHUNK_LENGTH):
					x, y, z = (self.base_position[0] + local_x, self.base_position[1] + local_y, self.base_position[2] + local_z)
					block = self.world.get_block((x, y, z))
					
					if block:
						if not self.world.get_block((x + 1, y, z)): add_face(0)
						if not self.world.get_block((x - 1, y, z)): add_face(1)
						if not self.world.get_block((x, y + 1, z)): add_face(2)
						if not self.world.get_block((x, y - 1, z)): add_face(3)
						if not self.world.get_block((x, y, z + 1)): add_face(4)
						if not self.world.get_block((x, y, z - 1)): add_face(5)

		# pass mesh data to gpu

		gl.glBindVertexArray(self.vao)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_position_vbo)
		gl.glBufferData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.mesh_vertex_positions)),
			(gl.GLfloat * len(self.mesh_vertex_positions)) (*self.mesh_vertex_positions),
			gl.GL_STATIC_DRAW)
		
		gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(0)
		
		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.tex_coord_vbo)
		gl.glBufferData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.mesh_tex_coords)),
			(gl.GLfloat * len(self.mesh_tex_coords)) (*self.mesh_tex_coords),
			gl.GL_STATIC_DRAW)
		
		gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(1)
		
		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.shading_values_vbo)
		gl.glBufferData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.mesh_shading_values)),
			(gl.GLfloat * len(self.mesh_shading_values)) (*self.mesh_shading_values),
			gl.GL_STATIC_DRAW)

		gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(2)
		
		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)
		gl.glBufferData(
			gl.GL_ELEMENT_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLuint * len(self.mesh_indices)),
			(gl.GLuint * len(self.mesh_indices)) (*self.mesh_indices),
			gl.GL_STATIC_DRAW)

	def draw(self):
		gl.glBindVertexArray(self.vao)
		
		gl.glDrawElements(
			gl.GL_TRIANGLES,
			len(self.mesh_indices),
			gl.GL_UNSIGNED_INT,
			None)