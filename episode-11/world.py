import math
import random
import noise

import time
import threading

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

		for x in range(16):
			for y in range(8):
				for z in range(16):
					chunk_position = (x - 8, y - 4, z - 8)
					current_chunk = chunk.Chunk(self, chunk_position)

					for i in range(chunk.CHUNK_WIDTH):
						for j in reversed(range(chunk.CHUNK_HEIGHT)):
							for k in range(chunk.CHUNK_LENGTH):
								# if j == 15: current_chunk.blocks[i][j][k] = random.choices([0, 9, 10], [20, 2, 1])[0]
								# elif j == 14: current_chunk.blocks[i][j][k] = 2
								# elif j > 11: current_chunk.blocks[i][j][k] = 4
								# else: current_chunk.blocks[i][j][k] = 5

								scale = 32.0
								is_cave = noise.pnoise3((x * chunk.CHUNK_WIDTH + i) / scale, (y * chunk.CHUNK_HEIGHT + j) / scale, (z * chunk.CHUNK_LENGTH + k) / scale, octaves = 3)

								scale = 48.0
								biome = noise.pnoise3(1000 + (x * chunk.CHUNK_WIDTH + i) / scale, 1000 + (y * chunk.CHUNK_HEIGHT + j) / scale, 1000 + (z * chunk.CHUNK_LENGTH + k) / scale)

								blocks = [5, 4, 2, 9, 10]

								if biome > 0.0:
									blocks = [5, 5, 6, 12, 11]
								
								if is_cave < (-(y * chunk.CHUNK_HEIGHT + j) + 4 * 16) * 0.1 / 16:
									if j + 1 < chunk.CHUNK_HEIGHT and current_chunk.blocks[i][j + 1][k] == 0:
										current_chunk.blocks[i][j][k] = blocks[2]
										current_chunk.blocks[i][j + 1][k] = random.choices([0, blocks[3], blocks[4]], [20, 2, 1])[0]
									
									elif j + 1 < chunk.CHUNK_HEIGHT and current_chunk.blocks[i][j + 1][k] == blocks[2]:
										current_chunk.blocks[i][j][k] = blocks[1]
									
									else:
										current_chunk.blocks[i][j][k] = blocks[0]

					self.chunks[chunk_position] = current_chunk

		# multiprocessing

		self.chunk_load_queue = {}
		self.active_loading_chunks = []
		self.active_threads = 0

		for chunk_position in self.chunks:
			self.add_chunk_to_load_queue(chunk_position)

	def add_chunk_to_load_queue(self, chunk_position):
		def chunk_load_function(chunk): # in separate thread
			# time.sleep(0.1)

			chunk.update_subchunk_meshes()
			chunk.update_mesh()

		chunk = self.chunks[chunk_position]

		thread = threading.Thread(target = chunk_load_function, args = (chunk,))
		thread.daemon = True

		self.chunk_load_queue[chunk_position] = {"chunk": chunk, "thread": thread, "running": False}

	def process_load_queue(self, propagation_position = (0, 0, 0)):
		closest_chunk_position = None
		closest_chunk_distance = math.inf

		for chunk_position in self.chunk_load_queue:
			queue_object = self.chunk_load_queue[chunk_position]

			if queue_object["running"]:
				if not queue_object["thread"].is_alive():
					queue_object["chunk"].send_mesh_data_to_gpu() # we don't wanna put this in 'chunk_load_function' because we could lose the GIL at any time during the execution of this function

					del self.chunk_load_queue[chunk_position]

					self.active_loading_chunks.remove(chunk_position)
					self.active_threads -= 1

					break # break since we just changed our dictionary's size
				
				continue

			chunk_distance = math.sqrt(
				(chunk_position[0] * chunk.CHUNK_WIDTH  - propagation_position[0]) ** 2 +
				(chunk_position[1] * chunk.CHUNK_HEIGHT - propagation_position[1]) ** 2 +
				(chunk_position[2] * chunk.CHUNK_LENGTH - propagation_position[2]) ** 2)

			if chunk_distance < closest_chunk_distance:
				closest_chunk_distance = chunk_distance
				closest_chunk_position = chunk_position

		else: # else means we didn't artificially break out of the loop (idk why we can't use 'elif' here)
			if closest_chunk_position and closest_chunk_distance < 320:
				chunk_position = closest_chunk_position
				queue_object = self.chunk_load_queue[chunk_position]
				
				if self.active_threads < 1: #len(os.sched_getaffinity(0)): # 'multiprocessing.cpu_count' gives us *total* CPU count, not CPU's usable by our program
					queue_object["thread"].start()
					queue_object["running"] = True

					self.active_loading_chunks.append(chunk_position)
					self.active_threads += 1

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

	def is_opaque_block(self, position):
		block_type = self.block_types[self.get_block_number(position)]

		if not block_type:
			return False

		return not block_type.transparent

	def set_block(self, position, number):
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if not chunk_position in self.chunks:
			if number == 0:
				return # no point in creating a whole new chunk if we're not gonna be adding anything to it

			self.chunks[chunk_position] = chunk.Chunk(self, chunk_position)

		if self.get_block_number(position) == number:
			return

		lx, ly, lz = self.get_local_position(position)

		def try_update_chunk_at_position(chunk_position, position):
			if chunk_position in self.chunks and not chunk_position in self.active_loading_chunks:
				self.chunks[chunk_position].update_at_position(position)

				self.chunks[chunk_position].update_mesh()
				self.chunks[chunk_position].send_mesh_data_to_gpu()

		self.chunks[chunk_position].blocks[lx][ly][lz] = number
		try_update_chunk_at_position(chunk_position, position)

		cx, cy, cz = chunk_position

		if lx == chunk.CHUNK_WIDTH - 1: try_update_chunk_at_position((cx + 1, cy, cz), (x + 1, y, z))
		if lx == 0: try_update_chunk_at_position((cx - 1, cy, cz), (x - 1, y, z))

		if ly == chunk.CHUNK_HEIGHT - 1: try_update_chunk_at_position((cx, cy + 1, cz), (x, y + 1, z))
		if ly == 0: try_update_chunk_at_position((cx, cy - 1, cz), (x, y - 1, z))

		if lz == chunk.CHUNK_LENGTH - 1: try_update_chunk_at_position((cx, cy, cz + 1), (x, y, z + 1))
		if lz == 0: try_update_chunk_at_position((cx, cy, cz - 1), (x, y, z - 1))

	def draw(self):
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()