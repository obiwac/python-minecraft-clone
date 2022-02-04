import ctypes
import math

import pyglet.gl as gl

import subchunk 

CHUNK_WIDTH = 16
CHUNK_HEIGHT = 128
CHUNK_LENGTH = 16

class Chunk:
	def __init__(self, world, chunk_position):
		self.world = world
		
		self.modified = False
		self.chunk_position = chunk_position

		self.position = (
			self.chunk_position[0] * CHUNK_WIDTH,
			self.chunk_position[1] * CHUNK_HEIGHT,
			self.chunk_position[2] * CHUNK_LENGTH)
		
		self.blocks = [[[0
			for z in range(CHUNK_LENGTH)]
			for y in range(CHUNK_HEIGHT)]
			for x in range(CHUNK_WIDTH )]

		self.subchunks = {}
		
		for x in range(int(CHUNK_WIDTH / subchunk.SUBCHUNK_WIDTH)):
			for y in range(int(CHUNK_HEIGHT / subchunk.SUBCHUNK_HEIGHT)):
				for z in range(int(CHUNK_LENGTH / subchunk.SUBCHUNK_LENGTH)):
					self.subchunks[(x, y, z)] = subchunk.Subchunk(self, (x, y, z))

		# mesh variables

		self.mesh_vertex_positions = []
		self.mesh_tex_coords = []
		self.mesh_shading_values = []

		self.mesh_index_counter = 0
		self.mesh_indices = []

		# create VAO and VBO's

		self.vao = gl.GLuint(0)
		gl.glGenVertexArrays(1, self.vao)
		gl.glBindVertexArray(self.vao)

		self.vertex_position_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.vertex_position_vbo)

		self.tex_coord_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.tex_coord_vbo)

		self.shading_values_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.shading_values_vbo)

		self.ibo = gl.GLuint(0)
		gl.glGenBuffers(1, self.ibo)
	
	def update_subchunk_meshes(self):
		for subchunk_position in self.subchunks:
			subchunk = self.subchunks[subchunk_position]
			subchunk.update_mesh()

	def update_at_position(self, position):
		x, y, z = position

		lx = int(x % subchunk.SUBCHUNK_WIDTH )
		ly = int(y % subchunk.SUBCHUNK_HEIGHT)
		lz = int(z % subchunk.SUBCHUNK_LENGTH)

		clx, cly, clz = self.world.get_local_position(position)

		sx = math.floor(clx / subchunk.SUBCHUNK_WIDTH)
		sy = math.floor(cly / subchunk.SUBCHUNK_HEIGHT)
		sz = math.floor(clz / subchunk.SUBCHUNK_LENGTH)

		self.subchunks[(sx, sy, sz)].update_mesh()

		def try_update_subchunk_mesh(subchunk_position):
			if subchunk_position in self.subchunks:
				self.subchunks[subchunk_position].update_mesh()

		if lx == subchunk.SUBCHUNK_WIDTH - 1: try_update_subchunk_mesh((sx + 1, sy, sz))
		if lx == 0: try_update_subchunk_mesh((sx - 1, sy, sz))

		if ly == subchunk.SUBCHUNK_HEIGHT - 1: try_update_subchunk_mesh((sx, sy + 1, sz))
		if ly == 0: try_update_subchunk_mesh((sx, sy - 1, sz))

		if lz == subchunk.SUBCHUNK_LENGTH - 1: try_update_subchunk_mesh((sx, sy, sz + 1))
		if lz == 0: try_update_subchunk_mesh((sx, sy, sz - 1))

	def update_mesh(self):
		# combine all the small subchunk meshes into one big chunk mesh

		self.mesh_vertex_positions = []
		self.mesh_tex_coords = []
		self.mesh_shading_values = []

		self.mesh_index_counter = 0
		self.mesh_indices = []

		for subchunk_position in self.subchunks:
			subchunk = self.subchunks[subchunk_position]

			self.mesh_vertex_positions.extend(subchunk.mesh_vertex_positions)
			self.mesh_tex_coords.extend(subchunk.mesh_tex_coords)
			self.mesh_shading_values.extend(subchunk.mesh_shading_values)

			mesh_indices = [index + self.mesh_index_counter for index in subchunk.mesh_indices]
			
			self.mesh_indices.extend(mesh_indices)
			self.mesh_index_counter += subchunk.mesh_index_counter
		
		# send the full mesh data to the GPU and free the memory used client-side (we don't need it anymore)
		# don't forget to save the length of 'self.mesh_indices' before freeing

		self.mesh_indices_length = len(self.mesh_indices)
		self.send_mesh_data_to_gpu()
		
		del self.mesh_vertex_positions
		del self.mesh_tex_coords
		del self.mesh_shading_values

		del self.mesh_indices
	
	def send_mesh_data_to_gpu(self): # pass mesh data to gpu
		if not self.mesh_index_counter:
			return

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
			ctypes.sizeof(gl.GLuint * self.mesh_indices_length),
			(gl.GLuint * self.mesh_indices_length) (*self.mesh_indices),
			gl.GL_STATIC_DRAW)

	def draw(self):
		if not self.mesh_index_counter:
			return
		
		gl.glBindVertexArray(self.vao)

		gl.glDrawElements(
			gl.GL_TRIANGLES,
			self.mesh_indices_length,
			gl.GL_UNSIGNED_INT,
			None)