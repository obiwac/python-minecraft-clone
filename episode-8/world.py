import math
import random

import chunk

import block_type
import texture_manager


class World:
	def __init__(self):
		# create list of block types

		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.block_types = [None]  # "None" is the block type for air

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

		self.texture_manager.generate_mipmaps()

		# create chunks with very crude terrain generation

		self.chunks = {}

		for x in range(8):
			for z in range(8):
				chunk_position = (x - 4, -1, z - 4)
				current_chunk = chunk.Chunk(self, chunk_position)

				for i in range(chunk.CHUNK_WIDTH):
					for j in range(chunk.CHUNK_HEIGHT):
						for k in range(chunk.CHUNK_LENGTH):
							if j > 13:
								current_chunk.blocks[i][j][k] = random.choice([0, 3])
							else:
								current_chunk.blocks[i][j][k] = random.choice([0, 0, 1])

				self.chunks[chunk_position] = current_chunk

		# update each chunk's mesh

		for chunk_position in self.chunks:
			self.chunks[chunk_position].update_mesh()

	def get_block_number(self, position):  # get the index in the block_types array of the block at a certain position
		x, y, z = position

		chunk_position = (  # get the chunk in which the the block is's position
			math.floor(x / chunk.CHUNK_WIDTH),
			math.floor(y / chunk.CHUNK_HEIGHT),
			math.floor(z / chunk.CHUNK_LENGTH),
		)

		if chunk_position not in self.chunks:  # return "air" if the chunk doesn't exist
			return 0

		# get the relative position of the block in the chunk

		local_x = int(x % chunk.CHUNK_WIDTH)
		local_y = int(y % chunk.CHUNK_HEIGHT)
		local_z = int(z % chunk.CHUNK_LENGTH)

		return self.chunks[chunk_position].blocks[local_x][local_y][
			local_z
		]  # return the block number at the local position in the correct chunk

	def draw(self):  # draw all the chunks in the world
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()
