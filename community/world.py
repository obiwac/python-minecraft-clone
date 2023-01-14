import chunk
import ctypes
import math
import logging
import glm
import options

from functools import cmp_to_key
from collections import deque

import pyglet.gl as gl

import block_type
import entity_type

import models

import shader
import save

from util import DIRECTIONS

def get_chunk_position(position):
	x, y, z = position

	return glm.ivec3(
		(x // chunk.CHUNK_WIDTH),
		(y // chunk.CHUNK_HEIGHT),
		(z // chunk.CHUNK_LENGTH))

def get_local_position(position):
	x, y, z = position

	return glm.ivec3(
		int(x % chunk.CHUNK_WIDTH),
		int(y % chunk.CHUNK_HEIGHT),
		int(z % chunk.CHUNK_LENGTH))

class World:
	def __init__(self, player, texture_manager, options):
		self.options = options
		self.player = player
		self.texture_manager = texture_manager
		self.block_types = [None]
		self.entity_types = {}

		self.daylight = 1800
		self.incrementer = 0
		self.time = 0
		
		# Compat
		self.get_chunk_position = get_chunk_position
		self.get_local_position = get_local_position

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

		self.light_blocks = [10, 11, 50, 51, 62, 75]

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

		gl.glBindVertexArray(0)
		
		indices = []

		for nquad in range(chunk.CHUNK_WIDTH * chunk.CHUNK_HEIGHT * chunk.CHUNK_LENGTH * 8):
			indices.append(4 * nquad + 0)
			indices.append(4 * nquad + 1)
			indices.append(4 * nquad + 2)
			indices.append(4 * nquad + 2)
			indices.append(4 * nquad + 3)
			indices.append(4 * nquad + 0)

		gl.glBindVertexArray(0)

		self.ibo = gl.GLuint(0)
		gl.glGenBuffers(1, self.ibo)
		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)
		gl.glBufferData(
			gl.GL_ELEMENT_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLuint * len(indices)),
			(gl.GLuint * len(indices))(*indices),
			gl.GL_STATIC_DRAW)
		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

		logging.debug("Created Shared Index Buffer")

		# matrices

		self.mv_matrix  = glm.mat4()
		self.p_matrix   = glm.mat4()
		self.mvp_matrix = glm.mat4()

		# shaders

		lighting_shader = "alpha_lighting"

		if options.COLORED_LIGHTING:
			lighting_shader = "colored_lighting"

		self.block_shader = shader.Shader(f"shaders/{lighting_shader}/vert.glsl", f"shaders/{lighting_shader}/frag.glsl")
		self.block_shader_sampler_location = self.block_shader.find_uniform(b"u_TextureArraySampler")
		self.block_shader_matrix_location = self.block_shader.find_uniform(b"u_MVPMatrix")
		self.block_shader_daylight_location = self.block_shader.find_uniform(b"u_Daylight")
		self.block_shader_chunk_offset_location = self.block_shader.find_uniform(b"u_ChunkPosition")

		self.entity_shader = shader.Shader("shaders/entity/vert.glsl", "shaders/entity/frag.glsl")
		self.entity_shader_sampler_location = self.entity_shader.find_uniform(b"texture_sampler")
		self.entity_shader_inverse_transform_matrix_location = self.entity_shader.find_uniform(b"inverse_transform_matrix")
		self.entity_shader_matrix_location = self.entity_shader.find_uniform(b"matrix")
		self.entity_shader_lighting_location = self.entity_shader.find_uniform(b"lighting")

		# load the world

		self.save = save.Save(self)

		self.chunks = {}
		self.sorted_chunks = []

		self.entities = []

		# light update queue

		self.light_increase_queue = deque() # Node: World Position, light
		self.light_decrease_queue = deque() # Node: World position, light
		self.skylight_increase_queue = deque()
		self.skylight_decrease_queue = deque()
		self.chunk_building_queue = deque()

		self.save.load()

		logging.info("Lighting chunks")
		for world_chunk in self.chunks.values():
			self.init_skylight(world_chunk)

		logging.info("Generating chunks")
		for world_chunk in self.chunks.values():
			world_chunk.update_subchunk_meshes()

		del indices
		self.visible_chunks = []

		# Debug variables

		self.pending_chunk_update_count = 0
		self.chunk_update_counter = 0
		self.visible_entities = 0

	def __del__(self):
		gl.glDeleteBuffers(1, ctypes.byref(self.ibo))

	################ LIGHTING ENGINE ################

	def increase_light(self, world_pos, newlight, light_update=True):
		chunk = self.chunks[get_chunk_position(world_pos)]
		local_pos = get_local_position(world_pos)

		chunk.set_block_light(local_pos, newlight)

		self.light_increase_queue.append((world_pos, newlight))

		self.propagate_increase(light_update)

	def propagate_increase(self, light_update):
		"""Starts propagating all queued block light increases
		This algorithm is derived from the Seed of Andromeda's tutorial
		It uses a FIFO queue to queue the pending blocks to light
		It then checks its 6 neighbours and propagate light to one of them if the latter's light level
		is lower than the former one"""

		while self.light_increase_queue:
			pos, light_level = self.light_increase_queue.popleft()

			for direction in DIRECTIONS:
				neighbour_pos = pos + direction

				chunk = self.chunks.get(get_chunk_position(neighbour_pos), None)
				if not chunk: continue
				local_pos = get_local_position(neighbour_pos)

				if not self.is_opaque_block(neighbour_pos) and chunk.get_block_light(local_pos) + 2 <= light_level:
					chunk.set_block_light(local_pos, light_level - 1)

					self.light_increase_queue.append((neighbour_pos, light_level - 1))

					if light_update:
						chunk.update_at_position(neighbour_pos)

	def init_skylight(self, pending_chunk):
		"""Initializes the skylight of each chunks
		To avoid unsufferable lag from propagating from the top of the chunks when
		most of the heights would be air, it instead runs a simple algorithm
		to check where the highest point of the chunk is and propagates skylight from
		this height"""

		chunk_pos = pending_chunk.chunk_position

		# Retrieve the highest chunk point
		height = 0
		for lx in range(chunk.CHUNK_WIDTH):
			for lz in range(chunk.CHUNK_LENGTH):
				for ly in range(chunk.CHUNK_HEIGHT-1, -1, -1):
					if pending_chunk.blocks[lx][ly][lz]:
						break
				if ly > height:
					height = ly

		# Initialize skylight to 15 until that point and then queue a skylight propagation increase
		for lx in range(chunk.CHUNK_WIDTH):
			for lz in range(chunk.CHUNK_LENGTH):
				for ly in range(chunk.CHUNK_HEIGHT - 1, height, -1):
					pending_chunk.set_sky_light(glm.ivec3(lx, ly, lz), 15)

				pos = glm.ivec3(chunk.CHUNK_WIDTH * chunk_pos[0] + lx,
						ly,
						chunk.CHUNK_LENGTH * chunk_pos[2] + lz
				)
				self.skylight_increase_queue.append((pos, 15))

		self.propagate_skylight_increase(False)

	def propagate_skylight_increase(self, light_update):
		"""Similar to the block light algorithm, but
		do not lower the light level in the downward direction"""
		while self.skylight_increase_queue:
			pos, light_level = self.skylight_increase_queue.popleft()

			for direction in DIRECTIONS:
				neighbour_pos = pos + direction
				if neighbour_pos.y > chunk.CHUNK_HEIGHT:
					continue

				_chunk = self.chunks.get(get_chunk_position(neighbour_pos), None)
				if not _chunk: continue
				local_pos = get_local_position(neighbour_pos)

				transparency = self.get_transparency(neighbour_pos)

				if transparency and _chunk.get_sky_light(local_pos) < light_level:
					newlight = light_level - (2 - transparency)

					if light_update:
						_chunk.update_at_position(neighbour_pos)

					if direction.y == -1:
						_chunk.set_sky_light(local_pos, newlight)
						self.skylight_increase_queue.append((neighbour_pos, newlight))
					elif _chunk.get_sky_light(local_pos) + 2 <= light_level:
						_chunk.set_sky_light(local_pos, newlight - 1)
						self.skylight_increase_queue.append((neighbour_pos, newlight - 1))

	def decrease_light(self, world_pos):
		chunk = self.chunks[get_chunk_position(world_pos)]
		local_pos = get_local_position(world_pos)
		old_light = chunk.get_block_light(local_pos)
		chunk.set_block_light(local_pos, 0)
		self.light_decrease_queue.append((world_pos, old_light))

		self.propagate_decrease(True)
		self.propagate_increase(True)

	def propagate_decrease(self, light_update):
		"""Starts propagating all queued block light decreases
		This algorithm is derived from the Seed of Andromeda's tutorial
		It uses a FIFO queue to queue the pending blocks to unlight
		It then checks its 6 neighbours and unlight to one of them if the latter's light level
		is lower than the former one"""

		while self.light_decrease_queue:
			pos, light_level = self.light_decrease_queue.popleft()

			for direction in DIRECTIONS:
				neighbour_pos = pos + direction

				chunk = self.chunks.get(get_chunk_position(neighbour_pos), None)
				if not chunk: continue
				local_pos = get_local_position(neighbour_pos)

				if self.get_block_number(neighbour_pos) in self.light_blocks:
					self.light_increase_queue.append((neighbour_pos, 15))
					continue

				if not self.is_opaque_block(neighbour_pos):
					neighbour_level = chunk.get_block_light(local_pos)
					if not neighbour_level: continue

					if neighbour_level < light_level:
						chunk.set_block_light(local_pos, 0)
						if light_update:
							chunk.update_at_position(neighbour_pos)
						self.light_decrease_queue.append((neighbour_pos, neighbour_level))
					elif neighbour_level >= light_level:
						self.light_increase_queue.append((neighbour_pos, neighbour_level))

	def decrease_skylight(self, world_pos, light_update=True):
		chunk = self.chunks[get_chunk_position(world_pos)]
		local_pos = get_local_position(world_pos)
		old_light = chunk.get_sky_light(local_pos)
		chunk.set_sky_light(local_pos, 0)
		self.skylight_decrease_queue.append((world_pos, old_light))

		self.propagate_skylight_decrease(light_update)
		self.propagate_skylight_increase(light_update)

	def propagate_skylight_decrease(self, light_update=True):
		"""Similar to the block light algorithm, but
		always unlight in the downward direction"""

		while self.skylight_decrease_queue:
			pos, light_level = self.skylight_decrease_queue.popleft()

			for direction in DIRECTIONS:
				neighbour_pos = pos + direction

				chunk = self.chunks.get(get_chunk_position(neighbour_pos), None)
				if not chunk: continue
				local_pos = get_local_position(neighbour_pos)

				if self.get_transparency(neighbour_pos):
					neighbour_level = chunk.get_sky_light(local_pos)
					if not neighbour_level: continue

					if direction.y == -1 or neighbour_level < light_level:
						chunk.set_sky_light(local_pos, 0)
						if light_update:
							chunk.update_at_position(neighbour_pos)
						self.skylight_decrease_queue.append((neighbour_pos, neighbour_level))
					elif neighbour_level >= light_level:
						self.skylight_increase_queue.append((neighbour_pos, neighbour_level))

	# Getters and setters

	def get_raw_light(self, position):
		chunk = self.chunks.get(get_chunk_position(position), None)
		if not chunk:
			return 15 << 4
		local_position = self.get_local_position(position)
		return chunk.get_raw_light(local_position)

	def get_light(self, position):
		chunk = self.chunks.get(get_chunk_position(position), None)
		if not chunk:
			return 0
		local_position = self.get_local_position(position)
		return chunk.get_block_light(local_position)

	def get_skylight(self, position):
		chunk = self.chunks.get(get_chunk_position(position), None)
		if not chunk:
			return 15
		local_position = self.get_local_position(position)
		return chunk.get_sky_light(local_position)

	def set_light(self, position, light):
		chunk = self.chunks.get(get_chunk_position(position), None)
		local_position = get_local_position(position)
		chunk.set_block_light(local_position, light)

	def set_skylight(self, position, light):
		chunk = self.chunks.get(get_chunk_position(position), None)
		local_position = get_local_position(position)
		chunk.set_sky_light(local_position, light)

	#################################################

	def get_block_number(self, position):
		chunk_position = get_chunk_position(position)

		if not chunk_position in self.chunks:
			return 0

		lx, ly, lz = get_local_position(position)

		block_number = self.chunks[chunk_position].blocks[lx][ly][lz]
		return block_number

	def get_transparency(self, position):
		block_type = self.block_types[self.get_block_number(position)]

		if not block_type:
			return 2

		return block_type.transparency

	def is_opaque_block(self, position):
		# get block type and check if it's opaque or not
		# air counts as a transparent block, so test for that too

		block_type = self.block_types[self.get_block_number(position)]

		if not block_type:
			return False

		return not block_type.transparent

	def create_chunk(self, chunk_position):
		self.chunks[chunk_position] = chunk.Chunk(self, chunk_position)
		self.init_skylight(self.chunks[chunk_position])

	def set_block(self, position, number): # set number to 0 (air) to remove block
		x, y, z = position
		chunk_position = get_chunk_position(position)

		if not chunk_position in self.chunks: # if no chunks exist at this position, create a new one
			if number == 0:
				return # no point in creating a whole new chunk if we're not gonna be adding anything

			self.create_chunk(chunk_position)


		if self.get_block_number(position) == number: # no point updating mesh if the block is the same
			return

		lx, ly, lz = get_local_position(position)

		self.chunks[chunk_position].blocks[lx][ly][lz] = number
		self.chunks[chunk_position].modified = True

		self.chunks[chunk_position].update_at_position((x, y, z))

		if number:
			if number in self.light_blocks:
				self.increase_light(position, 15)

			elif self.block_types[number].transparent != 2:
				self.decrease_light(position)
				self.decrease_skylight(position)

		elif not number:
			self.decrease_light(position)
			self.decrease_skylight(position)

		cx, cy, cz = chunk_position

		def try_update_chunk_at_position(chunk_position, position):
			if chunk_position in self.chunks:
				self.chunks[chunk_position].update_at_position(position)

		if lx == chunk.CHUNK_WIDTH - 1: try_update_chunk_at_position(glm.ivec3(cx + 1, cy, cz), (x + 1, y, z))
		if lx == 0: try_update_chunk_at_position(glm.ivec3(cx - 1, cy, cz), (x - 1, y, z))

		if ly == chunk.CHUNK_HEIGHT - 1: try_update_chunk_at_position(glm.ivec3(cx, cy + 1, cz), (x, y + 1, z))
		if ly == 0: try_update_chunk_at_position(glm.ivec3(cx, cy - 1, cz), (x, y - 1, z))

		if lz == chunk.CHUNK_LENGTH - 1: try_update_chunk_at_position(glm.ivec3(cx, cy, cz + 1), (x, y, z + 1))
		if lz == 0: try_update_chunk_at_position(glm.ivec3(cx, cy, cz - 1), (x, y, z - 1))

	def try_set_block(self, position, number, collider):
		# if we're trying to remove a block, whatever let it go through

		if not number:
			return self.set_block(position, 0)

		# make sure the block doesn't intersect with the passed collider

		for block_collider in self.block_types[number].colliders:
			if collider & (block_collider + position):
				return

		self.set_block(position, number)

	def toggle_AO(self):
		self.options.SMOOTH_LIGHTING = not self.options.SMOOTH_LIGHTING
		for chunk in self.chunks.values():
			chunk.update_subchunk_meshes()

	def speed_daytime(self):
		if self.daylight <= 480:
			self.incrementer = 1
		if self.daylight >= 1800:
			self.incrementer = -1

	def can_render_chunk(self, chunk_position):
		return self.player.check_chunk_in_frustum(chunk_position) and math.dist(self.get_chunk_position(self.player.position), chunk_position) <= self.options.RENDER_DISTANCE

	def prepare_rendering(self):
		self.visible_chunks = [self.chunks[chunk_position]
				for chunk_position in self.chunks if self.can_render_chunk(chunk_position)]
		self.sort_chunks()

	def sort_chunks(self):
		player_chunk_pos = self.get_chunk_position(self.player.position)
		self.visible_chunks.sort(key = cmp_to_key(lambda a, b: math.dist(player_chunk_pos, a.chunk_position)
				- math.dist(player_chunk_pos, b.chunk_position)))
		self.sorted_chunks = tuple(reversed(self.visible_chunks))

	def draw_translucent_fast(self):
		gl.glEnable(gl.GL_BLEND)
		gl.glDisable(gl.GL_CULL_FACE)
		gl.glDepthMask(gl.GL_FALSE)

		for render_chunk in self.sorted_chunks:
			render_chunk.draw_translucent(gl.GL_TRIANGLES)

		gl.glDepthMask(gl.GL_TRUE)
		gl.glEnable(gl.GL_CULL_FACE)
		gl.glDisable(gl.GL_BLEND)

	def draw_translucent_fancy(self):
		gl.glDepthMask(gl.GL_FALSE)
		gl.glFrontFace(gl.GL_CW)
		gl.glEnable(gl.GL_BLEND)

		for render_chunk in self.sorted_chunks:
			render_chunk.draw_translucent(gl.GL_TRIANGLES)

		gl.glFrontFace(gl.GL_CCW)

		for render_chunk in self.sorted_chunks:
			render_chunk.draw_translucent(gl.GL_TRIANGLES)

		gl.glDisable(gl.GL_BLEND)
		gl.glDepthMask(gl.GL_TRUE)

	draw_translucent = draw_translucent_fancy if options.FANCY_TRANSLUCENCY else draw_translucent_fast

	def draw(self):
		# Debug variables

		self.visible_entities = 0
                
		# daylight stuff

		daylight_multiplier = self.daylight / 1800
		gl.glClearColor(0.5 * (daylight_multiplier - 0.26),
				0.8 * (daylight_multiplier - 0.26),
				(daylight_multiplier - 0.26) * 1.36, 1.0)

		# setup block shader

		self.block_shader.use()
		self.block_shader.uniform_matrix(self.block_shader_matrix_location, self.mvp_matrix)
		gl.glUniform1f(self.block_shader_daylight_location, daylight_multiplier)

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_manager.texture_array)
		gl.glUniform1i(self.block_shader_sampler_location, 0)

		# draw chunks

		gl.glEnable(gl.GL_CULL_FACE)

		for render_chunk in self.visible_chunks:
			render_chunk.draw(gl.GL_TRIANGLES)

		# draw entities

		self.entity_shader.use()
		gl.glDisable(gl.GL_CULL_FACE)

		for entity in self.entities:
			dist = math.sqrt(sum(map(lambda x: (x[0] - x[1]) ** 2, zip(entity.position, self.player.position))))

			if dist > 32 or not self.player.check_in_frustum(entity.collider):
				continue

			entity.draw()
			self.visible_entities += 1

		# draw translucent chunks

		gl.glEnable(gl.GL_CULL_FACE)
		self.block_shader.use()

		self.draw_translucent()

	def update_daylight(self):
		if self.incrementer == -1:
			if self.daylight < 480: # Moonlight of 4
				self.incrementer = 0
		elif self.incrementer == 1:
			if self.daylight >= 1800:
				self.incrementer = 0

		if self.time % 36000 == 0:
			self.incrementer = 1
		elif self.time % 36000 == 18000:
			self.incrementer = -1

		self.daylight += self.incrementer

	def build_pending_chunks(self):
		if self.chunk_building_queue:
			pending_chunk = self.chunk_building_queue.popleft()
			pending_chunk.update_mesh()

	def process_chunk_updates(self):
		for chunk in self.visible_chunks:
			chunk.process_chunk_updates()

	def tick(self, delta_time):
		self.chunk_update_counter = 0
		self.time += 1
		self.pending_chunk_update_count = sum(len(chunk.chunk_update_queue) for chunk in self.chunks.values())
		self.update_daylight()
		self.build_pending_chunks()
		self.process_chunk_updates()





