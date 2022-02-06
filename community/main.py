from re import I
import pyglet
from scene import Scene
from scene import __WIDTH__
from scene import __HEIGHT__
from scene import convert_hashColor_to_RGBA
from time import time, sleep
import options
from gamemain import GameMain
import os
import logging

def init_logger():
	log_folder = "logs/"
	log_filename = f"{time()}.logs"
	log_path = os.path.join(log_folder, log_filename)

	if not os.path.isdir(log_folder):
		os.mkdir(log_folder)

	with open(log_path, 'x') as file:
		file.write("[LOGS]\n")

	logging.basicConfig(level=logging.INFO, filename=log_path, 
		format="[%(asctime)s] [%(processName)s/%(threadName)s/%(levelname)s] (%(module)s.py/%(funcName)s) %(message)s")


class InternalConfig:
	def __init__(self, options):
		self.RENDER_DISTANCE = options.RENDER_DISTANCE
		self.FOV = options.FOV
		self.INDIRECT_RENDERING = options.INDIRECT_RENDERING
		self.ADVANCED_OPENGL = options.ADVANCED_OPENGL
		self.CHUNK_UPDATES = options.CHUNK_UPDATES
		self.VSYNC = options.VSYNC
		self.MAX_CPU_AHEAD_FRAMES = options.MAX_CPU_AHEAD_FRAMES
		self.SMOOTH_FPS = options.SMOOTH_FPS
		self.SMOOTH_LIGHTING = options.SMOOTH_LIGHTING
		self.FANCY_TRANSLUCENCY = options.FANCY_TRANSLUCENCY
		self.MIPMAP_TYPE = options.MIPMAP_TYPE
		self.COLORED_LIGHTING = options.COLORED_LIGHTING
		self.ANTIALIASING = options.ANTIALIASING

class IntroScreen(Scene):
	def __init__(self, window):
		super(IntroScreen, self).__init__(window, texture=None, color='#FFFFFF')

		self.intro_text = pyglet.text.Label('Probably can\'t show the', font_size=40, font_name=('Verdana', 'Calibri', 'Arial'), x=self.window.width/2, y=self.window.height/2, multiline=False, width=self.window.width, height=self.window.height, color=(255, 165, 0, 255), anchor_x='center')
		self.has_been_visible_since = time()

	def on_draw(self):
		self.draw()
		self.intro_text.draw()
		if time() - 2 > self.has_been_visible_since:
			self.intro_text.text = 'Mojang Logo due to copyright.'

class MenuScreen(Scene):
	def __init__(self, window):
		image = pyglet.image.load("textures/dirt.png").get_texture()
		self.window = window
		image.height = self.window.height
		image.width = self.window.width

		super(MenuScreen, self).__init__(window, texture=image, color='#000000')

		self.screen_text = pyglet.text.Label('Minecraft', font_size=50, font_name=('Verdana', 'Calibri', 'Arial'), x=self.window.width/2, y=self.window.height/2+170, multiline=False, width=self.window.width, height=self.window.height, color=(100, 100, 100, 255), anchor_x='center')

		button_texture = pyglet.image.load('textures/button.png')
		self.button_sprite = pyglet.sprite.Sprite(button_texture, x=self.window.width/2-button_texture.width, y=self.window.height/2-button_texture.height)
		self.signal_text = pyglet.text.Label('Singelplayer', font_size=10, font_name=('Verdana', 'Calibri', 'Arial'), x=self.button_sprite.x, y=self.button_sprite.y, multiline=False, width=self.button_sprite.width, height=self.button_sprite.height, color=(255, 255, 255, 255), anchor_x='center')

	def on_mouse_press(self, x, y, button, modifiers):
		if x > self.button_sprite.x and x < (self.button_sprite.x + self.button_sprite.width):
			if y > self.button_sprite.y and y < (self.button_sprite.y + self.button_sprite.height):
				self.window.set_scene(GameMain(self.window))

	def on_draw(self):
		self.draw()
		self.screen_text.draw()
		self.button_sprite.draw()
		self.signal_text.draw()

class Window(pyglet.window.Window):
	def __init__(self, refreshrate, **args):
		super().__init__(**args)
		self.refreshrate = refreshrate
		
		# Options
		self.options = InternalConfig(options)

		self.alive = 1

		self.currentScreen = IntroScreen(self)
		self.screen_has_been_shown_since = time()

	def set_scene(self, scene):
		self.currentScreen = scene

	def on_draw(self):
		self.render()

	def on_key_press(self, symbol, mod):
		self.currentScreen.on_key_press(symbol, mod)

	def on_key_release(self, key, modifiers):
		self.currentScreen.on_key_release(key, modifiers)

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		self.currentScreen.on_mouse_motion(x, y, delta_x, delta_y)

	def on_mouse_drag(self, x, y, delta_x, delta_y, buttons, modifiers):
		self.currentScreen.on_mouse_drag(x, y, delta_x, delta_y, buttons, modifiers)

	def on_mouse_press(self, x, y, button, modifiers):
		self.currentScreen.on_mouse_press(x, y, button, modifiers)


	def render(self):
		self.clear()

		if time() - 5 > self.screen_has_been_shown_since and type(self.currentScreen) is not MenuScreen and type(self.currentScreen) is not GameMain:
			self.currentScreen = MenuScreen(self)

		self.currentScreen.on_draw()
		self.flip()

	def on_close(self):
		self.currentScreen.on_close()
		self.alive = 0

	def run(self):
		while self.alive:
			self.render()
			self.dispatch_events()
			pyglet.clock.tick()


if __name__ == "__main__":
	init_logger()
	win = Window(900, width = __WIDTH__, height = __HEIGHT__, caption = "Minecraft clone", resizable = True, vsync = options.VSYNC)
	win.run()