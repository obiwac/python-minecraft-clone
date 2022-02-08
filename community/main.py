from re import I, S
import pyglet
from scene import Scene
from scene import __WIDTH__
from scene import __HEIGHT__
from scene import convert_hashColor_to_RGBA
from time import time, sleep
from gamemain import GameMain
from gui import GuiButton
import options
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

		image = pyglet.image.load("textures/logo.png")
		self.logo = pyglet.sprite.Sprite(image, x=0, y=0)
		H_ratio = 1.5
		W_ratio = 1.2
		self.logo.scale_x = W_ratio
		self.logo.scale_y = H_ratio
		self.logo.x = (self.window.width/2)-self.logo.width/2
		self.logo.y = self.window.height-100

		self.singleplayer = GuiButton(self.on_singleplayer, self.window, self.window.width/2, self.window.height/2+35, 'Singleplayer')
		self.multiplayer = GuiButton(None, self.window, self.window.width/2, self.window.height/2, 'Multiplayer', locked=True)
		self.options = GuiButton(None, self.window, self.window.width/2, self.window.height/2-35, 'Options', locked=True)

	def on_singleplayer(self):
		self.window.set_scene(GameMain(self.window))

	def on_mouse_press(self, x, y, button, modifiers):
		self.singleplayer.on_mouse_press(x, y, button, modifiers)
		self.multiplayer.on_mouse_press(x, y, button, modifiers)
		self.options.on_mouse_press(x, y, button, modifiers)

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		self.singleplayer.on_mouse_motion(x, y, delta_x, delta_y)
		self.multiplayer.on_mouse_motion(x, y, delta_x, delta_y)
		self.options.on_mouse_motion(x, y, delta_x, delta_y)

	def on_draw(self):
		self.draw()
		self.logo.draw()
		self.singleplayer.draw()
		self.multiplayer.draw()
		self.options.draw()

class Window(pyglet.window.Window):
	def __init__(self, refreshrate, **args):
		super().__init__(**args)
		self.refreshrate = refreshrate
		
		# Options
		self.options = InternalConfig(options)

		self.alive = 1

		self.currentScreen = IntroScreen(self)
		self.screen_has_been_shown_since = time()
		self.not_first = 0

	def show_menu(self):
		self.currentScreen = MenuScreen(self)

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

	# def on_resize(self, width, height):
	# 	if self.not_first > 5:
	# 		print("s")
	# 		self.not_first = 0
	# 		self.currentScreen.on_resize(width, height)
	# 	self.not_first += 1

	def run(self):
		while self.alive:
			self.render()
			self.dispatch_events()
			pyglet.clock.tick()


if __name__ == "__main__":
	init_logger()
	win = Window(900, width = __WIDTH__, height = __HEIGHT__, caption = "Minecraft clone", resizable = True, vsync = options.VSYNC)
	win.run()