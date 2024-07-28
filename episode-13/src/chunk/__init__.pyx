from src.chunk.common import CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_LENGTH
from src.chunk.common import SUBCHUNK_WIDTH, SUBCHUNK_HEIGHT, SUBCHUNK_LENGTH

from libc.stdlib cimport malloc, free
from libc.string cimport memset
from libc.stdint cimport uint8_t, uint32_t

cdef int C_CHUNK_WIDTH = CHUNK_WIDTH
cdef int C_CHUNK_HEIGHT = CHUNK_HEIGHT
cdef int C_CHUNK_LENGTH = CHUNK_LENGTH

cdef int C_SUBCHUNK_WIDTH = SUBCHUNK_WIDTH
cdef int C_SUBCHUNK_HEIGHT = SUBCHUNK_HEIGHT
cdef int C_SUBCHUNK_LENGTH = SUBCHUNK_LENGTH

cdef class CSubchunk:
	cdef size_t data_count
	cdef float* data

	cdef size_t index_count
	cdef uint32_t* indices

	def __init__(self):
		self.data_count = 0
		self.index_count = 0

cdef class CChunk:
	cdef size_t data_count
	cdef float* data

	cdef size_t index_count
	cdef int* indices

	cdef size_t size
	cdef uint8_t* blocks

	def __init__(self):
		self.size = CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_LENGTH * sizeof(self.blocks[0])
		self.blocks = <uint8_t*>malloc(self.size)
		memset(self.blocks, 0, self.size)

	def __del__(self):
		free(self.blocks)

	@property
	def index_count(self):
		return self.index_count

	def get_blocks(self, i):
		return self.blocks[i]

	def set_blocks(self, i, val):
		self.blocks[i] = val

	def copy_blocks(self, blocks):
		cdef int i
		cdef int length = len(blocks)

		for i in range(length):
			self.blocks[i] = blocks[i]
