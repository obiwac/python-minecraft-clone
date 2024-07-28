import ctypes
import array
import math

import pyglet.gl as gl

from libc.stdlib cimport malloc, free
from libc.stdint cimport uint8_t
from src.chunk cimport CChunk, CSubchunk
from src.chunk import CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_LENGTH
from src.chunk import SUBCHUNK_WIDTH, SUBCHUNK_HEIGHT, SUBCHUNK_LENGTH

# define these first because subchunk depends on them

import src.chunk.subchunk as subchunk

cdef send_mesh_data_to_gpu(self): # pass mesh data to gpu
	cdef CChunk c = self.c

	if not c.index_count:
		return

	gl.glBindVertexArray(self.vao)

	gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
	gl.glBufferData(
		gl.GL_ARRAY_BUFFER,
		c.data_count * sizeof(c.data[0]),
		ctypes.cast(<size_t>c.data, ctypes.POINTER(gl.GLfloat)),
		gl.GL_STATIC_DRAW)

	f = ctypes.sizeof(gl.GLfloat)
	
	gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 7 * f, 0 * f)
	gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 7 * f, 3 * f)
	gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, gl.GL_FALSE, 7 * f, 6 * f)

	gl.glEnableVertexAttribArray(0)
	gl.glEnableVertexAttribArray(1)
	gl.glEnableVertexAttribArray(2)

	gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)
	gl.glBufferData(
		gl.GL_ELEMENT_ARRAY_BUFFER,
		c.index_count * sizeof(c.indices[0]),
		ctypes.cast(<size_t>c.indices, ctypes.POINTER(gl.GLuint)),
		gl.GL_STATIC_DRAW)

cdef update_mesh(self):
	cdef CChunk c = self.c

	# combine all the small subchunk meshes into one big chunk mesh

	cdef int target_data_count = 0
	cdef int target_index_count = 0

	cdef CSubchunk subchunk_c

	for subchunk in self.subchunks.values():
		subchunk_c = subchunk.c

		target_data_count += subchunk_c.data_count
		target_index_count += subchunk_c.index_count

	c.data_count = 0
	c.data = <float*>malloc(target_data_count * sizeof(c.data[0]))

	c.index_count = 0
	c.indices = <int*>malloc(target_index_count * sizeof(c.indices[0]))

	cdef size_t i

	for subchunk_position in self.subchunks:
		subchunk = self.subchunks[subchunk_position]
		subchunk_c = subchunk.c

		c.data[c.data_count: c.data_count + subchunk_c.data_count] = subchunk_c.data
		c.data_count += subchunk_c.data_count

		for i in range(subchunk_c.index_count):
			c.indices[c.index_count + i] = subchunk_c.indices[i] + c.index_count // 6 * 4

		c.index_count += subchunk_c.index_count

	# send the full mesh data to the GPU and free the memory used client-side (we don't need it anymore)
	# don't forget to save the length of 'self.mesh_indices' before freeing

	send_mesh_data_to_gpu(self)

	free(c.data)
	free(c.indices)

class Chunk:
	def __init__(self, world, chunk_position):
		self.world = world
		
		self.modified = False
		self.chunk_position = chunk_position

		self.position = (
			self.chunk_position[0] * CHUNK_WIDTH,
			self.chunk_position[1] * CHUNK_HEIGHT,
			self.chunk_position[2] * CHUNK_LENGTH)
		
		self.subchunks = {}
		
		for x in range(int(CHUNK_WIDTH / SUBCHUNK_WIDTH)):
			for y in range(int(CHUNK_HEIGHT / SUBCHUNK_HEIGHT)):
				for z in range(int(CHUNK_LENGTH / SUBCHUNK_LENGTH)):
					self.subchunks[(x, y, z)] = subchunk.Subchunk(self, (x, y, z))

		self.c = CChunk()

		# create VAO, VBO, and IBO

		self.vao = gl.GLuint(0)
		gl.glGenVertexArrays(1, self.vao)
		gl.glBindVertexArray(self.vao)

		self.vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.vbo)

		self.ibo = gl.GLuint(0)
		gl.glGenBuffers(1, self.ibo)

	@property
	def loaded(self):
		return self.c.index_count > 0

	def get_block(self, x, y, z):
		return self.c.get_blocks(
			x * CHUNK_LENGTH * CHUNK_HEIGHT +
			z * CHUNK_HEIGHT +
			y)

	def set_block(self, x, y, z, block):
		self.c.set_blocks(
			x * CHUNK_LENGTH * CHUNK_HEIGHT +
			z * CHUNK_HEIGHT +
			y, block)

	def copy_blocks(self, blocks):
		self.c.copy_blocks(blocks)

	def update_subchunk_meshes(self):
		for subchunk_position in self.subchunks:
			subchunk = self.subchunks[subchunk_position]
			subchunk.update_mesh()

	def update_at_position(self, position):
		x, y, z = position

		lx = int(x % SUBCHUNK_WIDTH )
		ly = int(y % SUBCHUNK_HEIGHT)
		lz = int(z % SUBCHUNK_LENGTH)

		clx, cly, clz = self.world.get_local_position(position)

		sx = math.floor(clx / SUBCHUNK_WIDTH)
		sy = math.floor(cly / SUBCHUNK_HEIGHT)
		sz = math.floor(clz / SUBCHUNK_LENGTH)

		self.subchunks[(sx, sy, sz)].update_mesh()

		def try_update_subchunk_mesh(subchunk_position):
			if subchunk_position in self.subchunks:
				self.subchunks[subchunk_position].update_mesh()

		if lx == SUBCHUNK_WIDTH - 1: try_update_subchunk_mesh((sx + 1, sy, sz))
		if lx == 0: try_update_subchunk_mesh((sx - 1, sy, sz))

		if ly == SUBCHUNK_HEIGHT - 1: try_update_subchunk_mesh((sx, sy + 1, sz))
		if ly == 0: try_update_subchunk_mesh((sx, sy - 1, sz))

		if lz == SUBCHUNK_LENGTH - 1: try_update_subchunk_mesh((sx, sy, sz + 1))
		if lz == 0: try_update_subchunk_mesh((sx, sy, sz - 1))

	def update_mesh(self):
		update_mesh(self)

	def draw(self):
		if not self.loaded:
			return
		
		gl.glBindVertexArray(self.vao)

		gl.glDrawElements(
			gl.GL_TRIANGLES,
			self.c.index_count,
			gl.GL_UNSIGNED_INT,
			None)
