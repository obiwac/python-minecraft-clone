import nbtlib as nbt
import base36

from src.chunk.chunk import Chunk, CHUNK_HEIGHT, CHUNK_LENGTH, CHUNK_WIDTH


class Save:
	def __init__(self, world, path="save"):
		self.world = world
		self.path = path

	def chunk_position_to_path(self, chunk_position):
		x, _, z = chunk_position

		chunk_path = "/".join(
			(self.path, base36.dumps(x % 64), base36.dumps(z % 64), f"c.{base36.dumps(x)}.{base36.dumps(z)}.dat")
		)

		return chunk_path

	def load_chunk(self, chunk_position):
		# load the chunk file

		chunk_path = self.chunk_position_to_path(chunk_position)

		try:
			chunk_blocks = nbt.load(chunk_path)["Level"]["Blocks"]

		except FileNotFoundError:
			return

		# create chunk and fill it with the blocks from our chunk file

		self.world.chunks[chunk_position] = Chunk(self.world, chunk_position)

		for x in range(CHUNK_WIDTH):
			for y in range(CHUNK_HEIGHT):
				for z in range(CHUNK_LENGTH):
					self.world.chunks[chunk_position].blocks[x][y][z] = chunk_blocks[
						x * CHUNK_LENGTH * CHUNK_HEIGHT + z * CHUNK_HEIGHT + y
					]

	def save_chunk(self, chunk_position):
		x, y, z = chunk_position

		# try to load the chunk file
		# if it doesn't exist, create a new one

		chunk_path = self.chunk_position_to_path(chunk_position)

		try:
			chunk_data = nbt.load(chunk_path)

		except FileNotFoundError:
			chunk_data = nbt.File({"": nbt.Compound({"Level": nbt.Compound()})})

			chunk_data["Level"]["xPos"] = x
			chunk_data["Level"]["zPos"] = z

		# fill the chunk file with the blocks from our chunk

		chunk_blocks = nbt.ByteArray([0] * (CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_LENGTH))

		for x in range(CHUNK_WIDTH):
			for y in range(CHUNK_HEIGHT):
				for z in range(CHUNK_LENGTH):
					chunk_blocks[
						x * CHUNK_LENGTH * CHUNK_HEIGHT + z * CHUNK_HEIGHT + y
					] = self.world.chunks[
						chunk_position
					].blocks[x][y][z]

		# save the chunk file

		chunk_data["Level"]["Blocks"] = chunk_blocks
		chunk_data.save(chunk_path, gzipped=True)

	def load(self):
		# for x in range(-16, 15):
		# 	for y in range(-15, 16):
		# 		self.load_chunk((x, 0, y))

		# for x in range(-4, 4):
		# 	for y in range(-4, 4):
		# 		self.load_chunk((x, 0, y))

		for x in range(-1, 1):
			for y in range(-1, 1):
				self.load_chunk((x, 0, y))

	def save(self):
		for chunk_position in self.world.chunks:
			if chunk_position[1] != 0:  # reject all chunks above and below the world limit
				continue

			chunk = self.world.chunks[chunk_position]

			if chunk.modified:
				self.save_chunk(chunk_position)
				chunk.modified = False
