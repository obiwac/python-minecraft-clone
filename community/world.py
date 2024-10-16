import math
from random import *
from noise import *
import time
import threading

import chunk

import block_type
import texture_manager

# import custom block models
import models.leaves
import models.liquid
import models.plant
import models.cactus

class World:
	def __init__(self):
		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.block_types = [None]

		self.block_types.append(block_type.Block_type(self.texture_manager, name="cobblestone", block_face_textures = {"all": "cobblestone"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="grass", block_face_textures = {"top": "grass", "bottom": "dirt", "sides": "grass_side"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="grass_block", block_face_textures = {"all": "grass"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="dirt", block_face_textures = {"all": "dirt"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="stone", block_face_textures = {"all": "stone"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="sand", block_face_textures = {"all": "sand"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="planks", block_face_textures = {"all": "planks"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="log", block_face_textures = {"top": "log_top", "bottom": "log_top", "sides": "log_side"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="water", block_face_textures = {"all": "water"},  model = models.liquid, transparent=True))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="rose", block_face_textures = {"all": "rose"},  model = models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="cactus", block_face_textures = {"top": "cactus_top", "bottom": "cactus_bottom", "sides": "cactus_side"},  model = models.cactus))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="dead_bush", block_face_textures = {"all": "dead_bush"},  model = models.plant))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="leaves", block_face_textures = {"all": "leaves"},  model = models.leaves))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="bedrock", block_face_textures = {"all": "bedrock"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="lava", block_face_textures = {"all": "lava"},  model = models.liquid, transparent=True))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="coal_ore", block_face_textures = {"all": "coal_ore"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="iron_ore", block_face_textures = {"all": "iron_ore"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="diamond_ore", block_face_textures = {"all": "diamond_ore"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="under_water", block_face_textures = {"all": "water"}))
		self.block_types.append(block_type.Block_type(self.texture_manager, name="under_lava", block_face_textures = {"all": "lava"}))

		self.texture_manager.generate_mipmaps()

		self.chunks = {}
				
		self.scale = 100.0  # Controls the frequency of the noise
		self.octaves = 4   # Increased number of layers of noise to combine for more detail
		self.persistence = 0.5
		self.lacunarity = 2.0

		self.cave_scale = 10.0  # Controls the frequency of the cave noise
		self.cave_threshold = 0.1 # Threshold for cave generation

		for x in range(-8, 7):
			for z in range(-8, 7):
				self.generate_chunk(x, z)

		# multiprocessing

		self.chunk_load_queue = {}
		self.active_loading_chunks = []
		self.active_threads = 0

		for chunk_position in self.chunks:
			self.add_chunk_to_load_queue(chunk_position)

	def generate_chunk(self, x, z):
		chunk_position = (x, 0, z)
		current_chunk = chunk.Chunk(self, chunk_position)
		trees = list()
		for i in range(5):
			tree_x = randint(0, 15)
			tree_z = randint(0, 15)
			trees.append((tree_x, tree_z))

		chunk_offset_x = x * chunk.CHUNK_WIDTH
		chunk_offset_z = z * chunk.CHUNK_LENGTH

		for i in range(chunk.CHUNK_WIDTH):
			for j in range(chunk.CHUNK_HEIGHT):
				for k in range(chunk.CHUNK_LENGTH):
					# Use chunk-specific offsets to avoid repeating patterns
					surfaceY = 60 + pnoise2(
						(chunk_offset_x + i) / self.scale,
						(chunk_offset_z + k) / self.scale,
						octaves=self.octaves,
						persistence=self.persistence,
						lacunarity=self.lacunarity
					) * 50
					surfaceY = max(0, surfaceY)  # Ensure surfaceY is not below 0

					if j == 0:
						current_chunk.blocks[i][j][k] = 14

					if 0 < j < surfaceY:
						cave_noise = pnoise3(
							(chunk_offset_x + i) / self.cave_scale,
							j / self.cave_scale,
							(chunk_offset_z + k) / self.cave_scale
						)
						cave_noise2 = pnoise3(
							(chunk_offset_x + i) / (self.cave_scale * 2),
							j / (self.cave_scale * 2),
							(chunk_offset_z + k) / (self.cave_scale * 2)
						)

						if cave_noise < self.cave_threshold and cave_noise2 < self.cave_threshold and j != surfaceY-2:
							current_chunk.blocks[i][j][k] = 0  # Cave block
						else:
							current_chunk.blocks[i][j][k] = 5  # Ground block
						
						for l in range(math.ceil(surfaceY), 61):
							if l < 60:
								current_chunk.blocks[i][l][k] = 19  # Underground block
							else:
								current_chunk.blocks[i][l][k] = 9

						

					for m in range(math.ceil(surfaceY), math.ceil(surfaceY) + 2):
						current_chunk.blocks[i][m][k] = 4  # Surface block

					if surfaceY > 58:
						current_chunk.blocks[i][math.ceil(surfaceY)+2][k] = 2

					# Ore generation logic
					if 30 <= j <= surfaceY:
						if current_chunk.blocks[i][j][k] == 5 and randint(0, 100) < 5:  # Chance to place coal
							current_chunk.blocks[i][j][k] = 16  # Coal ore
					if 10 <= j <= 50:
						if current_chunk.blocks[i][j][k] == 5 and randint(0, 100) < 2:  # Chance to place iron
							current_chunk.blocks[i][j][k] = 17  # Iron ore
					if 2 <= j <= 15:
						if current_chunk.blocks[i][j][k] == 5 and randint(0, 1000) < 2:  # Chance to place diamond
							current_chunk.blocks[i][j][k] = 18  # Diamond ore

					# Cave entrance generation logic
					if 100 > surfaceY > 60:
						if randint(0, 5000) < 2:
							cave_width = randint(2, 3)
							for offset_x in range(-cave_width, cave_width + 1):
								for offset_z in range(-cave_width, cave_width + 1):
									if 0 <= i + offset_x < chunk.CHUNK_WIDTH and 0 <= k + offset_z < chunk.CHUNK_LENGTH:
										for j in range(int(surfaceY), chunk.CHUNK_HEIGHT):
											cave_noise = pnoise3(
												(chunk_offset_x + i + offset_x)/ self.cave_scale,
												j / self.cave_scale,
												(chunk_offset_z + k + offset_z)/ self.cave_scale
											)
											cave_noise2 = pnoise3(
												(chunk_offset_x + i + offset_x)/ (self.cave_scale * 2),
												j / (self.cave_scale * 2),
												(chunk_offset_z + k + offset_z)/ (self.cave_scale * 2)
											)
											if cave_noise < self.cave_threshold and cave_noise2 < self.cave_threshold:
												current_chunk.blocks[i + offset_x][j][k + offset_z] = 0  # Tunnel block
											else:
												break

					if 1 <= j <= 3 and current_chunk.blocks[i][j][k] == 0:
						current_chunk.blocks[i][j][k] = 5

					if 4 <=j <=7 and current_chunk.blocks[i][j][k] == 0:
						if j<7:
							current_chunk.blocks[i][j][k] = 20
						else:
							current_chunk.blocks[i][j][k] = 15

		for _ in range(5):
			placed = False
			attempts = 0
			while not placed and attempts < 50:  # Limit attempts to find a valid tree position
				tree_x = randint(0, 15)
				tree_z = randint(0, 15)
				baseY = math.ceil(surfaceY)
				tree_y = baseY + 2

				if current_chunk.blocks[tree_x][tree_y][tree_z] == 2:  # Check if the block is grass
					# Check surrounding blocks for existing trees
					has_adjacent_tree = False
					for dx in range(-1, 2):
						for dz in range(-1, 2):
							if 0 <= tree_x + dx < chunk.CHUNK_WIDTH and 0 <= tree_z + dz < chunk.CHUNK_LENGTH:
								if (tree_x + dx, tree_y, tree_z + dz) in trees:
									has_adjacent_tree = True
									break
						if has_adjacent_tree:
							break

					if not has_adjacent_tree:
						# Place the log blocks
						for n in range(5):
							current_chunk.blocks[tree_x][tree_y + n][tree_z] = 8  # Log block

						# Place the leaves blocks
						leaves_height = tree_y + 5
						for dx in range(-2, 3):
							for dz in range(-2, 3):
								if (0 <= tree_x + dx < chunk.CHUNK_WIDTH and 
									0 <= tree_z + dz < chunk.CHUNK_LENGTH):
									current_chunk.blocks[tree_x + dx][leaves_height][tree_z + dz] = 13
										# Leaves block
						if (0 <= tree_x< chunk.CHUNK_WIDTH and 
									0 <= tree_z< chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 1][tree_z] = 13
						if (0 <= tree_x+1< chunk.CHUNK_WIDTH and 
									0 <= tree_z + 1 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x+1][leaves_height + 1][tree_z+1] = 13
						if (0 <= tree_x - 1 < chunk.CHUNK_WIDTH and 
									0 <= tree_z + 1 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x-1][leaves_height + 1][tree_z+1] = 13
						if (0 <= tree_x - 1 < chunk.CHUNK_WIDTH and 
									0 <= tree_z - 1 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x-1][leaves_height + 1][tree_z-1] = 13
						if (0 <= tree_x + 1 < chunk.CHUNK_WIDTH and 
									0 <= tree_z -1 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x+1][leaves_height + 1][tree_z-1] = 13
						if (0 <= tree_x + 1 < chunk.CHUNK_WIDTH and 
									0 <= tree_z< chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x+1][leaves_height + 1][tree_z] = 13
						if (0 <= tree_x - 1 < chunk.CHUNK_WIDTH and 
									0 <= tree_z < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x-1][leaves_height + 1][tree_z] = 13
						if (0 <= tree_x < chunk.CHUNK_WIDTH and 
									0 <= tree_z + 1 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 1][tree_z+1] = 13
						if (0 <= tree_x < chunk.CHUNK_WIDTH and 
									0 <= tree_z - 1 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 1][tree_z-1] = 13
						if (0 <= tree_x + 2 < chunk.CHUNK_WIDTH and 
									0 <= tree_z < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x+2][leaves_height + 1][tree_z] = 13
						if (0 <= tree_x - 2 < chunk.CHUNK_WIDTH and 
									0 <= tree_z < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x-2][leaves_height + 1][tree_z] = 13
						if (0 <= tree_x < chunk.CHUNK_WIDTH and 
									0 <= tree_z + 2 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 1][tree_z+2] = 13
						if (0 <= tree_x < chunk.CHUNK_WIDTH and 
									0 <= tree_z - 2 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 1][tree_z-2] = 13
						if (0 <= tree_x < chunk.CHUNK_WIDTH and 
									0 <= tree_z < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 2][tree_z] = 13
						if (0 <= tree_x + 1 < chunk.CHUNK_WIDTH and 
									0 <= tree_z < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x+1][leaves_height + 2][tree_z] = 13
						if (0 <= tree_x - 1 < chunk.CHUNK_WIDTH and 
									0 <= tree_z < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x-1][leaves_height + 2][tree_z] = 13
						if (0 <= tree_x < chunk.CHUNK_WIDTH and 
									0 <= tree_z + 2 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 2][tree_z+1] = 13
						if (0 <= tree_x < chunk.CHUNK_WIDTH and 
									0 <= tree_z - 2 < chunk.CHUNK_LENGTH):
							current_chunk.blocks[tree_x][leaves_height + 2][tree_z-1] = 13

						trees.append((tree_x, tree_y, tree_z))
						placed = True
				attempts += 1

		self.chunks[chunk_position] = current_chunk

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

	def get_nearby_blocks(self, position):
    # Return a list of block positions near the player's position.
    # This is a placeholder implementation. You'll need to adapt this to your world's data structure.
		x, y, z = map(int, position)
		nearby_blocks = []
		for dx in range(-1, 2):
			for dy in range(-1, 2):
				for dz in range(-1, 2):
					block_pos = (x + dx, y + dy, z + dz)
					if self.get_block_number(block_pos):  # Check if there's a block at this position
						nearby_blocks.append(block_pos)
		return nearby_blocks


	def draw(self):
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()