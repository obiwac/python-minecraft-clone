from util import *
import numpy as np
import glm
import options

SUBCHUNK_WIDTH  = 4
SUBCHUNK_HEIGHT = 4
SUBCHUNK_LENGTH = 4

class Subchunk:
	def __init__(self, parent, subchunk_position):
		self.parent = parent
		self.world = self.parent.world

		self.subchunk_position = subchunk_position

		self.local_position = (
			self.subchunk_position[0] * SUBCHUNK_WIDTH,
			self.subchunk_position[1] * SUBCHUNK_HEIGHT,
			self.subchunk_position[2] * SUBCHUNK_LENGTH)

		self.position = (
			self.parent.position[0] + self.local_position[0],
			self.parent.position[1] + self.local_position[1],
			self.parent.position[2] + self.local_position[2])

		# mesh variables

		self.mesh = []
		self.mesh_array = None
	
		self.translucent_mesh = []
		self.translucent_mesh_array = None

	def get_block_light(self, face, pos, npos):
		if not npos:
			light_levels = self.world.get_light(pos)
		else:
			light_levels = self.world.get_light(npos)
		return [light_levels] * 4

	def get_sky_light(self, face, pos, npos):
		if not npos:
			light_levels = self.world.get_skylight(pos)
		else:
			light_levels = self.world.get_skylight(npos)
		return [light_levels] * 4

	def get_vertex_ao(self, light, light2, light3, corner):
		ambient1 = glm.mix(light, light2, 1/2)
		ambient2 = glm.mix(light, light3, 1/2)
		ambient3 = glm.mix(light, corner, 1/2)
		return (ambient1, ambient2, ambient3) / 3

	def get_baked_face_light(self, light, light1, light2, light3,
										  light4,		  light5,
										  light6, light7, light8):
		vertex1 = self.get_vertex_ao(light, light2, light4, light1)
		vertex2 = self.get_vertex_ao(light, light4, light7, light6)
		vertex3 = self.get_vertex_ao(light, light5, light7, light8)
		vertex4 = self.get_vertex_ao(light, light2, light5, light3)
		return (vertex1, vertex2, vertex3, vertex4)

	def get_neighbour_voxels(self, npos, face):
		match face:
			case 0: # EAST
				neighbours = [
					npos + UP + SOUTH,
					npos + UP,
					npos + UP + NORTH,
					npos + SOUTH,
					npos + NORTH,
					npos + DOWN + SOUTH,
					npos + DOWN,
					npos + DOWN + NORTH
				]
			case 1: # WEST
				neighbours = [
					npos + UP + NORTH,
					npos + UP,
					npos + UP + SOUTH,
					npos + NORTH,
					npos + SOUTH,
					npos + DOWN + NORTH,
					npos + DOWN,
					npos + DOWN + SOUTH
				]
			case 2: # UP
				neighbours = [
					npos + SOUTH + EAST, npos + SOUTH, npos + SOUTH + WEST,
					npos + EAST,					   npos + WEST,
					npos + NORTH + EAST, npos + NORTH, npos + NORTH + WEST
				]
			case 3: # DOWN
				neighbours = [
					npos + SOUTH + WEST, npos + SOUTH, npos + SOUTH + EAST,
					npos + WEST,                       npos + EAST,
					npos + NORTH + WEST, npos + NORTH, npos + NORTH + EAST
				]
			case 4:
				neighbours = [
					npos + UP + WEST, npos + UP, npos + UP + EAST,
					npos + WEST,                 npos + EAST,
					npos + DOWN + WEST, npos + DOWN, npos + DOWN + EAST
				]
			case 5:
				neighbours = [
					npos + UP + EAST, npos + UP, npos + UP + WEST,
					npos + EAST,                 npos + WEST,
					npos + DOWN + EAST, npos + DOWN, npos + DOWN + WEST
				]
		return neighbours



	def get_baked_light(self, face, pos, npos):
		if not npos:
			return [self.world.get_light(pos)] * 4

		neighbours = self.get_neighbour_voxels(npos, face)

		nlights = (self.world.get_light(neighbour_pos) for neighbour_pos in neighbours)

		return self.get_baked_face_light(self.world.get_light(npos), *nlights)

	def get_baked_skylight(self, face, pos, npos):
		if not npos:
			return [self.world.get_skylight(pos)] * 4

		neighbours = self.get_neighbour_voxels(npos, face)
		
		nlights = (self.world.get_skylight(neighbour_pos) for neighbour_pos in neighbours)

		return self.get_baked_face_light(self.world.get_skylight(npos), *nlights)

	get_light = get_baked_light if options.SMOOTH_LIGHTING else get_block_light
	get_skylight = get_baked_skylight if options.SMOOTH_LIGHTING else get_sky_light

	def add_face(self, face, pos, lpos, block_type, npos=None):
		lx, ly, lz = lpos
		vertex_positions = block_type.vertex_positions[face]
		tex_index = block_type.tex_indices[face]
		shading_values = block_type.shading_values[face]
		baked_lights = self.get_light(face, pos, npos)
		baked_skylights = self.get_skylight(face, pos, npos)

		if block_type.model.translucent:
			mesh = self.translucent_mesh
		else:
			mesh = self.mesh
		
		for i in range(4):
			mesh += [vertex_positions[i * 3 + 0] + lx, 
					 vertex_positions[i * 3 + 1] + ly, 
					 vertex_positions[i * 3 + 2] + lz,
					 tex_index * 4 + i,
					 shading_values[i],
					 baked_lights[i],
					 baked_skylights[i]]
					 

	def can_render_face(self, block_type, block_number, position):
		return not (self.world.is_opaque_block(position)
			or (block_type.glass and self.world.get_block_number(position) == block_number))
			

	def update_mesh(self):
		self.mesh = []
		self.translucent_mesh = []

		for local_x in range(SUBCHUNK_WIDTH):
			for local_y in range(SUBCHUNK_HEIGHT):
				for local_z in range(SUBCHUNK_LENGTH):
					parent_lx = self.local_position[0] + local_x
					parent_ly = self.local_position[1] + local_y
					parent_lz = self.local_position[2] + local_z

					block_number = self.parent.blocks[parent_lx][parent_ly][parent_lz]

					parent_lpos = glm.ivec3(parent_lx, parent_ly, parent_lz)

					if block_number:
						block_type = self.world.block_types[block_number]

						x, y, z = pos = glm.ivec3(
							self.position[0] + local_x,
							self.position[1] + local_y,
							self.position[2] + local_z)
						

						# if block is cube, we want it to check neighbouring blocks so that we don't uselessly render faces
						# if block isn't a cube, we just want to render all faces, regardless of neighbouring blocks
						# since the vast majority of blocks are probably anyway going to be cubes, this won't impact performance all that much; the amount of useless faces drawn is going to be minimal

						if block_type.is_cube:
							for face, direction in enumerate(DIRECTIONS):
								npos = pos + direction
								if self.can_render_face(block_type, block_number, npos):
									self.add_face(face, pos, parent_lpos, block_type, npos)
														
						else:
							for i in range(len(block_type.vertex_positions)):
								self.add_face(i, pos, parent_lpos, block_type)

