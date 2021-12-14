import chunk
import ctypes
import math


import pyglet.gl as gl

import block_type
import models
import save
import texture_manager
import options
# import custom block models


class World:
	def __init__(self, camera):
		self.camera = camera
		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.block_types = [None]

		# parse block type data file

		blocks_data_file = open("data/blocks.mcpy")
		blocks_data = blocks_data_file.readlines()
		blocks_data_file.close()

		for block in blocks_data:
			if block[0] in ['\n', '#']: # skip if empty line or comment
				continue
			
			number, props = block.split(':', 1)
			number = int(number)

			# default block

			name = "Unknown"
			model = models.cube
			texture = {"all": "unknown"}

			# read properties

			for prop in props.split(','):
				prop = prop.strip()
				prop = list(filter(None, prop.split(' ', 1)))

				if prop[0] == "sameas":
					sameas_number = int(prop[1])

					name = self.block_types[sameas_number].name
					texture = self.block_types[sameas_number].block_face_textures
					model = self.block_types[sameas_number].model
				
				elif prop[0] == "name":
					name = eval(prop[1])
				
				elif prop[0][:7] == "texture":
					_, side = prop[0].split('.')
					texture[side] = prop[1].strip()

				elif prop[0] == "model":
					model = eval(prop[1])
			
			# add block type

			_block_type = block_type.Block_type(self.texture_manager, name, texture, model)

			if number < len(self.block_types):
				self.block_types[number] = _block_type
			
			else:
				self.block_types.append(_block_type)

		self.texture_manager.generate_mipmaps()

		chunk_indices = []

		for nquad in range(chunk.CHUNK_WIDTH * chunk.CHUNK_HEIGHT * chunk.CHUNK_LENGTH * 8):
			chunk_indices.append(4 * nquad + 0)
			chunk_indices.append(4 * nquad + 1)
			chunk_indices.append(4 * nquad + 2)
			chunk_indices.append(4 * nquad + 0)
			chunk_indices.append(4 * nquad + 2)
			chunk_indices.append(4 * nquad + 3)

		self.ibo = gl.GLuint(0)
		gl.glGenBuffers(1, ctypes.byref(self.ibo))
		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)
		gl.glBufferData(
			gl.GL_ELEMENT_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLuint * len(chunk_indices)),
			(gl.GLuint * len(chunk_indices))(*chunk_indices),
			gl.GL_STATIC_DRAW)
		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

		

		# load the world

		self.save = save.Save(self)

		self.chunks = {}
		self.save.load()
		
		for chunk_position in self.chunks:
			self.chunks[chunk_position].update_subchunk_meshes()
			self.chunks[chunk_position].update_mesh()

		del chunk_indices

	def __del__(self):
		gl.glDeleteBuffers(1, ctypes.byref(self.ibo))
	
	def get_chunk_position(self, position):
		x, y, z = position

		return (
			(x // chunk.CHUNK_WIDTH),
			(y // chunk.CHUNK_HEIGHT),
			(z // chunk.CHUNK_LENGTH))

	def get_local_position(self, position):
		x, y, z = position
		
		return (
			int(x % chunk.CHUNK_WIDTH),
			int(y % chunk.CHUNK_HEIGHT),
			int(z % chunk.CHUNK_LENGTH))

	def get_block_number(self, position):
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if not chunk_position in self.chunks:
			return 0
		
		lx, ly, lz = self.get_local_position(position)

		block_number = self.chunks[chunk_position].blocks[lx][ly][lz]
		return block_number

	def is_opaque_block(self, position):
		# get block type and check if it's opaque or not
		# air counts as a transparent block, so test for that too
		
		block_type = self.block_types[self.get_block_number(position)]

		if not block_type:
			return False
		
		return not block_type.transparent

	def set_block(self, position, number): # set number to 0 (air) to remove block
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if not chunk_position in self.chunks: # if no chunks exist at this position, create a new one
			if number == 0:
				return # no point in creating a whole new chunk if we're not gonna be adding anything

			self.chunks[chunk_position] = chunk.Chunk(self, chunk_position)
		
		if self.get_block_number(position) == number: # no point updating mesh if the block is the same
			return
		
		lx, ly, lz = self.get_local_position(position)

		self.chunks[chunk_position].blocks[lx][ly][lz] = number
		self.chunks[chunk_position].modified = True

		self.chunks[chunk_position].update_at_position((x, y, z))
		self.chunks[chunk_position].update_mesh()

		cx, cy, cz = chunk_position

		def try_update_chunk_at_position(chunk_position, position):
			if chunk_position in self.chunks:
				self.chunks[chunk_position].update_at_position(position)
				self.chunks[chunk_position].update_mesh()
		
		if lx == chunk.CHUNK_WIDTH - 1: try_update_chunk_at_position((cx + 1, cy, cz), (x + 1, y, z))
		if lx == 0: try_update_chunk_at_position((cx - 1, cy, cz), (x - 1, y, z))

		if ly == chunk.CHUNK_HEIGHT - 1: try_update_chunk_at_position((cx, cy + 1, cz), (x, y + 1, z))
		if ly == 0: try_update_chunk_at_position((cx, cy - 1, cz), (x, y - 1, z))

		if lz == chunk.CHUNK_LENGTH - 1: try_update_chunk_at_position((cx, cy, cz + 1), (x, y, z + 1))
		if lz == 0: try_update_chunk_at_position((cx, cy, cz - 1), (x, y, z - 1))
	
	def can_render_chunk(self, chunk_position, pl_c_pos):
		rx, ry, rz = (chunk_position[0] - pl_c_pos[0]) \
					* math.cos(self.camera.rotation[0]) \
					* math.cos(self.camera.rotation[1]) , \
				(chunk_position[1] - pl_c_pos[1]) \
					* math.sin(self.camera.rotation[1]) , \
				(chunk_position[2] - pl_c_pos[2]) \
					* math.sin(self.camera.rotation[0]) \
					* math.cos(self.camera.rotation[1])
		return rx >= -1 and ry >= -1 and rz >= -1 
	
	def draw_translucent_fast(self, player_chunk_pos):
		gl.glDisable(gl.GL_CULL_FACE)
		gl.glEnable(gl.GL_BLEND)
		gl.glDepthMask(gl.GL_FALSE)

		for chunk_position in self.chunks:
			if self.can_render_chunk(chunk_position, player_chunk_pos):
				self.chunks[chunk_position].draw_translucent()

		gl.glDepthMask(gl.GL_TRUE)
		gl.glDisable(gl.GL_BLEND)
		gl.glEnable(gl.GL_CULL_FACE)
		
	def draw_translucent_fancy(self, player_chunk_pos):
		gl.glDepthMask(gl.GL_FALSE)
		gl.glFrontFace(gl.GL_CW)
		gl.glEnable(gl.GL_BLEND)

		for chunk_position in self.chunks:
			if self.can_render_chunk(chunk_position, player_chunk_pos):
				self.chunks[chunk_position].draw_translucent()
		
		gl.glFrontFace(gl.GL_CCW)
		gl.glEnable(gl.GL_BLEND)
		
		for chunk_position in self.chunks:
			if self.can_render_chunk(chunk_position, player_chunk_pos):
				self.chunks[chunk_position].draw_translucent()

		gl.glDisable(gl.GL_BLEND)
		gl.glDepthMask(gl.GL_TRUE)

	draw_translucent = draw_translucent_fancy if options.TRANSLUCENT_BLENDING else draw_translucent_fast
	
	def draw(self):
		player_floored_pos = tuple(self.camera.position)
		player_chunk_pos = self.get_chunk_position(player_floored_pos)

		for chunk_position in self.chunks:
			if self.can_render_chunk(chunk_position, player_chunk_pos):
				self.chunks[chunk_position].draw()

		self.draw_translucent(player_chunk_pos)

	
		
