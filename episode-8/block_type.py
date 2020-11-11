import numbers

class Block_type:
	def __init__(self, texture_manager, name = "unknown", block_face_textures = {"all": "cobblestone"}):
		self.name = name

		self.vertex_positions = numbers.vertex_positions
		self.tex_coords = numbers.tex_coords.copy()
		self.shading_values = numbers.shading_values

		def set_block_face(side, texture):
			self.tex_coords[side] = self.tex_coords[side].copy()

			for vertex in range(4):
				self.tex_coords[side][vertex * 3 + 2] = texture

		for face in block_face_textures:
			texture = block_face_textures[face]
			texture_manager.add_texture(texture)

			texture_index = texture_manager.textures.index(texture)

			if face == "all":
				set_block_face(0, texture_index)
				set_block_face(1, texture_index)
				set_block_face(2, texture_index)
				set_block_face(3, texture_index)
				set_block_face(4, texture_index)
				set_block_face(5, texture_index)
			
			elif face == "sides":
				set_block_face(0, texture_index)
				set_block_face(1, texture_index)
				set_block_face(4, texture_index)
				set_block_face(5, texture_index)
			
			else:
				set_block_face(["right", "left", "top", "bottom", "front", "back"].index(face), texture_index)