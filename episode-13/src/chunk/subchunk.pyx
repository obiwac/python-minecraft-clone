import src.chunk.chunk as chunk
from src.chunk cimport CChunk, CSubchunk
from src.chunk cimport C_CHUNK_WIDTH, C_CHUNK_HEIGHT, C_CHUNK_LENGTH
from src.chunk cimport C_SUBCHUNK_WIDTH, C_SUBCHUNK_HEIGHT, C_SUBCHUNK_LENGTH

from libc.stdlib cimport malloc, realloc, free
from libc.string cimport memcpy
from libc.stdint cimport uint32_t, uint8_t
from pyglet.gl import gl

cdef bint can_render_face(uint8_t* parent_blocks, chunks, block_types, int block_number, block_type, int x_, int y_, int z_):
	cdef int x = x_ % C_CHUNK_WIDTH
	cdef int y = y_ % C_CHUNK_HEIGHT
	cdef int z = z_ % C_CHUNK_LENGTH

	cdef int adj_number = 0

	cdef CChunk c_chunk

	# getting block number from adjacent chunks is relatively slow, but we can just index the chunk directly if we know we're not on the edges of it

	if x == 0 or x == C_CHUNK_WIDTH - 1 or y == 0 or y == C_CHUNK_HEIGHT - 1 or z == 0 or z == C_CHUNK_LENGTH - 1:
		chunk_position = (
			x_ // C_CHUNK_WIDTH,
			y_ // C_CHUNK_HEIGHT,
			z_ // C_CHUNK_LENGTH)

		if chunk_position in chunks:
			c_chunk = chunks[chunk_position].c

			adj_number = c_chunk.blocks[
				x * C_CHUNK_LENGTH * C_CHUNK_HEIGHT +
				z * C_CHUNK_HEIGHT +
				y]

	else:
		adj_number = parent_blocks[
			x * C_CHUNK_LENGTH * C_CHUNK_HEIGHT +
			z * C_CHUNK_HEIGHT +
			y]

	adj_type = block_types[adj_number]

	if not adj_number or adj_type.transparent: # TODO getting transparent attribute of adjacent block incurs a lot of overhead
		if block_type.glass and adj_number == block_number: # rich compare between adj_number and block_number prevented
			return False

		return True

	return False

cdef update_mesh(self):
	cdef CSubchunk c = self.c

	if c.data_count:
		free(c.data)

	if c.index_count:
		free(c.indices)

	c.data_count = 0
	c.data = <float*>malloc(1)

	c.index_count = 0
	c.indices = <uint32_t*>malloc(1)

	def add_face(face):
		vertex_positions = block_type.vertex_positions[face]
		tex_coords = block_type.tex_coords[face]
		shading_values = block_type.shading_values[face]

		cdef float[4 * 7] data
		cdef size_t i

		for i in range(4):
			data[i * 7 + 0] = vertex_positions[i * 3 + 0] + x
			data[i * 7 + 1] = vertex_positions[i * 3 + 1] + y
			data[i * 7 + 2] = vertex_positions[i * 3 + 2] + z

			data[i * 7 + 3] = tex_coords[i * 3 + 0]
			data[i * 7 + 4] = tex_coords[i * 3 + 1]
			data[i * 7 + 5] = tex_coords[i * 3 + 2]

			data[i * 7 + 6] = shading_values[i]

		# TODO make realloc not increment one at a time

		c.data_count += sizeof(data) // sizeof(data[0])
		c.data = <float*>realloc(c.data, c.data_count * sizeof(data[0]))
		memcpy(<void*>c.data + c.data_count * sizeof(data[0]) - sizeof(data), data, sizeof(data))

		cdef uint32_t[6] indices = [0, 1, 2, 0, 2, 3]

		for i in range(6):
			indices[i] += c.index_count // 6 * 4

		c.index_count += sizeof(indices) // sizeof(indices[0])
		c.indices = <uint32_t*>realloc(c.indices, c.index_count * sizeof(indices[0]))
		memcpy(<void*>c.indices + c.index_count * sizeof(indices[0]) - sizeof(indices), indices, sizeof(indices))

	chunks = self.world.chunks
	block_types = self.world.block_types

	cdef CChunk c_parent = self.parent.c
	cdef uint8_t* parent_blocks = c_parent.blocks

	cdef int slx = self.local_position[0]
	cdef int sly = self.local_position[1]
	cdef int slz = self.local_position[2]

	cdef int sx = self.position[0]
	cdef int sy = self.position[1]
	cdef int sz = self.position[2]

	cdef int x, y, z
	cdef int parent_lx, parent_ly, parent_lz
	cdef int block_number
	cdef int local_x, local_y, local_z

	for local_x in range(C_SUBCHUNK_WIDTH):
		for local_y in range(C_SUBCHUNK_HEIGHT):
			for local_z in range(C_SUBCHUNK_LENGTH):
				parent_lx = slx + local_x
				parent_ly = sly + local_y
				parent_lz = slz + local_z

				block_number = parent_blocks[
					parent_lx * C_CHUNK_LENGTH * C_CHUNK_HEIGHT +
					parent_lz * C_CHUNK_HEIGHT +
					parent_ly]

				if block_number:
					block_type = block_types[block_number]

					x = sx + local_x
					y = sy + local_y
					z = sz + local_z

					# if block is cube, we want it to check neighbouring blocks so that we don't uselessly render faces
					# if block isn't a cube, we just want to render all faces, regardless of neighbouring blocks
					# since the vast majority of blocks are probably anyway going to be cubes, this won't impact performance all that much; the amount of useless faces drawn is going to be minimal

					if block_type.is_cube:
						if can_render_face(parent_blocks, chunks, block_types, block_number, block_type, x + 1, y, z): add_face(0)
						if can_render_face(parent_blocks, chunks, block_types, block_number, block_type, x - 1, y, z): add_face(1)
						if can_render_face(parent_blocks, chunks, block_types, block_number, block_type, x, y + 1, z): add_face(2)
						if can_render_face(parent_blocks, chunks, block_types, block_number, block_type, x, y - 1, z): add_face(3)
						if can_render_face(parent_blocks, chunks, block_types, block_number, block_type, x, y, z + 1): add_face(4)
						if can_render_face(parent_blocks, chunks, block_types, block_number, block_type, x, y, z - 1): add_face(5)

					else:
						for i in range(len(block_type.vertex_positions)):
							add_face(i)

class Subchunk:
	def __init__(self, parent, subchunk_position):
		self.parent = parent
		self.world = self.parent.world

		self.subchunk_position = subchunk_position

		self.local_position = (
			self.subchunk_position[0] * C_SUBCHUNK_WIDTH,
			self.subchunk_position[1] * C_SUBCHUNK_HEIGHT,
			self.subchunk_position[2] * C_SUBCHUNK_LENGTH)

		self.position = (
			self.parent.position[0] + self.local_position[0],
			self.parent.position[1] + self.local_position[1],
			self.parent.position[2] + self.local_position[2])

		self.c = CSubchunk()

	def update_mesh(self):
		update_mesh(self)
