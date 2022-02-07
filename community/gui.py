import pyglet

class GuiButton():
	def __init__(self, on_click_func, window, x, y, text, locked=False):
		self.locked = locked
		self.func = on_click_func
		self.window = window
		self.text = text
		self.hovered=False

		self.button_texture = pyglet.image.load('textures/button.png')
		self.button_texture_hover = pyglet.image.load('textures/button_hover.png')
		self.button_texture_locked = pyglet.image.load('textures/button_locked.png')

		H_ratio = 1.5
		W_ratio = 1.2

		self.font_size = self.button_texture.height/2
		self.x = x-self.button_texture.width/2
		self.y = y-self.button_texture.height/2

		self.button_sprite = pyglet.sprite.Sprite(self.button_texture, x=self.x, y=self.y)
		self.button_sprite.scale_x = W_ratio
		self.button_sprite.scale_y = H_ratio
		self.font_size = self.button_sprite.height/2
		self.x = x-self.button_sprite.width/2
		self.y = y-self.button_sprite.height/2
		self.button_sprite.x = self.x
		self.button_sprite.y = self.y

		self.button_sprite_hover = pyglet.sprite.Sprite(self.button_texture_hover, x=self.x, y=self.y)
		self.button_sprite_hover.scale_x = W_ratio
		self.button_sprite_hover.scale_y = H_ratio

		self.button_sprite_locked = pyglet.sprite.Sprite(self.button_texture_locked, x=self.x, y=self.y)
		self.button_sprite_locked.scale_x = W_ratio
		self.button_sprite_locked.scale_y = H_ratio

		self.button_text = pyglet.text.Label(text, font_size=self.font_size, font_name=('Verdana', 'Calibri', 'Arial'), x=self.button_sprite.x+self.button_sprite.width/2, y=(self.button_sprite.y+self.button_sprite.height/2)-self.font_size/2, multiline=False, width=self.button_sprite.width, height=self.button_sprite.height, color=(255, 255, 255, 255), anchor_x='center')

	def draw(self):
		if not self.locked:
			if self.hovered:
				self.button_sprite_hover.draw()
			else:
				self.button_sprite.draw()
		else:
			self.button_sprite_locked.draw()
		self.button_text.draw()

	def on_mouse_press(self, x, y, button, modifiers):
		if not self.locked:
			if x > self.button_sprite.x and x < (self.button_sprite.x + self.button_sprite.width):
				if y > self.button_sprite.y and y < (self.button_sprite.y + self.button_sprite.height):
					self.func()
	
	def on_mouse_motion(self, x, y, delta_x, delta_y):
		if not self.locked:
			self.hovered = False
			if x > self.button_sprite.x and x < (self.button_sprite.x + self.button_sprite.width):
				if y > self.button_sprite.y and y < (self.button_sprite.y + self.button_sprite.height):
					self.hovered = True