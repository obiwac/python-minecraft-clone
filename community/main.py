import logging
import math
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
import camera
import texture_manager

import world

import hit
import time

import joystick
import keyboard_mouse

class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)
		
		# create shader

		logging.info("Compiling Shaders")
		self.shader = shader.Shader("vert.glsl", "frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"u_TextureArraySampler")
		self.shader.use()

		# create textures
		logging.info("Creating Texture Array")
		self.texture_manager = texture_manager.TextureManager(16, 16, 256)

		# pyglet stuff

		pyglet.clock.schedule(self.update)
		self.mouse_captured = False


		# camera stuff

		logging.info("Setting up camera scene")
		self.camera = camera.Camera(self.shader, self.width, self.height)

		# create world

		self.world = world.World(self.camera, self.texture_manager)

		# misc stuff

		self.holding = 50

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)

		# enable cool stuff

		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)
		gl.glBlendFunc(gl.GL_SRC_COLOR, gl.GL_ONE_MINUS_SRC_COLOR)

		# controls stuff
		self.controls = [0, 0, 0]

		# joystick stuff
		self.joystick_controller = joystick.Joystick_controller(self)

		# mouse and keyboard stuff
		self.keyboard_mouse = keyboard_mouse.Keyboard_Mouse(self)

		# sync status
		self.status = gl.GL_CONDITION_SATISFIED
		self.fence = gl.glFenceSync(gl.GL_SYNC_GPU_COMMANDS_COMPLETE, 0)

		# music stuff
		self.music = [pyglet.media.load(os.path.join("audio/music", file)) for file in os.listdir("audio/music") if os.path.isfile(os.path.join("audio/music", file))]

		self.player = pyglet.media.Player()
		self.player.volume = 0.5

		if len(self.music) > 0:
			self.player.queue(random.choice(self.music))
			self.player.play()
			self.player.standby = False
		else:
			self.player.standby = True

		self.player.next_time = 0

	def update(self, delta_time):
		if pyglet.clock.get_fps() < 20:
			logging.warning(f"Warning: framerate dropping below 20 fps ({pyglet.clock.get_fps()} fps)")

		if not self.mouse_captured:
			self.camera.input = [0, 0, 0]

		if not self.player.source and len(self.music) > 0:
			if not self.player.standby:
				self.player.standby = True
				self.player.next_time = time.time() + random.randint(240, 360)
			elif time.time() >= self.player.next_time:
				self.player.standby = False
				self.player.queue(random.choice(self.music))
				self.player.play()

		self.joystick_controller.update_controller()
		self.camera.update_camera(delta_time)
		self.world.update()
	
	def on_draw(self):
		self.camera.update_matrices()

		self.status = gl.glClientWaitSync(self.fence, gl.GL_SYNC_FLUSH_COMMANDS_BIT, 2985984)
		gl.glDeleteSync(self.fence)

		gl.glClearColor(0.4, 0.7, 1.0, 1.0)
		self.clear()

		self.world.draw()

		self.fence = gl.glFenceSync(gl.GL_SYNC_GPU_COMMANDS_COMPLETE, 0)

	# input functions

	def on_resize(self, width, height):
		logging.info(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.camera.width = width
		self.camera.height = height

class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer = True,
				major_version = 3, minor_version = 3,
				depth_size = 16)
		self.window = Window(config = self.config, width = 854, height = 480, caption = "Minecraft clone", resizable = True, vsync = False)

	def run(self): 
		pyglet.app.run()
		pyglet.app.exit()

def main():
	log_filename = f"logs/{time.time()}.log"
	with open(log_filename, 'x') as file:
		file.write("Logging file\n")

	logging.basicConfig(level=logging.INFO, filename=log_filename, 
		format="[%(asctime)s] [%(processName)s/%(threadName)s/%(levelname)s] (%(module)s.py/%(funcName)s) %(message)s")

	game = Game()
	game.run()

if __name__ == "__main__":
	main()
