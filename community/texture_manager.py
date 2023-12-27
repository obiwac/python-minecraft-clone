import options
import pyglet
import logging

import pyglet.gl as gl
from PIL import Image
import OpenGL.GL as pgl


class GLImage:
	def __init__(self, gl_id, width, height, uv0, uv1) -> None:
		self.id = gl_id
		self.width = width
		self.height = height
		self.uv0 = uv0
		self.uv1 = uv1


class TextureManager:
	def __init__(self, texture_width, texture_height, max_textures):
		self.texture_width = texture_width
		self.texture_height = texture_height

		self.max_textures = max_textures

		self.textures = []

		self.texture_array = gl.GLuint(0)
		gl.glGenTextures(1, self.texture_array)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array)

		gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MIN_FILTER, options.MIPMAP_TYPE)
		gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

		gl.glTexImage3D(
			gl.GL_TEXTURE_2D_ARRAY, 0, gl.GL_RGBA,
			self.texture_width, self.texture_height, self.max_textures,
			0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
	
	def generate_mipmaps(self):
		logging.debug(f"Generating Mipmaps, using mipmap type {options.MIPMAP_TYPE}")
		gl.glGenerateMipmap(gl.GL_TEXTURE_2D_ARRAY)
	
	def add_texture(self, texture):
		logging.debug(f"Loading texture textures/{texture}.png")

		if not texture in self.textures:
			self.textures.append(texture)

			texture_image = pyglet.image.load(f"textures/{texture}.png").get_image_data()
			gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array)

			gl.glTexSubImage3D(
				gl.GL_TEXTURE_2D_ARRAY, 0,
				0, 0, self.textures.index(texture),
				self.texture_width, self.texture_height, 1,
				gl.GL_RGBA, gl.GL_UNSIGNED_BYTE,
				texture_image.get_data("RGBA", texture_image.width * 4))

	def load_texture(self, texture, use_pyglet_gl = True):
		logging.debug(f"Loading texture textures/{texture}.png")

		if use_pyglet_gl:
			image = pyglet.image.load(f"textures/{texture}.png")
			width = image.width
			height = image.height

			return GLImage(image.get_texture().id, width, height, (0, 1), (1, 0))
		else:
			# Load the image using PIL
			image = Image.open(f"textures/{texture}.png")
			img_data = list(image.getdata())

			# Create a texture ID
			texture_id = pgl.glGenTextures(1)

			# Bind the texture
			pgl.glBindTexture(pgl.GL_TEXTURE_2D, texture_id)

			# Set texture parameters
			pgl.glTexParameteri(pgl.GL_TEXTURE_2D, pgl.GL_TEXTURE_MIN_FILTER, pgl.GL_LINEAR)
			pgl.glTexParameteri(pgl.GL_TEXTURE_2D, pgl.GL_TEXTURE_MAG_FILTER, pgl.GL_LINEAR)

			# Convert image data to bytes
			img_bytes = []
			for rgba in img_data:
				img_bytes.extend(rgba)

			# Upload the texture data
			pgl.glTexImage2D(
				pgl.GL_TEXTURE_2D,
				0,
				pgl.GL_RGBA,
				image.width,
				image.height,
				0,
				pgl.GL_RGBA,
				pgl.GL_UNSIGNED_BYTE,
				(pgl.GLubyte * len(img_bytes))(*img_bytes)
			)

			# Unbind the texture
			pgl.glBindTexture(pgl.GL_TEXTURE_2D, 0)

			return GLImage(texture_id, image.width, image.height, (0, -1), (1, 0))
