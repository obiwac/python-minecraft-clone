import pyglet

class GuiButton():
	def __init__(self, on_click_func, window, x, y, text):
		self.func = on_click_func
		self.window = window
		self.text = text
		button_texture = pyglet.image.load('textures/button.png')
		self.font_size = button_texture.height/2
		self.x = x-button_texture.width/2
		self.y = y-button_texture.height/2
		self.button_sprite = pyglet.sprite.Sprite(button_texture, x=self.x, y=self.y)
		self.button_text = pyglet.text.Label(text, font_size=self.font_size, font_name=('Verdana', 'Calibri', 'Arial'), x=self.button_sprite.x+button_texture.width/2, y=(self.button_sprite.y+button_texture.height/2)-self.font_size/2, multiline=False, width=self.button_sprite.width, height=self.button_sprite.height, color=(255, 255, 255, 255), anchor_x='center')

	def draw(self):
		self.button_sprite.draw()
		self.button_text.draw()

	def on_mouse_press(self, x, y, button, modifiers):
		if x > self.button_sprite.x and x < (self.button_sprite.x + self.button_sprite.width):
			if y > self.button_sprite.y and y < (self.button_sprite.y + self.button_sprite.height):
				self.func()
	