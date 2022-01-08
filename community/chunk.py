import ctypes
import numpy as np

import pyglet.gl as gl

import subchunk 

import options

CHUNK_WIDTH = 16
CHUNK_HEIGHT = 128
CHUNK_LENGTH = 16

class Chunk:
	def __init__(self, world, chunk_position):
		self.world = world
		self.shader_chunk_offset_location = self.world.shader.find_uniform(b"u_ChunkPosition")
		
		self.modified = False
		self.chunk_position = chunk_position

		self.position = (
			self.chunk_position[0] * CHUNK_WIDTH,
			self.chunk_position[1] * CHUNK_HEIGHT,
			self.chunk_position[2] * CHUNK_LENGTH)
		
		self.blocks = [[[0 for z in range(CHUNK_LENGTH)]
							for y in range(CHUNK_HEIGHT)]
							for x in range(CHUNK_WIDTH)]
		# Numpy is really slow there
		self.lightmap = [[[0 for z in range(CHUNK_LENGTH)]
							for y in range(CHUNK_HEIGHT)]
							for x in range(CHUNK_WIDTH)]
		
		self.subchunks = {}
		
		for x in range(int(CHUNK_WIDTH / subchunk.SUBCHUNK_WIDTH)):
			for y in range(int(CHUNK_HEIGHT / subchunk.SUBCHUNK_HEIGHT)):
				for z in range(int(CHUNK_LENGTH / subchunk.SUBCHUNK_LENGTH)):
					self.subchunks[(x, y, z)] = subchunk.Subchunk(self, (x, y, z))

		# mesh variables

		self.mesh = None
		self.translucent_mesh = None

		self.mesh_quad_count = 0
		self.translucent_quad_count = 0

		# create VAO and VBO's

		self.vao = gl.GLuint(0)
		gl.glGenVertexArrays(1, self.vao)
		gl.glBindVertexArray(self.vao)
		
		self.vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.vbo)
		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(gl.GLfloat * CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_LENGTH * 6), None, gl.GL_DYNAMIC_DRAW)

		gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, 
				gl.GL_FALSE, 6 * ctypes.sizeof(gl.GLfloat), 0)
		gl.glEnableVertexAttribArray(0)
		gl.glVertexAttribPointer(1, 1, gl.GL_FLOAT, 
				gl.GL_FALSE, 6 * ctypes.sizeof(gl.GLfloat), 3 * ctypes.sizeof(gl.GLfloat))
		gl.glEnableVertexAttribArray(1)
		gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, 
				gl.GL_FALSE, 6 * ctypes.sizeof(gl.GLfloat), 4 * ctypes.sizeof(gl.GLfloat))
		gl.glEnableVertexAttribArray(2)
		gl.glVertexAttribPointer(3, 1, gl.GL_FLOAT, 
				gl.GL_FALSE, 6 * ctypes.sizeof(gl.GLfloat), 5 * ctypes.sizeof(gl.GLfloat))
		gl.glEnableVertexAttribArray(3)


		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, world.ibo)

	def __del__(self):
		gl.glDeleteBuffers(1, self.vbo)
		gl.glDeleteVertexArrays(1, self.vao)

	def get_block_light(self, position):
		x, y, z = position
		return self.lightmap[x][y][z] & 0xF

	def set_block_light(self, position, value):
		x, y, z = position
		self.lightmap[x][y][z] = (self.lightmap[x][y][z] & 0xF0) | value

	def get_sky_light(self, position):
		x, y, z = position
		return (self.lightmap[x][y][z] >> 4) & 0xF

	def set_sky_light(self, position, value):
		x, y, z = position
		self.lightmap[x][y][z] = (self.lightmap[x][y][z] & 0xF) | (value << 4)

	def get_raw_light(self, position):
		x, y, z = position
		return self.lightmap[x][y][z]

	
	
	def update_subchunk_meshes(self):
		for subchunk in self.subchunks.values():
			subchunk.update_mesh()

	def update_at_position(self, position):
		x, y, z = position

		lx = int(x % subchunk.SUBCHUNK_WIDTH )
		ly = int(y % subchunk.SUBCHUNK_HEIGHT)
		lz = int(z % subchunk.SUBCHUNK_LENGTH)

		clx, cly, clz = self.world.get_local_position(position)

		sx = clx // subchunk.SUBCHUNK_WIDTH
		sy = cly // subchunk.SUBCHUNK_HEIGHT
		sz = clz // subchunk.SUBCHUNK_LENGTH

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
		self.mesh = np.hstack(tuple(subchunk.mesh_array for subchunk in self.subchunks.values()))
		self.translucent_mesh = np.hstack(tuple(subchunk.translucent_mesh_array for subchunk in self.subchunks.values()))

		# send the full mesh data to the GPU and free the memory used client-side (we don't need it anymore)
		# don't forget to save the length of 'self.mesh_indices' before freeing

		self.mesh_quad_count = len(self.mesh) // 24 # 24 = 6 (attributes of a vertex) * 4 (number of vertices per quad)
		self.translucent_quad_count = len(self.translucent_mesh) // 24

		self.send_mesh_data_to_gpu()

	
	def send_mesh_data_to_gpu(self): # pass mesh data to gpu
		if not self.mesh_quad_count:
			return

		gl.glBindVertexArray(self.vao)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER, 
			ctypes.sizeof(gl.GLfloat * CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_LENGTH * 8), 
			None, 
			gl.GL_DYNAMIC_DRAW
		)
		
		gl.glBufferSubData(
			gl.GL_ARRAY_BUFFER,
			0,
			ctypes.sizeof(gl.GLfloat * len(self.mesh)),
			(gl.GLfloat * len(self.mesh)) (*self.mesh)
		)
		gl.glBufferSubData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.mesh)),
			ctypes.sizeof(gl.GLfloat * len(self.translucent_mesh)),
			(gl.GLfloat * len(self.translucent_mesh)) (*self.translucent_mesh)
		)

	def draw(self):
		if not self.mesh_quad_count:
			return

		gl.glBindVertexArray(self.vao)
		gl.glUniform2i(self.shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])

		gl.glDrawElementsBaseVertex(
			gl.GL_TRIANGLES,
			self.mesh_quad_count * 6,
			gl.GL_UNSIGNED_INT,
			None,
			0
		)

	def draw_translucent(self):
		if not self.translucent_quad_count:
			return
		
		gl.glBindVertexArray(self.vao)
		gl.glUniform2i(self.shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])

		gl.glDrawElementsBaseVertex(
			gl.GL_TRIANGLES,
			self.translucent_quad_count * 6,
			gl.GL_UNSIGNED_INT,
			None,
			self.mesh_quad_count * 4
		)
		
