from __future__ import annotations

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

import imgui
from imgui.integrations.pyglet import create_renderer


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


class Scene():
	def __init__(self, window: Window) -> None:
		self.window = window

	def on_close(self):
		pass

	def on_draw(self):
		pass

	def on_resize(self, width, height):
		pass

	def update(self, delta_time):
		pass

	def update_ui(self):
		pass


class GameScene(Scene):
	def __init__(self, window: Window, path) -> None:
		super().__init__(window)
		logging.info("Loading game scene")

		# F3 Debug Screen

		self.show_f3 = False

		# create textures
		logging.info("Creating Texture Array")
		self.texture_manager = texture_manager.TextureManager(16, 16, 256)

		# create shader

		logging.info("Compiling Shaders")
		if not self.window.options.COLORED_LIGHTING:
			self.shader = shader.Shader("shaders/alpha_lighting/vert.glsl", "shaders/alpha_lighting/frag.glsl")
		else:
			self.shader = shader.Shader("shaders/colored_lighting/vert.glsl", "shaders/colored_lighting/frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"u_TextureArraySampler")
		self.shader.use()

		# create world

		self.world = world.World(path, self.shader, None, self.texture_manager, self.window.options)

		# player stuff

		logging.info("Setting up player & camera")
		self.player = player.Player(self.world, self.shader, self.window.width, self.window.height)
		self.world.player = self.player

		# pyglet stuff
		pyglet.clock.schedule(self.player.update_interpolation)

		# misc stuff

		self.holding = 50

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)

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

	def on_close(self):
		super().on_close()
		logging.info("Deleting media player")
		self.media_player.delete()
		for fence in self.window.fences:
			gl.glDeleteSync(fence)

	def update_f3(self):
		"""Update the F3 debug screen content"""
		imgui.set_next_window_position(5, 5)
		imgui.set_next_window_bg_alpha(0.175)
		imgui.get_io().ini_file_name = None

		player_chunk_pos = world.get_chunk_position(self.player.position)
		player_local_pos = world.get_local_position(self.player.position)
		chunk_count = len(self.world.chunks)
		visible_chunk_count = len(self.world.visible_chunks)
		quad_count = sum(chunk.mesh_quad_count for chunk in self.world.chunks.values())
		visible_quad_count = sum(chunk.mesh_quad_count for chunk in self.world.visible_chunks)

		if imgui.begin(
			"F3 Debug Screen",
			self.show_f3,
			flags=
			imgui.WINDOW_NO_DECORATION |
			imgui.WINDOW_ALWAYS_AUTO_RESIZE |
			imgui.WINDOW_NO_SAVED_SETTINGS |
			imgui.WINDOW_NO_FOCUS_ON_APPEARING |
			imgui.WINDOW_NO_NAV
		):
			imgui.text(f"""
{round(1 / self.window.delta_time)} FPS ({self.world.chunk_update_counter} Chunk Updates) {"inf" if not self.window.options.VSYNC else "vsync"}{"ao" if self.window.options.SMOOTH_LIGHTING else ""}
C: {visible_chunk_count} / {chunk_count} pC: {self.world.pending_chunk_update_count} pU: {len(self.world.chunk_building_queue)} aB: {chunk_count}
Client Singleplayer @{round(self.window.delta_time * 1000)} ms tick {round(1 / self.window.delta_time)} TPS

XYZ: ( X: {round(self.player.position[0], 3)} / Y: {round(self.player.position[1], 3)} / Z: {round(self.player.position[2], 3)} )
Block: {self.player.rounded_position[0]} {self.player.rounded_position[1]} {self.player.rounded_position[2]}
Chunk: {player_local_pos[0]} {player_local_pos[1]} {player_local_pos[2]} in {player_chunk_pos[0]} {player_chunk_pos[1]} {player_chunk_pos[2]}
Light: {max(self.world.get_light(self.player.rounded_position), self.world.get_skylight(self.player.rounded_position))} ({self.world.get_skylight(self.player.rounded_position)} sky, {self.world.get_light(self.player.rounded_position)} block)

{self.window.system_info}

Renderer: {"OpenGL 3.3 VAOs" if not self.window.options.INDIRECT_RENDERING else "OpenGL 4.0 VAOs Indirect"} {"Conditional" if self.window.options.ADVANCED_OPENGL else ""}
Buffers: {chunk_count}
Vertex Data: {round(quad_count * 28 * ctypes.sizeof(gl.GLfloat) / 1048576, 3)} MiB ({quad_count} Quads)
Visible Quads: {visible_quad_count}
Buffer Uploading: Direct (glBufferSubData)
			""")
		imgui.end()

	def update(self, delta_time):
		super().update(delta_time)
		if not self.media_player.source and len(self.music) > 0:
			if not self.media_player.standby:
				self.media_player.standby = True
				self.media_player.next_time = time.time() + random.randint(240, 360)
			elif time.time() >= self.media_player.next_time:
				self.media_player.standby = False
				self.media_player.queue(random.choice(self.music))
				self.media_player.play()

		if not self.window.mouse_captured:
			self.player.input = [0, 0, 0]

		self.joystick_controller.update_controller()
		self.player.update(delta_time)

		self.world.tick(delta_time)

	def update_ui(self):
		super().update_ui()
		if self.show_f3:
			self.update_f3()

	def on_draw(self):
		super().on_draw()
		gl.glEnable(gl.GL_DEPTH_TEST)
		self.shader.use()
		self.player.update_matrices()

		while len(self.window.fences) > self.window.options.MAX_CPU_AHEAD_FRAMES:
			fence = self.window.fences.popleft()
			gl.glClientWaitSync(fence, gl.GL_SYNC_FLUSH_COMMANDS_BIT, 2147483647)
			gl.glDeleteSync(fence)

		self.window.clear()
		self.world.prepare_rendering()
		self.world.draw()

		# CPU - GPU Sync
		if not self.window.options.SMOOTH_FPS:
			# self.fences.append(gl.glFenceSync(gl.GL_SYNC_GPU_COMMANDS_COMPLETE, 0))
			# Broken in pyglet 2; glFenceSync is missing
			pass
		else:
			gl.glFinish()

	def on_resize(self, width, height):
		super().on_resize(width, height)
		logging.info(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.player.view_width = width
		self.player.view_height = height


class MenuScene(Scene):
	def __init__(self, window: Window) -> None:
		super().__init__(window)
		self.texture_manager = texture_manager.TextureManager(0, 0, 0)

		self.icon = self.texture_manager.load_texture("dirt")
		self.logo = self.texture_manager.load_texture("logo")

	def on_draw(self):
		super().on_draw()
		gl.glEnable(gl.GL_TEXTURE_2D)
		self.window.clear()

	def update_ui(self):
		super().update_ui()
		io = imgui.get_io()
		imgui.set_next_window_size(io.display_size.x, io.display_size.y)
		imgui.set_next_window_position(0, 0)
		imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0.0)
		imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (0.0, 0.0))

		if imgui.begin(
			"MCPY",
			True,
			flags=
			imgui.WINDOW_NO_DECORATION |
			imgui.WINDOW_ALWAYS_AUTO_RESIZE |
			imgui.WINDOW_NO_SAVED_SETTINGS |
			imgui.WINDOW_NO_NAV
		):
			# Get the draw list
			draw_list = imgui.get_window_draw_list()

			# Tile the image across the window
			for x in range(0, int(io.display_size.x), self.icon[1]):
				for y in range(0, int(io.display_size.y), self.icon[2]):
					draw_list.add_image(self.icon[0].id, (x, y), (x + self.icon[1], y + self.icon[2]))

			# Draw a semi-transparent overlay to darken the background
			overlay_color = imgui.get_color_u32_rgba(0, 0, 0, 0.75)
			draw_list.add_rect_filled(0, 0, io.display_size.x, io.display_size.y, overlay_color)


			# Calculate the position to horizontally center the image
			image_width = self.logo[1] / 2.5
			image_height = self.logo[2] / 2.5

			# Set the cursor position to the calculated center position
			imgui.set_cursor_pos(((io.display_size.x - image_width) / 2, 50))

			# Draw the image at the calculated position
			imgui.image(self.logo[0].id, image_width, image_height, (0, 1), (1, 0))

			# Calculate the position to horizontally center the buttons
			button_width = 300  # Adjust button width as needed
			button_height = 30  # Adjust button height as needed
			button_x = (io.display_size.x - button_width) / 2
			button_y = imgui.get_cursor_pos().y + image_height - 50

			# Set the cursor position to the calculated center position for buttons
			imgui.set_cursor_pos((button_x, button_y))

			# Add buttons under the logo
			if imgui.button("Singleplayer", width=button_width, height=button_height):
				# Handle button 1 click
				pass

			imgui.set_cursor_pos((button_x, imgui.get_cursor_pos().y + 10))

			if imgui.button("Multiplayer", width=button_width, height=button_height):
				# Handle button 2 click
				pass

			imgui.set_cursor_pos((button_x, imgui.get_cursor_pos().y + 10))

			if imgui.button("Play tutorial level", width=button_width, height=button_height):
				scene = GameScene(self.window, "save")
				self.window.push_scene(scene)

			imgui.set_cursor_pos((button_x, imgui.get_cursor_pos().y + 20))

			if imgui.button("Options", width=button_width, height=button_height):
				# Handle button 2 click
				pass

			text = "Copyright MCPY contributors. MCPY is licensed under the MIT."
			# Calculate the position to render the text in the bottom right
			text_width, text_height = imgui.calc_text_size(text)
			text_x = io.display_size.x - text_width
			text_y = io.display_size.y - text_height

			# Set the cursor position to the calculated position for the text
			imgui.set_cursor_pos((text_x, text_y))

			# Render the text in the bottom right
			imgui.text(text)
		imgui.end()
		imgui.pop_style_var()
		imgui.pop_style_var()


