import math
import random
import noise

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
		self.block_types.append(block_type.Block_type(self.texture_manager, "grass", {"top": "grass", "bottom": "dirt", "sides": "grass_side"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "grass_block", {"all": "grass"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "dirt", {"all": "dirt"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "stone", {"all": "stone"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "sand", {"all": "sand"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "planks", {"all": "planks"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "log", {"top": "log_top", "bottom": "log_top", "sides": "log_side"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, "daisy", {"all": "daisy"}, models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, "rose", {"all": "rose"}, models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, "cactus", {"top": "cactus_top", "bottom": "cactus_bottom", "sides": "cactus_side"}, models.cactus))
		self.block_types.append(block_type.Block_type(self.texture_manager, "dead_bush", {"all": "dead_bush"}, models.plant))

		self.texture_manager.generate_mipmaps()

		self.chunks = {}

		## Noise settings
		octaves = 10
		base = 2

		for x in range(2):
			for z in range(2):
				chunk_position = (x - 1, -1, z - 1)
				current_chunk = chunk.Chunk(self, chunk_position)

				for chunk_x in range(chunk.CHUNK_WIDTH):
					for chunk_y in range(chunk.CHUNK_HEIGHT):
						for chunk_z in range(chunk.CHUNK_LENGTH):
							if chunk_y == 15: 
								current_chunk.blocks[chunk_x][chunk_y][chunk_z] = random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 9, 10])
							elif chunk_y == 14: 
								current_chunk.blocks[chunk_x][chunk_y][chunk_z] = 2
							elif chunk_y > 10: 
								current_chunk.blocks[chunk_x][chunk_y][chunk_z] = 4
							elif chunk_y == 10:
								current_chunk.blocks[chunk_x][chunk_y][chunk_z] = 5
							elif chunk_y == 0:
								current_chunk.blocks[chunk_x][chunk_y][chunk_z] = 5
							elif 10 > chunk_y > 0:
								block = 5
								random_num = random.randint(1, 2)
								extra_noise = noise.pnoise3(chunk_x/16+random_num/random_num, chunk_y/16+random_num, chunk_z/16+random_num/random_num)
								is_cave = noise.pnoise3(chunk_x/16+random_num+extra_noise, chunk_y/16+extra_noise+random_num, chunk_z/16+extra_noise)
								if is_cave < 0.02:
									block = 0
								current_chunk.blocks[chunk_x][chunk_y][chunk_z] = block

				self.chunks[chunk_position] = current_chunk
		
		for chunk_position in self.chunks:
			self.chunks[chunk_position].update_subchunk_meshes()
			self.chunks[chunk_position].update_mesh()
	
	# create functions to make things a bit easier

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
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if not chunk_position in self.chunks:
			return 0
		
		lx, ly, lz = self.get_local_position(position)

		block_number = self.chunks[chunk_position].blocks[lx][ly][lz]
		return block_number

	def is_solid_block(self, position):
		# get block type and check if it's transparent or not
		# return False if it is, True if it isn't
		# 'not block_type' tests if it's air

		block_type = self.block_types[self.get_block_number(position)]
		return block_type and not block_type.transparent

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
		self.chunks[chunk_position].update_position((x, y, z))

		cx, cy, cz = chunk_position

		if lx == chunk.CHUNK_WIDTH - 1 and (cx + 1, cy, cz) in self.chunks: self.chunks[(cx + 1, cy, cz)].update_position((x + 1, y, z))
		if lx == 0 and (cx - 1, cy, cz) in self.chunks: self.chunks[(cx - 1, cy, cz)].update_position((x - 1, y, z))

		if ly == chunk.CHUNK_HEIGHT - 1 and (cx, cy + 1, cz) in self.chunks: self.chunks[(cx, cy + 1, cz)].update_position((x, y + 1, z))
		if ly == 0 and (cx, cy - 1, cz) in self.chunks: self.chunks[(cx, cy - 1, cz)].update_position((x, y - 1, z))

		if lz == chunk.CHUNK_LENGTH - 1 and (cx, cy, cz + 1) in self.chunks: self.chunks[(cx, cy, cz + 1)].update_position((x, y, z + 1))
		if lz == 0 and (cx, cy, cz - 1) in self.chunks: self.chunks[(cx, cy, cz - 1)].update_position((x, y, z - 1))
	
	def draw(self):
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()