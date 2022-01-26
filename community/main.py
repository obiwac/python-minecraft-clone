import sys
import logging
import random
import time
import os

import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False
pyglet.options["search_local_libs"] = True
pyglet.options["audio"] = ("openal", "pulse", "directsound", "xaudio2", "silent")

import pyglet.gl as gl
import shader
import player
import texture_manager

import world

import options
import time

import joystick
import keyboard_mouse
from collections import deque

class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)

		if options.INDIRECT_RENDERING and not gl.gl_info.have_version(4, 2):
			raise RuntimeError("""Indirect Rendering is not supported on your hardware
			This feature is only supported on OpenGL 4.2+, but your driver doesnt seem to support it, 
			Please disable "INDIRECT_RENDERING" in options.py""")

		print(f"OpenGL Version: {gl.gl_info.get_version()}")
	
		# FPS display
		if options.FPS_DISPLAY:
			self.fps_display = pyglet.window.FPSDisplay(self)
			self.fps_display.label.color = (255, 255, 255, 255)
			self.fps_display.label.y = self.height - 30
		
		# create shader

		logging.info("Compiling Shaders")
		if not options.COLORED_LIGHTING:
			self.shader = shader.Shader("shaders/alpha_lighting/vert.glsl", "shaders/alpha_lighting/frag.glsl")
		else:
			self.shader = shader.Shader("shaders/colored_lighting/vert.glsl", "shaders/colored_lighting/frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"u_TextureArraySampler")
		self.shader.use()

		# create textures
		logging.info("Creating Texture Array")
		self.texture_manager = texture_manager.TextureManager(16, 16, 256)

		# create world

		self.world = world.World(self.shader, None, self.texture_manager)

		# player stuff

		logging.info("Setting up player & camera")
		self.player = player.Player(self.world, self.shader, self.width, self.height)
		self.world.player = self.player

		# pyglet stuff
		pyglet.clock.schedule(self.player.update_interpolation)
		pyglet.clock.schedule_interval(self.update, 1 / 60)
		self.mouse_captured = False

		# misc stuff

		self.holding = 50

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)

		# enable cool stuff

		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)
		gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

		# controls stuff
		self.controls = [0, 0, 0]

		# joystick stuff
		self.joystick_controller = joystick.Joystick_controller(self)

		# mouse and keyboard stuff
		self.keyboard_mouse = keyboard_mouse.Keyboard_Mouse(self)

		# music stuff
		logging.info("Loading audio")
		try:
			self.music = [pyglet.media.load(os.path.join("audio/music", file)) for file in os.listdir("audio/music") if os.path.isfile(os.path.join("audio/music", file))]
		except:
			self.music = []

		self.media_player = pyglet.media.Player()
		self.media_player.volume = 0.5

		if len(self.music) > 0:
			self.media_player.queue(random.choice(self.music))
			self.media_player.play()
			self.media_player.standby = False
		else:
			self.media_player.standby = True

		self.media_player.next_time = 0

		self.fences = deque()
		
	def toggle_fullscreen(self):
		self.set_fullscreen(not self.fullscreen)

	def on_close(self):
		logging.info("Deleting media player")
		self.media_player.delete()
		for fence in self.fences:
			gl.glDeleteSync(fence)

	def update(self, delta_time):
		if not self.media_player.source and len(self.music) > 0:
			if not self.media_player.standby:
				self.media_player.standby = True
				self.media_player.next_time = time.time() + random.randint(240, 360)
			elif time.time() >= self.media_player.next_time:
				self.media_player.standby = False
				self.media_player.queue(random.choice(self.music))
				self.media_player.play()

		if not self.mouse_captured:
			self.player.input = [0, 0, 0]

		self.joystick_controller.update_controller()
		self.player.update(delta_time)

		self.world.tick(delta_time)

	def on_draw(self):
		self.shader.use()
		self.player.update_matrices()

		while len(self.fences) > options.MAX_PRERENDERED_FRAMES:
			fence = self.fences.popleft()
			gl.glClientWaitSync(fence, gl.GL_SYNC_FLUSH_COMMANDS_BIT, 2147483647)
			gl.glDeleteSync(fence)

		self.clear()
		self.world.prepare_rendering()
		self.world.draw()

		self.fences.append(gl.glFenceSync(gl.GL_SYNC_GPU_COMMANDS_COMPLETE, 0))

		# Clear GL global state
		if options.FPS_DISPLAY:
			self.fps_display.label.text = f"{round(pyglet.clock.get_fps())} fps  C: {len(self.world.visible_chunks)}"
			gl.glUseProgram(0) 
			gl.glBindVertexArray(0)
			self.fps_display.draw()


	# input functions

	def on_resize(self, width, height):
		logging.info(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.player.view_width = width
		self.player.view_height = height
		if options.FPS_DISPLAY:
			self.fps_display.label.y = self.height - 30

class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer = True,
				major_version = 3, minor_version = 3,
				depth_size = 16)
		self.window = Window(config = self.config, width = 852, height = 480, caption = "Minecraft clone", resizable = True, vsync = options.VSYNC)

	def run(self): 
		pyglet.app.run()



def init_logger():
	log_folder = "logs/"
	log_filename = f"{time.time()}.log"
	log_path = os.path.join(log_folder, log_filename)

	if not os.path.isdir(log_folder):
		os.mkdir(log_folder)

	with open(log_path, 'x') as file:
		file.write("[LOGS]\n")

	logging.basicConfig(level=logging.INFO, filename=log_path, 
		format="[%(asctime)s] [%(processName)s/%(threadName)s/%(levelname)s] (%(module)s.py/%(funcName)s) %(message)s")




def main():
	init_logger()
	game = Game()
	game.run()

if __name__ == "__main__":
	main()
