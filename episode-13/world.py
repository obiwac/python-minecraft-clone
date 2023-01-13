import math
import matrix

import save
import chunk
import shader

import block_type
import texture_manager

import entity_type

import pyglet.gl as gl

# import custom block models

import models

class World:
	def __init__(self):
		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.block_types = [None]

		self.entity_types = {}

		# parse block type data file

		with open("data/blocks.mcpy") as f:
			blocks_data = f.readlines()

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

		# parse entity type data file

		with open("data/entities.mcpy") as f:
			entities_data = f.readlines()

		for _entity in entities_data:
			if _entity[0] in "\n#": # skip if empty line or comment
				continue

			name, props = _entity.split(':', 1)

			# default entity

			model = models.pig
			texture = "pig"

			width = 0.6
			height = 1.8

			# read properties

			for prop in props.split(','):
				prop = prop.strip()
				*prop, = filter(None, prop.split(' ', 1))

				if prop[0] == "width":
					width = float(prop[1])

				elif prop[0] == "height":
					height = float(prop[1])

				elif prop[0] == "texture":
					texture = prop[1]

				elif prop[0] == "model":
					model = eval(prop[1])

			# add entity type

			self.entity_types[name] = entity_type.Entity_type(self, name, texture, model, width, height)

		# matrices

		self.mv_matrix  = matrix.Matrix()
		self.p_matrix   = matrix.Matrix()
		self.mvp_matrix = matrix.Matrix()

		# shaders

		self.block_shader = shader.Shader("shaders/block/vert.glsl", "shaders/block/frag.glsl")
		self.block_shader_sampler_location = self.block_shader.find_uniform(b"texture_array_sampler")
		self.block_shader_matrix_location = self.block_shader.find_uniform(b"matrix")

		self.entity_shader = shader.Shader("shaders/entity/vert.glsl", "shaders/entity/frag.glsl")
		self.entity_shader_sampler_location = self.entity_shader.find_uniform(b"texture_sampler")
		self.entity_shader_transform_matrix_location = self.entity_shader.find_uniform(b"transform_matrix")
		self.entity_shader_matrix_location = self.entity_shader.find_uniform(b"matrix")

		# load the world

		self.save = save.Save(self)

		self.chunks = {}
		self.entities = []

		self.save.load()

		for chunk_position in self.chunks:
			self.chunks[chunk_position].update_subchunk_meshes()
			self.chunks[chunk_position].update_mesh()

	def get_chunk_position(self, position):
		x, y, z = position

		return (
			math.floor(x / chunk.CHUNK_WIDTH),
			math.floor(y / chunk.CHUNK_HEIGHT),
			math.floor(z / chunk.CHUNK_LENGTH))

	def get_local_position(self, position):
		x, y, z = position

		return (
			int(x % chunk.CHUNK_WIDTH),
			int(y % chunk.CHUNK_HEIGHT),
			int(z % chunk.CHUNK_LENGTH))

	def get_block_number(self, position):
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

	def try_set_block(self, pos, num, collider):
		# if we're trying to remove a block, whatever let it go through

		if not num:
			return self.set_block(pos, 0)

		# make sure the block doesn't intersect with the passed collider

		for block_collider in self.block_types[num].colliders:
			if collider & (block_collider + pos):
				return

		self.set_block(pos, num)

	def draw(self, player):
		# setup block shader

		self.block_shader.use()
		self.block_shader.uniform_matrix(self.block_shader_matrix_location, self.mvp_matrix)

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_manager.texture_array)
		gl.glUniform1i(self.block_shader_sampler_location, 0)

		# draw chunks

		gl.glEnable(gl.GL_CULL_FACE)

		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()

		# draw entities

		self.entity_shader.use()
		gl.glDisable(gl.GL_CULL_FACE)

		for entity in self.entities:
			dist = math.sqrt(sum(map(lambda x: (x[0] - x[1]) ** 2, zip(entity.position, player.position))))

			if dist > 32:
				continue

			entity.draw()
