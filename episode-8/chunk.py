import ctypes

import pyglet.gl as gl

# define constant values for the chunk's dimensions

CHUNK_WIDTH = 16
CHUNK_HEIGHT = 16
CHUNK_LENGTH = 16


class Chunk:
	def __init__(self, world, chunk_position):
		self.chunk_position = chunk_position

		self.position = (  # get a world-space position for the chunk
			self.chunk_position[0] * CHUNK_WIDTH,
			self.chunk_position[1] * CHUNK_HEIGHT,
			self.chunk_position[2] * CHUNK_LENGTH,
		)

		self.world = world

		self.blocks = [
			[
				[0 for z in range(CHUNK_LENGTH)]  # create an array of blocks filled with "air" (block number 0)
				for y in range(CHUNK_HEIGHT)
			]
			for x in range(CHUNK_WIDTH)
		]

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
		# reset all the mesh-related values

		self.has_mesh = True

		self.mesh_vertex_positions = []
		self.mesh_tex_coords = []
		self.mesh_shading_values = []

		self.mesh_index_counter = 0
		self.mesh_indices = []

		def add_face(face):  # add a face to the chunk mesh
			vertex_positions = block_type.vertex_positions[
				face
			].copy()  # get the vertex positions of the face to be added

			for i in range(4):  # add the world-space position of the face to it's vertex positions
				vertex_positions[i * 3 + 0] += x
				vertex_positions[i * 3 + 1] += y
				vertex_positions[i * 3 + 2] += z

			self.mesh_vertex_positions.extend(
				vertex_positions
			)  # add those vertex positions to the chunk mesh's vertex positions

			indices = [0, 1, 2, 0, 2, 3]  # create a list of indices for the face's vertices
			for i in range(
				6
			):  # shift each index by the chunk mesh's index counter so that no two faces share the same indices
				indices[i] += self.mesh_index_counter

			self.mesh_indices.extend(indices)  # add those indices to the chunk mesh's indices
			self.mesh_index_counter += 4  # add 4 (the amount of vertices in a face) to the chunk mesh's index counter

			self.mesh_tex_coords.extend(
				block_type.tex_coords[face]
			)  # add the face's texture coordinates to the chunk mesh's texture coordinates
			self.mesh_shading_values.extend(
				block_type.shading_values[face]
			)  # add the face's shading values to the chunk mesh's shading values

		# iterate through all local block positions in the chunk

		for local_x in range(CHUNK_WIDTH):
			for local_y in range(CHUNK_HEIGHT):
				for local_z in range(CHUNK_LENGTH):
					block_number = self.blocks[local_x][local_y][
						local_z
					]  # get the block number of the block at that local position

					if block_number:  # check if the block is not air
						block_type = self.world.block_types[block_number]  # get the block type

						x, y, z = (  # get the world-space position of the block
							self.position[0] + local_x,
							self.position[1] + local_y,
							self.position[2] + local_z,
						)

						# check for each block face if it's hidden by another block, and add that face to the chunk mesh if not

						if not self.world.get_block_number((x + 1, y, z)):
							add_face(0)
						if not self.world.get_block_number((x - 1, y, z)):
							add_face(1)
						if not self.world.get_block_number((x, y + 1, z)):
							add_face(2)
						if not self.world.get_block_number((x, y - 1, z)):
							add_face(3)
						if not self.world.get_block_number((x, y, z + 1)):
							add_face(4)
						if not self.world.get_block_number((x, y, z - 1)):
							add_face(5)

		# pass mesh data to gpu

		if not self.mesh_index_counter:  # make sure there actually is data in the mesh
			return

		gl.glBindVertexArray(self.vao)  # bind the VAO

		# pass the mesh data to the vertex position VBO

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_position_vbo)
		gl.glBufferData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.mesh_vertex_positions)),
			(gl.GLfloat * len(self.mesh_vertex_positions))(*self.mesh_vertex_positions),
			gl.GL_STATIC_DRAW,
		)

		gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(0)

		# pass the mesh data to the texture coordinates VBO

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.tex_coord_vbo)
		gl.glBufferData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.mesh_tex_coords)),
			(gl.GLfloat * len(self.mesh_tex_coords))(*self.mesh_tex_coords),
			gl.GL_STATIC_DRAW,
		)

		gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(1)

		# pass the mesh data to the shading values VBO

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.shading_values_vbo)
		gl.glBufferData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.mesh_shading_values)),
			(gl.GLfloat * len(self.mesh_shading_values))(*self.mesh_shading_values),
			gl.GL_STATIC_DRAW,
		)

		gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(2)

		# pass the mesh data to the IBO

		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)
		gl.glBufferData(
			gl.GL_ELEMENT_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLuint * len(self.mesh_indices)),
			(gl.GLuint * len(self.mesh_indices))(*self.mesh_indices),
			gl.GL_STATIC_DRAW,
		)

	def draw(self):
		if not self.mesh_index_counter:  # make sure there actually is data in the mesh
			return

		# draw the VAO

		gl.glBindVertexArray(self.vao)

		gl.glDrawElements(gl.GL_TRIANGLES, len(self.mesh_indices), gl.GL_UNSIGNED_INT, None)
