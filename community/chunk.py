import ctypes
from collections import deque

import pyglet.gl as gl

import subchunk

import options

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

		self.blocks = [[[0 for z in range(CHUNK_LENGTH)]
							for y in range(CHUNK_HEIGHT)]
							for x in range(CHUNK_WIDTH)]
		# Numpy is really slow there
		self.lightmap = [[[0 for z in range(CHUNK_LENGTH)]
							for y in range(CHUNK_HEIGHT)]
							for x in range(CHUNK_WIDTH)]

		self.subchunks = {}
		self.chunk_update_queue = deque()

		for x in range(int(CHUNK_WIDTH / subchunk.SUBCHUNK_WIDTH)):
			for y in range(int(CHUNK_HEIGHT / subchunk.SUBCHUNK_HEIGHT)):
				for z in range(int(CHUNK_LENGTH / subchunk.SUBCHUNK_LENGTH)):
					self.subchunks[(x, y, z)] = subchunk.Subchunk(self, (x, y, z))

		# mesh variables

		self.mesh = []
		self.translucent_mesh = []

		self.mesh_quad_count = 0
		self.translucent_quad_count = 0

		# create VAO and VBO's

		self.vao = gl.GLuint(0)
		gl.glGenVertexArrays(1, self.vao)
		gl.glBindVertexArray(self.vao)

		self.vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.vbo)
		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(gl.GLfloat * CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_LENGTH * 7), None, gl.GL_DYNAMIC_DRAW)

		gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT,
				gl.GL_FALSE, 7 * ctypes.sizeof(gl.GLfloat), 0)
		gl.glEnableVertexAttribArray(0)
		gl.glVertexAttribPointer(1, 1, gl.GL_FLOAT,
				gl.GL_FALSE, 7 * ctypes.sizeof(gl.GLfloat), 3 * ctypes.sizeof(gl.GLfloat))
		gl.glEnableVertexAttribArray(1)
		gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT,
				gl.GL_FALSE, 7 * ctypes.sizeof(gl.GLfloat), 4 * ctypes.sizeof(gl.GLfloat))
		gl.glEnableVertexAttribArray(2)
		gl.glVertexAttribPointer(3, 1, gl.GL_FLOAT,
				gl.GL_FALSE, 7 * ctypes.sizeof(gl.GLfloat), 5 * ctypes.sizeof(gl.GLfloat))
		gl.glEnableVertexAttribArray(3)
		gl.glVertexAttribPointer(4, 1, gl.GL_FLOAT,
				gl.GL_FALSE, 7 * ctypes.sizeof(gl.GLfloat), 6 * ctypes.sizeof(gl.GLfloat))
		gl.glEnableVertexAttribArray(4)



		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, world.ibo)

		if self.world.options.INDIRECT_RENDERING:
			self.indirect_command_buffer = gl.GLuint(0)
			gl.glGenBuffers(1, self.indirect_command_buffer)
			gl.glBindBuffer(gl.GL_DRAW_INDIRECT_BUFFER, self.indirect_command_buffer)
			gl.glBufferData(
				gl.GL_DRAW_INDIRECT_BUFFER,
				ctypes.sizeof(gl.GLuint * 10),
				None,
				gl.GL_DYNAMIC_DRAW
			)

		self.draw_commands = []

		self.occlusion_query = gl.GLuint(0)
		gl.glGenQueries(1, self.occlusion_query)


	def __del__(self):
		gl.glDeleteQueries(1, self.occlusion_query)
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

	def get_block_number(self, position):
		lx, ly, lz = position

		block_number = self.blocks[lx][ly][lz]
		return block_number

	def get_transparency(self, position):
		block_type = self.world.block_types[self.get_block_number(position)]

		if not block_type:
			return 2

		return block_type.transparent

	def is_opaque_block(self, position):
		# get block type and check if it's opaque or not
		# air counts as a transparent block, so test for that too

		block_type = self.world.block_types[self.get_block_number(position)]

		if not block_type:
			return False

		return not block_type.transparent

	def update_subchunk_meshes(self):
		self.chunk_update_queue.clear()
		for subchunk in self.subchunks.values():
			self.chunk_update_queue.append(subchunk)

	def update_at_position(self, position):
		x, y, z = position

		lx = int(x % subchunk.SUBCHUNK_WIDTH )
		ly = int(y % subchunk.SUBCHUNK_HEIGHT)
		lz = int(z % subchunk.SUBCHUNK_LENGTH)

		clx, cly, clz = self.world.get_local_position(position)

		sx = clx // subchunk.SUBCHUNK_WIDTH
		sy = cly // subchunk.SUBCHUNK_HEIGHT
		sz = clz // subchunk.SUBCHUNK_LENGTH

		if self.subchunks[(sx, sy, sz)] not in self.chunk_update_queue:
			self.chunk_update_queue.append(self.subchunks[(sx, sy, sz)])

		def try_update_subchunk_mesh(subchunk_position):
			if subchunk_position in self.subchunks:
				if not self.subchunks[subchunk_position] in self.chunk_update_queue:
					self.chunk_update_queue.append(self.subchunks[subchunk_position])

		if lx == subchunk.SUBCHUNK_WIDTH - 1: try_update_subchunk_mesh((sx + 1, sy, sz))
		if lx == 0: try_update_subchunk_mesh((sx - 1, sy, sz))

		if ly == subchunk.SUBCHUNK_HEIGHT - 1: try_update_subchunk_mesh((sx, sy + 1, sz))
		if ly == 0: try_update_subchunk_mesh((sx, sy - 1, sz))

		if lz == subchunk.SUBCHUNK_LENGTH - 1: try_update_subchunk_mesh((sx, sy, sz + 1))
		if lz == 0: try_update_subchunk_mesh((sx, sy, sz - 1))

	def process_chunk_updates(self):
		for i in range(self.world.options.CHUNK_UPDATES):
			if self.chunk_update_queue:
				subchunk = self.chunk_update_queue.popleft()
				subchunk.update_mesh()
				self.world.chunk_update_counter += 1
				if not self.chunk_update_queue:
					self.world.chunk_building_queue.append(self)
					return

	def update_mesh(self):
		# combine all the small subchunk meshes into one big chunk mesh

		for subchunk in self.subchunks.values():
			self.mesh += subchunk.mesh
			self.translucent_mesh += subchunk.translucent_mesh

		# send the full mesh data to the GPU and free the memory used client-side (we don't need it anymore)
		# don't forget to save the length of 'self.mesh_indices' before freeing

		self.mesh_quad_count = len(self.mesh) // 28 # 28 = 7 (attributes of a vertex) * 4 (number of vertices per quad)
		self.translucent_quad_count = len(self.translucent_mesh) // 28

		self.send_mesh_data_to_gpu()

		self.mesh = []
		self.translucent_mesh = []

	def send_mesh_data_to_gpu(self): # pass mesh data to gpu
		if not self.mesh_quad_count:
			return

		gl.glBindVertexArray(self.vao)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER, # Orphaning
			ctypes.sizeof(gl.GLfloat * CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_LENGTH * 7),
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

		if not self.world.options.INDIRECT_RENDERING:
			return

		self.draw_commands = [
			# Index Count                    Instance Count  Base Index     Base Vertex               Base Instance
			self.mesh_quad_count        * 6,       1,            0,              0,                        0,     # Opaque mesh commands
			self.translucent_quad_count * 6,       1,            0,      self.mesh_quad_count * 4,         0      # Translucent mesh commands
		]

		gl.glBindBuffer(gl.GL_DRAW_INDIRECT_BUFFER, self.indirect_command_buffer)
		gl.glBufferSubData(
			gl.GL_DRAW_INDIRECT_BUFFER,
			0,
			ctypes.sizeof(gl.GLuint * len(self.draw_commands)),
			(gl.GLuint * len(self.draw_commands)) (*self.draw_commands)
		)

	def draw_direct(self, mode):
		if not self.mesh_quad_count:
			return
		gl.glBindVertexArray(self.vao)
		gl.glUniform2i(self.world.block_shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])
		gl.glDrawElements(
			mode,
			self.mesh_quad_count * 6,
			gl.GL_UNSIGNED_INT,
			None,
		)

	def draw_indirect(self, mode):
		if not self.mesh_quad_count:
			return

		gl.glBindVertexArray(self.vao)
		gl.glBindBuffer(gl.GL_DRAW_INDIRECT_BUFFER, self.indirect_command_buffer)
		gl.glUniform2i(self.world.block_shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])

		gl.glDrawElementsIndirect(
			mode,
			gl.GL_UNSIGNED_INT,
			None,
		)

	def draw_direct_advanced(self, mode):
		if not self.mesh_quad_count:
			return

		gl.glBindVertexArray(self.vao)
		gl.glUniform2i(self.world.block_shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])

		gl.glBeginQuery(gl.GL_ANY_SAMPLES_PASSED, self.occlusion_query)
		gl.glDrawElements(
			mode,
			self.mesh_quad_count * 6,
			gl.GL_UNSIGNED_INT,
			None,
		)
		gl.glEndQuery(gl.GL_ANY_SAMPLES_PASSED)


		gl.glBeginConditionalRender(self.occlusion_query, gl.GL_QUERY_BY_REGION_WAIT)
		gl.glDrawElements(
			mode,
			self.mesh_quad_count * 6,
			gl.GL_UNSIGNED_INT,
			None,
		)
		gl.glEndConditionalRender()

	def draw_indirect_advanced(self, mode):
		if not self.mesh_quad_count:
			return

		gl.glBindVertexArray(self.vao)
		gl.glBindBuffer(gl.GL_DRAW_INDIRECT_BUFFER, self.indirect_command_buffer)
		gl.glUniform2i(self.world.block_shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])

		gl.glBeginQuery(gl.GL_ANY_SAMPLES_PASSED, self.occlusion_query)
		gl.glDrawElementsIndirect(
			mode,
			gl.GL_UNSIGNED_INT,
			None,
		)
		gl.glEndQuery(gl.GL_ANY_SAMPLES_PASSED)


		gl.glBeginConditionalRender(self.occlusion_query, gl.GL_QUERY_BY_REGION_WAIT)
		gl.glDrawElementsIndirect(
			mode,
			gl.GL_UNSIGNED_INT,
			None,
		)
		gl.glEndConditionalRender()

	draw_normal = draw_indirect if options.INDIRECT_RENDERING else draw_direct
	draw_advanced = draw_indirect_advanced if options.INDIRECT_RENDERING else draw_direct_advanced
	draw = draw_advanced if options.ADVANCED_OPENGL else draw_normal

	def draw_translucent_direct(self, mode):
		if not self.mesh_quad_count:
			return

		gl.glBindVertexArray(self.vao)
		gl.glUniform2i(self.world.block_shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])

		gl.glDrawElementsBaseVertex(
			mode,
			self.translucent_quad_count * 6,
			gl.GL_UNSIGNED_INT,
			None,
			self.mesh_quad_count * 4
		)

	def draw_translucent_indirect(self, mode):
		if not self.translucent_quad_count:
			return

		gl.glBindVertexArray(self.vao)
		gl.glBindBuffer(gl.GL_DRAW_INDIRECT_BUFFER, self.indirect_command_buffer)
		gl.glUniform2i(self.world.block_shader_chunk_offset_location, self.chunk_position[0], self.chunk_position[2])

		gl.glMemoryBarrier(gl.GL_COMMAND_BARRIER_BIT)

		gl.glDrawElementsIndirect(
			mode,
			gl.GL_UNSIGNED_INT,
			5 * ctypes.sizeof(gl.GLuint)  # offset pointer to the indirect command buffer pointing to the translucent mesh commands
		)

	draw_translucent = draw_translucent_indirect if options.INDIRECT_RENDERING else draw_translucent_direct

