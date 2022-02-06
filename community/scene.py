import pyglet

__WIDTH__ = 852
__HEIGHT__ = 480

def convert_hashColor_to_RGBA(color):
	if '#' in color:
		c = color.lstrip("#")
		c = max(6-len(c),0)*"0" + c
		r = int(c[:2], 16)
		g = int(c[2:4], 16)
		b = int(c[4:], 16)
		color = (r,g,b,255)
	return color

class Scene(pyglet.sprite.Sprite):
	def __init__(self, window, texture=None, color="#000000"):
		self.window = window
		width = window.width
		height = window.height
		x = width/2
		y = height/2
		if texture is None:
			self.texture = pyglet.image.SolidColorImagePattern(convert_hashColor_to_RGBA(color)).create_image(width,height)
		else:
			self.texture = texture
		super(Scene, self).__init__(self.texture)

		self.image.anchor_x = self.image.width / 2
		self.image.anchor_y = self.image.height / 2
		self.x = x
		self.y = y

	def on_draw(self):
		self.draw()

	def on_close(self):
		pass

	def on_key_press(self, symbol, mod):
		pass

	def on_key_release(self, key, modifiers):
		pass

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		pass

	def on_mouse_drag(self, x, y, delta_x, delta_y, buttons, modifiers):
		pass

	def on_mouse_press(self, x, y, button, modifiers):
		pass

	def on_resize(self, width, height):
		self.image.width = width
		self.image.height = height
		self.image.anchor_x = self.image.width / 2
		self.image.anchor_y = self.image.height / 2