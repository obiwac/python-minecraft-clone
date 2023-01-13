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

		# vertex positions

		self.vertices_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.vertices_vbo)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertices_vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(gl.GLfloat * vertex_count * 3), 0, gl.GL_STREAM_DRAW)

		gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(0)

		# texture coordinates
		# these can be filled in straight away as they won't change

		self.tex_coords_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.tex_coords_vbo)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.tex_coords_vbo)
		gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(gl.GLfloat * tex_coord_count * 2), 0, gl.GL_STREAM_DRAW)

		offset = 0

		for bone in self.model.bones:
			tex_coords = sum(bone["tex_coords"], [])

			type_ = gl.GLfloat * len(tex_coords)
			size = ctypes.sizeof(type_)

			gl.glBufferSubData(
				gl.GL_ARRAY_BUFFER, offset,
				size, (type_) (*tex_coords))

			offset += size

		gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(1)

		"""
		# normals

		self.normals_vbo = gl.GLuint(0)
		gl.glGenBuffers(1, self.normals_vbo)

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.normals_vbo)
		gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
		gl.glEnableVertexAttribArray(2)
		"""

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

	def animate(self, age, speed):
		print(age, speed)
		gl.glBindVertexArray(self.vao)

		# compute & upload vertex positions

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertices_vbo)
		offset = 0

		for bone in self.model.bones:
			name = bone["name"]
			pivot = bone["pivot"]
			vertices = sum(bone["vertices"], [])

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

			if kind is not None:
				if kind == "head":
					anim.rotate_2d(math.sin(age) / 2, math.cos(age) / 2)

				if "leg" in kind:
					phase = math.tau / 2 * (kind == "odd_leg")
					anim.rotate_2d(0, math.sin(age * 10 + phase) * 15 * speed)

			anim.translate(*[-x for x in pivot])

			for i in range(len(vertices))[::3]:
				vector = vertices[i: i + 3] + [1]
				vertices[i: i + 3] = matrix.multiply_matrix_vector(anim, vector)[:3]

			# upload vertex positions

			type_ = gl.GLfloat * len(vertices)
			size = ctypes.sizeof(type_)

			gl.glBufferSubData(
				gl.GL_ARRAY_BUFFER, offset,
				size, (type_) (*vertices))

			offset += size

		"""
		# compute normals

		self.normals = []

		for face in model.vertex_positions:
			# take the cross product between two vectors we know are on the plane the face belongs to

			u = [face[0] - face[3], face[1] - face[4], face[2] - face[5]]
			v = [face[0] - face[6], face[1] - face[7], face[2] - face[8]]

			n = [
				 u[1] * v[2] - u[2] * v[1],
				-u[0] * v[2] + u[2] * v[0],
				 u[0] * v[1] - u[1] * v[0],
			]

			self.normals.extend(n * 4)

		# upload normals

		gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.normals_vbo)
		gl.glBufferData(
			gl.GL_ARRAY_BUFFER,
			ctypes.sizeof(gl.GLfloat * len(self.normals)),
			(gl.GLfloat * len(self.normals)) (*self.normals),
			gl.GL_STATIC_DRAW)
		"""

	def draw(self):
		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
		gl.glUniform1i(self.world.entity_shader_sampler_location, 0)

		# draw entity

		gl.glBindVertexArray(self.vao)
		gl.glDrawElements(gl.GL_TRIANGLES, len(self.indices), gl.GL_UNSIGNED_INT, None)