class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)

		# Options
		self.options = InternalConfig(options)

		if self.options.INDIRECT_RENDERING and not gl.gl_info.have_version(4, 2):
			raise RuntimeError("""Indirect Rendering is not supported on your hardware
			This feature is only supported on OpenGL 4.2+, but your driver doesnt seem to support it, 
			Please disable "INDIRECT_RENDERING" in options.py""")
	
		self.system_info = f"""Python: {platform.python_implementation()} {platform.python_version()}
System: {platform.machine()} {platform.system()} {platform.release()} {platform.version()}
CPU: {platform.processor()}
Display: {gl.gl_info.get_renderer()} 
{gl.gl_info.get_version()}"""

		logging.info(f"System Info: {self.system_info}")

		# set scene
		self.scenes = [MenuScene(self)]
		self.current_scene = self.scenes[0]
		self.go_next_scene = False
		self.mouse_captured = False

		# enable cool stuff

		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)
		gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
		
		if self.options.ANTIALIASING:
			gl.glEnable(gl.GL_MULTISAMPLE)
			gl.glEnable(gl.GL_SAMPLE_ALPHA_TO_COVERAGE)
			gl.glSampleCoverage(0.5, gl.GL_TRUE)

		# GPU command syncs
		self.fences = deque()

		# ui stuff
		imgui.create_context()
		self.impl = create_renderer(self)
		self.delta_time = 1
		pyglet.clock.schedule_interval(self.update, 1 / 60)
		
	def toggle_fullscreen(self):
		self.set_fullscreen(not self.fullscreen)

	def on_close(self):
		self.current_scene.on_close()
		super().on_close()

	def update_ui(self):
		self.current_scene.update_ui()

	def update(self, delta_time):
		"""Every tick"""
		self.impl.process_inputs()
		self.delta_time = delta_time
		self.current_scene.update(delta_time)
		self.try_next_scene()

	def on_draw(self):
		self.current_scene.on_draw()
		
		# Handle UI
		imgui.new_frame()
		self.update_ui()
		imgui.render()
		self.impl.render(imgui.get_draw_data())

	# input functions

	def on_resize(self, width, height):
		self.current_scene.on_resize(width, height)

	# scene functions

	def push_scene(self, scene):
		self.scenes.append(scene)
		self.go_next_scene = True

	def pop_scene(self):
		return self.scenes.pop(len(self.scenes) - 1)

	def try_next_scene(self):
		if self.go_next_scene:
			try:
				scene = self.scenes[len(self.scenes) - 1]
				if scene != self.current_scene:
					self.current_scene = self.pop_scene()
					self.go_next_scene = False
			except IndexError:
				pass # do nothing because there are no other scenes to switch to.


class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer = True,
				major_version = 3, minor_version = 3,
				depth_size = 16, sample_buffers=bool(options.ANTIALIASING), samples=options.ANTIALIASING)
		self.window = Window(config = self.config, width = 852, height = 480, caption = "Minecraft clone", resizable = True, vsync = options.VSYNC)

	def run(self): 
		pyglet.app.run(interval = 0)


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
