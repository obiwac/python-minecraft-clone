import ctypes
import math

import pyglet

import pyglet.gl as gl

import matrix

import models.pig # default model

class Entity_type:
	def __init__(self, world, name = "unknown", texture = "pig", model = models.pig, width = 0.6, height = 1.8):
		self.world = world

		self.name = name
		self.model = model

		self.width  = width
		self.height = height

		# load texture image

		texture_image = pyglet.image.load(f"textures/{texture}.png").get_image_data()

		self.texture_width  = texture_image.width
		self.texture_height = texture_image.height

		# create texture

		self.texture = gl.GLuint(0)
		gl.glGenTextures(1, self.texture)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)

		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

		gl.glTexImage2D(
			gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
			self.texture_width, self.texture_height,
			0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE,
			texture_image.get_data("RGBA", self.texture_width * 4))

		gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

		# get total size of the models so we can create vertex buffers

		vertex_count = 0
		tex_coord_count = 0

		for bone in model.bones:
			vertex_count += len(sum(bone["vertices"], [])) // 3
			tex_coord_count += len(sum(bone["tex_coords"], [])) // 2

		# create VAO/VBO/IBO

		self.vao = gl.GLuint(0)
		gl.glGenVertexArrays(1, self.vao)
		gl.glBindVertexArray(self.vao)

		# vertex positions & normals
		# we'll combine these two (6 floats per vertex, first 3 for position, next 3 for normal)

		self.vertices_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.vertices_vbo)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertices_vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * vertex_count * 6),
			0, gl.GL_STREAM_DRAW)

		size = ctypes.sizeof(gl.GLfloat * 3)

		gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, size * 2, size * 0)
		gl.glEnableVertexAttribArray(0)

		gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, size * 2, size * 1)
		gl.glEnableVertexAttribArray(1)

		# texture coordinates
		# these can be filled in straight away as they won't change

		self.tex_coords_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.tex_coords_vbo)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.tex_coords_vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(gl.GLfloat * tex_coord_count * 2), 0, gl.GL_STATIC_DRAW)

		offset = 0

		for bone in self.model.bones:
			tex_coords = sum(bone["tex_coords"], [])

			type_ = gl.GLfloat * len(tex_coords)
			size = ctypes.sizeof(type_)

			gl.glBufferSubData(
				gl.GL_ARRAY_BUFFER, offset,
				size, (type_) (*tex_coords))

			offset += size

		gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(2)

		# compute indices

		self.indices = []

		for i in range(vertex_count):
			self.indices.extend(x + i * 4 for x in (0, 1, 2, 0, 2, 3))

		# indices
		# these can be filled in straight away as they won't change

		self.ibo = gl.GLuint(0)
		gl.glGenBuffers(1, self.ibo)

		gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)
		gl.glBufferData(
			gl.GL_ELEMENT_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLuint * len(self.indices)),
			(gl.GLuint * len(self.indices)) (*self.indices),
			gl.GL_STATIC_DRAW)

	def animate(self, age, speed, position, rotation):
		gl.glBindVertexArray(self.vao)

		# compute & upload vertex positions

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertices_vbo)
		offset = 0

		for bone in self.model.bones:
			name = bone["name"]
			pivot = bone["pivot"]
			vertices = sum(bone["vertices"], [])
			buffer = vertices * 2 # we want our buffer to hold both vertex positions & normals

			# compute animation transformation matrix

			anim = matrix.Matrix()
			anim.load_identity()

			anim.translate(*pivot)

			kind = None

			if name == "head":
				kind = "head"

			elif name[:3] == "leg":
				kind = "odd_" * (int(name[3:]) in (1, 2)) + "leg"

			elif name == "rightLeg":
				kind = "leg"

			elif name == "leftLeg":
				kind = "odd_leg"

			elif name == "rightArm":
				kind = "arm"

			elif name == "leftArm":
				kind = "odd_arm"

			if kind is not None:
				odd = "odd" in kind

				if kind == "head":
					x, y, z = self.world.player.position

					dx = x - position[0]
					dy = y - position[1]
					dz = z - position[2]

					theta = -rotation[0] - math.atan2(dz, dx) - math.tau / 4
					iota = -math.atan2(dy, math.sqrt(dx ** 2 + dz ** 2))

					anim.rotate_2d(theta, 0)
					anim.rotate_2d(0, iota)

				if "leg" in kind:
					phase = math.tau / 2 * odd
					anim.rotate_2d(0, math.sin(age * 7 + phase) * 10 * speed)

				if "arm" in kind:
					theta = (-age if odd else age) * 2
					phase = math.tau / 2 * odd
					anim.rotate_2d(math.sin(theta + phase) / 8, math.cos(theta + phase) / 8 - math.tau / 4)

			anim.translate(*[-x for x in pivot])

			for i in range(0, len(vertices), 3):
				vector = vertices[i: i + 3] + [1]
				buffer[i * 2: i * 2 + 3] = matrix.multiply_matrix_vector(anim, vector)[:3]

			# compute normals

			for i in range(0, len(buffer), 24):
				# take the cross product between two vectors we know are on the plane the face belongs to

				n = matrix.cross_product(
					[buffer[i + 0] - buffer[i + 6], buffer[i + 1] - buffer[i + 7], buffer[i + 2] - buffer[i + 8]],
					[buffer[i + 0] - buffer[i + 12], buffer[i + 1] - buffer[i + 13], buffer[i + 2] - buffer[i + 14]]
				)

				# each vertex of a face will have the same normal, so we can simply copy it 4 times

				for j in range(4):
					buffer[i + j * 6 + 3: i + j * 6 + 6] = n

			# upload vertex buffer section

			type_ = gl.GLfloat * len(buffer)
			size = ctypes.sizeof(type_)

			gl.glBufferSubData(
				gl.GL_ARRAY_BUFFER, offset,
				size, (type_) (*buffer))

			offset += size

	def draw(self):
		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
		gl.glUniform1i(self.world.entity_shader_sampler_location, 0)

		# draw entity

		gl.glBindVertexArray(self.vao)
		gl.glDrawElements(gl.GL_TRIANGLES, len(self.indices), gl.GL_UNSIGNED_INT, None)
