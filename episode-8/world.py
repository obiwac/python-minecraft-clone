import math
import random
import time

import chunk

import block_type
import texture_manager

class World:
	def __init__(self):
		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.blocks = [None]
		
		self.blocks.append(block_type.Block_type(self.texture_manager, "cobblestone", {"all": "cobblestone"}))
		self.blocks.append(block_type.Block_type(self.texture_manager, "grass", {"top": "grass", "bottom": "dirt", "sides": "grass_side"}))
		self.blocks.append(block_type.Block_type(self.texture_manager, "grass_block", {"all": "grass"}))
		self.blocks.append(block_type.Block_type(self.texture_manager, "dirt", {"all": "dirt"}))
		self.blocks.append(block_type.Block_type(self.texture_manager, "stone", {"all": "stone"}))
		self.blocks.append(block_type.Block_type(self.texture_manager, "sand", {"all": "sand"}))
		self.blocks.append(block_type.Block_type(self.texture_manager, "planks", {"all": "planks"}))
		self.blocks.append(block_type.Block_type(self.texture_manager, "log", {"top": "log_top", "bottom": "log_top", "sides": "log_side"}))

		self.texture_manager.generate_mipmaps()

		self.chunks = {}

		for x in range(8):
			for z in range(8):
				chunk_position = (x - 4, -1, z - 4)
				current_chunk = chunk.Chunk(self, chunk_position)
				current_chunk.blocks = []

				for i in range(16):
					for j in range(16):
						for k in range(16):
							if j > 13: current_chunk.blocks.append(random.choice([0, 3]))
							else: current_chunk.blocks.append(random.choice([0, 0, 1]))
				
				self.chunks[chunk_position] = current_chunk
				self.chunks[chunk_position].update_mesh()

	def get_block(self, position):
		x, y, z = position

		chunk_x = math.floor(x / chunk.CHUNK_WIDTH)
		chunk_y = math.floor(y / chunk.CHUNK_HEIGHT)
		chunk_z = math.floor(z / chunk.CHUNK_LENGTH)

		local_x = int(x % chunk.CHUNK_WIDTH)
		local_y = int(y % chunk.CHUNK_HEIGHT)
		local_z = int(z % chunk.CHUNK_LENGTH)

		chunk_position = (chunk_x, chunk_y, chunk_z)

		if not chunk_position in self.chunks:
			return self.blocks[0]
		
		return self.blocks[self.chunks[chunk_position].blocks[local_x * chunk.CHUNK_LENGTH * chunk.CHUNK_HEIGHT + local_y * chunk.CHUNK_LENGTH + local_z]]

	def draw(self, position):
		for chunk_position in self.chunks:
			x = int(position[0] / chunk.CHUNK_WIDTH  - chunk_position[0])
			y = int(position[1] / chunk.CHUNK_HEIGHT - chunk_position[1])
			z = int(-position[2] / chunk.CHUNK_LENGTH - chunk_position[2])

			if math.sqrt(x * x + y * y + z * z) < 4:
				self.chunks[chunk_position].draw()