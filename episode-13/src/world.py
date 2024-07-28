import math
from src.chunk import CHUNK_HEIGHT, CHUNK_LENGTH, CHUNK_WIDTH
from src.chunk.chunk import Chunk
from src.save import Save
from src.renderer.block_type import BlockType
from src.renderer.texture_manager import TextureManager

# import custom block models

import models


class World:
	def __init__(self):
		self.texture_manager = TextureManager(16, 16, 256)
		self.block_types: list[BlockType | None] = [None]

		# parse block type data file

		with open("data/blocks.mcpy") as f:
			blocks_data = f.readlines()

		for block in blocks_data:
			if block[0] in ["\n", "#"]:  # skip if empty line or comment
				continue

			number, props = block.split(":", 1)
			number = int(number)

			# default block

			name = "Unknown"
			model = models.cube
			texture = {"all": "unknown"}

			# read properties

			for prop in props.split(","):
				prop = prop.strip()
				prop = list(filter(None, prop.split(" ", 1)))

				if prop[0] == "sameas":
					sameas_number = int(prop[1])
					sameas = self.block_types[sameas_number]

					if sameas is not None:
						name = sameas.name
						texture = sameas.block_face_textures
						model = sameas.model

				elif prop[0] == "name":
					name = eval(prop[1])

				elif prop[0][:7] == "texture":
					_, side = prop[0].split(".")
					texture[side] = prop[1].strip()

				elif prop[0] == "model":
					model = eval(prop[1])

			# add block type

			block_type = BlockType(self.texture_manager, name, texture, model)

			if number < len(self.block_types):
				self.block_types[number] = block_type

			else:
				self.block_types.append(block_type)

		self.texture_manager.generate_mipmaps()

		# load the world

		self.save = Save(self)

		self.chunks = {}
		self.save.load()

	def get_chunk_position(self, position):
		x, y, z = position

		return (
			math.floor(x / CHUNK_WIDTH),
			math.floor(y / CHUNK_HEIGHT),
			math.floor(z / CHUNK_LENGTH),
		)

	def get_local_position(self, position):
		x, y, z = position

		return (int(x % CHUNK_WIDTH), int(y % CHUNK_HEIGHT), int(z % CHUNK_LENGTH))

	def get_block_number(self, position):
		chunk_position = self.get_chunk_position(position)

		if chunk_position not in self.chunks:
			return 0

		pos = self.get_local_position(position)

		block_number = self.chunks[chunk_position].get_block(*pos)
		return block_number

	def is_opaque_block(self, position):
		# get block type and check if it's opaque or not
		# air counts as a transparent block, so test for that too

		block_type = self.block_types[self.get_block_number(position)]

		if not block_type:
			return False

		return not block_type.transparent

	def set_block(self, position, number):  # set number to 0 (air) to remove block
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if chunk_position not in self.chunks:  # if no chunks exist at this position, create a new one
			if number == 0:
				return  # no point in creating a whole new chunk if we're not gonna be adding anything

			self.chunks[chunk_position] = Chunk(self, chunk_position)

		if self.get_block_number(position) == number:  # no point updating mesh if the block is the same
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

		if lx == CHUNK_WIDTH - 1:
			try_update_chunk_at_position((cx + 1, cy, cz), (x + 1, y, z))
		if lx == 0:
			try_update_chunk_at_position((cx - 1, cy, cz), (x - 1, y, z))

		if ly == CHUNK_HEIGHT - 1:
			try_update_chunk_at_position((cx, cy + 1, cz), (x, y + 1, z))
		if ly == 0:
			try_update_chunk_at_position((cx, cy - 1, cz), (x, y - 1, z))

		if lz == CHUNK_LENGTH - 1:
			try_update_chunk_at_position((cx, cy, cz + 1), (x, y, z + 1))
		if lz == 0:
			try_update_chunk_at_position((cx, cy, cz - 1), (x, y, z - 1))

	def try_set_block(self, pos, num, collider):
		# if we're trying to remove a block, whatever let it go through

		if not num:
			return self.set_block(pos, 0)

		# make sure the block doesn't intersect with the passed collider

		for block_collider in self.block_types[num].colliders:
			if collider & (block_collider + pos):
				return

		self.set_block(pos, num)

	def draw(self):
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()
