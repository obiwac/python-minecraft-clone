import models.cube # default model

class Block_type:
	# new optional model argument (cube model by default)
	def __init__(self, texture_manager, name = "unknown", block_face_textures = {"all": "cobblestone"}, model = models.cube):
		self.name = name

		# create members based on model attributes

		self.transparent = model.transparent
		self.is_cube = model.is_cube

		# replace data contained in numbers.py with model specific data

		self.vertex_positions = model.vertex_positions
		self.tex_coords = model.tex_coords.copy()
		self.shading_values = model.shading_values

		def set_block_face(face, texture):
			# make sure we don't add inexistent faces
			if face > len(self.tex_coords) - 1:
				return

			self.tex_coords[face] = self.tex_coords[face].copy()

			for vertex in range(4):
				self.tex_coords[face][vertex * 3 + 2] = texture

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