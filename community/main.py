import sys
import logging
import random
import time
import os

import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = True
pyglet.options["search_local_libs"] = True
pyglet.options["audio"] = ("openal", "pulse", "directsound", "xaudio2", "silent")

import pyglet.gl as gl
import shader
import camera
import texture_manager

import world

import options
import time

import joystick
import keyboard_mouse


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

		# camera stuff

		logging.info("Setting up camera scene")
		self.camera = camera.Camera(self.shader, self.width, self.height)

		# create world

		self.world = world.World(self.shader, self.camera, self.texture_manager)

		# pyglet stuff

		pyglet.clock.schedule(self.update)
		pyglet.clock.schedule_interval(self.tick, 1 / 60)
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
		
	def toggle_fullscreen(self):
		self.set_fullscreen(not self.fullscreen)

	def on_close(self):
		logging.info("Deleting player")
		self.player.delete()

		pyglet.app.exit() # Closes the game

	def tick(self, delta_time):
		if not self.player.source and len(self.music) > 0:
			if not self.player.standby:
				self.player.standby = True
				self.player.next_time = time.time() + random.randint(240, 360)
			elif time.time() >= self.player.next_time:
				self.player.standby = False
				self.player.queue(random.choice(self.music))
				self.player.play()
		
		self.world.tick(delta_time)

	def update(self, delta_time):
		if not self.mouse_captured:
			self.camera.input = [0, 0, 0]

		self.joystick_controller.update_controller()
		self.camera.update_camera(delta_time)
		
	
	def on_draw(self):
		self.shader.use()
		self.camera.update_matrices()
		
		self.clear()

		self.world.draw()

		# Clear GL global state
		if options.FPS_DISPLAY:
			gl.glUseProgram(0) 
			gl.glBindVertexArray(0)
			self.fps_display.draw()

	# input functions

	def on_resize(self, width, height):
		logging.info(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.camera.width = width
		self.camera.height = height
		self.fps_display.label.y = self.height - 30

class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer = True,
				major_version = 3, minor_version = 3,
				depth_size = 16, forward_compatible = True)
		self.window = Window(config = self.config, width = 852, height = 480, caption = "Minecraft clone", resizable = True, vsync = False)

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
