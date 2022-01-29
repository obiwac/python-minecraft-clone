import platform
import ctypes
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
	
		# F3 Debug Screen

		self.show_f3 = False
		self.f3 = pyglet.text.Label("", x = 10, y = self.height - 10,
				font_size = 16,
				color = (255, 255, 255, 255),
				width = self.width // 3,
				multiline = True
		)
		
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
		
		if options.ANTIALIASING:
			gl.glEnable(gl.GL_MULTISAMPLE)
			gl.glEnable(gl.GL_SAMPLE_ALPHA_TO_COVERAGE)
			gl.glSampleCoverage(0.5, gl.GL_TRUE)

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

		# GPU command syncs
		self.fences = deque()
		
	def toggle_fullscreen(self):
		self.set_fullscreen(not self.fullscreen)

	def on_close(self):
		logging.info("Deleting media player")
		self.media_player.delete()
		for fence in self.fences:
			gl.glDeleteSync(fence)

		pyglet.app.exit()

	def update_f3(self, delta_time):
		"""Update the F3 debug screen content"""

		player_chunk_pos = world.get_chunk_position(self.player.position)
		player_local_pos = world.get_local_position(self.player.position)
		chunk_count = len(self.world.chunks)
		visible_chunk_count = len(self.world.visible_chunks)
		quad_count = sum(chunk.mesh_quad_count for chunk in self.world.chunks.values())
		visible_quad_count = sum(chunk.mesh_quad_count for chunk in self.world.visible_chunks)
		self.f3.text = \
f"""
{round(pyglet.clock.get_fps())} FPS ({self.world.chunk_update_counter} Chunk Updates)
C: {visible_chunk_count} / {chunk_count} pC: {self.world.pending_chunk_update_count} pU: {len(self.world.chunk_building_queue)} aB: {chunk_count}
Client Singleplayer @{round(delta_time * 1000)} ms tick {round(1 / delta_time)} TPS

XYZ: ( X: {round(self.player.position[0], 3)} / Y: {round(self.player.position[1], 3)} / Z: {round(self.player.position[2], 3)} )
Block: {self.player.rounded_position[0]} {self.player.rounded_position[1]} {self.player.rounded_position[2]}
Chunk: {player_local_pos[0]} {player_local_pos[1]} {player_local_pos[2]} in {player_chunk_pos[0]} {player_chunk_pos[1]} {player_chunk_pos[2]}
Light: {max(self.world.get_light(self.player.rounded_position), self.world.get_skylight(self.player.rounded_position))} ({self.world.get_skylight(self.player.rounded_position)} sky, {self.world.get_light(self.player.rounded_position)} block)

Python: {platform.python_implementation()} {platform.python_version()}
System: {platform.machine()} {platform.system()} {platform.release()} {platform.version()}
CPU: {platform.processor()}
Display: {gl.gl_info.get_renderer()} 
{gl.gl_info.get_version()}

Renderer: {"OpenGL 3.3 VAOs" if not options.INDIRECT_RENDERING else "OpenGL 4.0 VAOs Indirect"} {"Conditional" if options.ADVANCED_OPENGL else ""}
Buffers: {chunk_count}
Vertex Data: {round(quad_count * 28 * ctypes.sizeof(gl.GLfloat) / 1048576, 3)} MiB ({quad_count} Quads)
Visible Quads: {visible_quad_count}
Buffer Uploading: Direct (glBufferSubData)
"""

	def update(self, delta_time):
		"""Every tick"""
		if self.show_f3:
			self.update_f3(delta_time)

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
		gl.glEnable(gl.GL_DEPTH_TEST)
		self.shader.use()
		self.player.update_matrices()

		while len(self.fences) > options.MAX_PRERENDERED_FRAMES:
			fence = self.fences.popleft()
			gl.glClientWaitSync(fence, gl.GL_SYNC_FLUSH_COMMANDS_BIT, 2147483647)
			gl.glDeleteSync(fence)

		self.clear()
		self.world.prepare_rendering()
		self.world.draw()

		# Draw the F3 Debug screen
		if self.show_f3:
			self.draw_f3()

		# CPU - GPU Sync
		if not options.SMOOTH_FPS:
			self.fences.append(gl.glFenceSync(gl.GL_SYNC_GPU_COMMANDS_COMPLETE, 0))
		else:
			gl.glFinish()

	def draw_f3(self):
		"""Draws the f3 debug screen. Current uses the fixed-function pipeline since pyglet labels uses it"""
		gl.glDisable(gl.GL_DEPTH_TEST)
		gl.glUseProgram(0) 
		gl.glBindVertexArray(0)
		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPushMatrix()
		gl.glLoadIdentity()

		gl.glMatrixMode(gl.GL_PROJECTION)
		gl.glPushMatrix()
		gl.glLoadIdentity()
		gl.glOrtho(0, self.width, 0, self.height, -1, 1)

		self.f3.draw()

		gl.glPopMatrix()

		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPopMatrix()


	# input functions

	def on_resize(self, width, height):
		logging.info(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.player.view_width = width
		self.player.view_height = height
		self.f3.y = self.height - 10
		self.f3.width = self.width // 3

class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer = True,
				major_version = 3, minor_version = 3,
				depth_size = 16, sample_buffers=bool(options.ANTIALIASING), samples=options.ANTIALIASING)
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
