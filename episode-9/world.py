import math
import random

import chunk

import block_type
import texture_manager

# import custom block models

import models.plant
import models.cactus


class World:
	def __init__(self):
		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.block_types = [None]

		self.block_types.append(block_type.Block_type(self.texture_manager, "cobblestone", {"all": "cobblestone"}))
		self.block_types.append(
			block_type.Block_type(
				self.texture_manager, "grass", {"top": "grass", "bottom": "dirt", "sides": "grass_side"}
			)
		)
		self.block_types.append(block_type.Block_type(self.texture_manager, "grass_block", {"all": "grass"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "dirt", {"all": "dirt"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "stone", {"all": "stone"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "sand", {"all": "sand"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "planks", {"all": "planks"}))
		self.block_types.append(
			block_type.Block_type(
				self.texture_manager, "log", {"top": "log_top", "bottom": "log_top", "sides": "log_side"}
			)
		)
		self.block_types.append(block_type.Block_type(self.texture_manager, "daisy", {"all": "daisy"}, models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, "rose", {"all": "rose"}, models.plant))
		self.block_types.append(
			block_type.Block_type(
				self.texture_manager,
				"cactus",
				{"top": "cactus_top", "bottom": "cactus_bottom", "sides": "cactus_side"},
				models.cactus,
			)
		)
		self.block_types.append(
			block_type.Block_type(self.texture_manager, "dead_bush", {"all": "dead_bush"}, models.plant)
		)

		self.texture_manager.generate_mipmaps()

		self.chunks = {}

		for x in range(8):
			for z in range(8):
				chunk_position = (x - 4, -1, z - 4)
				current_chunk = chunk.Chunk(self, chunk_position)

				for i in range(chunk.CHUNK_WIDTH):
					for j in range(chunk.CHUNK_HEIGHT):
						for k in range(chunk.CHUNK_LENGTH):
							if j == 15:
								current_chunk.blocks[i][j][k] = random.choice(
									[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 12, 12, 11]
								)
							elif j > 12:
								current_chunk.blocks[i][j][k] = random.choice([0, 6])
							else:
								current_chunk.blocks[i][j][k] = random.choice([0, 0, 5])

				self.chunks[chunk_position] = current_chunk

		for chunk_position in self.chunks:
			self.chunks[chunk_position].update_mesh()

	# could admittedly be named better, as it only returns the block number of opaque blocks
	# this'll be refactored in a future episode

	def get_block_number(self, position):
		x, y, z = position

		chunk_position = (
			math.floor(x / chunk.CHUNK_WIDTH),
			math.floor(y / chunk.CHUNK_HEIGHT),
			math.floor(z / chunk.CHUNK_LENGTH),
		)

		if not chunk_position in self.chunks:
			return 0

		local_x = int(x % chunk.CHUNK_WIDTH)
		local_y = int(y % chunk.CHUNK_HEIGHT)
		local_z = int(z % chunk.CHUNK_LENGTH)

		# get block type and check if it's transparent or not
		# if it is, return 0
		# if it isn't, return the block number

		block_number = self.chunks[chunk_position].blocks[local_x][local_y][local_z]
		block_type = self.block_types[block_number]

		if not block_type or block_type.transparent:
			return 0
		else:
			return block_number

	def draw(self):
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()
