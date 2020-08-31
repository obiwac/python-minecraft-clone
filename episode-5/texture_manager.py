import ctypes
import pyglet

import pyglet.gl as gl

class Texture_manager:
	def __init__(self, texture_width, texture_height, max_textures):
		self.texture_width = texture_width
		self.texture_height = texture_height

		self.max_textures = max_textures

		self.textures = [] # an array to keep track of the textures we've already added

		self.texture_array = gl.GLuint(0) # create our texture array
		gl.glGenTextures(1, self.texture_array)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array)

		gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST) # disable texture filtering for magnification (return the texel that's nearest to the fragment's texture coordinate)

		gl.glTexImage3D( # set the dimensions of our texture array
			gl.GL_TEXTURE_2D_ARRAY, 0, gl.GL_RGBA,
			self.texture_width, self.texture_height, self.max_textures,
			0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
	
	def generate_mipmaps(self):
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array) # make sure our texture is bound
		gl.glGenerateMipmap(gl.GL_TEXTURE_2D_ARRAY) # generate mipmaps for our texture
	
	def add_texture(self, texture):
		if not texture in self.textures: # check to see if our texture has not yet been added
			self.textures.append(texture) # add it to our textures list if not

			texture_image = pyglet.image.load(f"textures/{texture}.png").get_image_data() # load and get the image data of the texture we want
			gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_array) # make sure our texture array is bound

			gl.glTexSubImage3D( # paste our texture's image data in the appropriate spot in our texture array
				gl.GL_TEXTURE_2D_ARRAY, 0,
				0, 0, self.textures.index(texture),
				self.texture_width, self.texture_height, 1,
				gl.GL_RGBA, gl.GL_UNSIGNED_BYTE,
				texture_image.get_data("RGBA", texture_image.width * 4))