import math
import random
import cProfile
import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False

import pyglet.gl as gl
import pyglet.window.mouse

from src.entity.player import SPRINTING_SPEED, WALKING_SPEED, Player
from src.physics.hit import HIT_RANGE, HitRay
from src.renderer.shader import Shader
from src.world import World
from src.chunk.chunk import CHUNK_HEIGHT, CHUNK_WIDTH, CHUNK_LENGTH


class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)

		# create world

		self.world = World()

		# create shader

		self.shader = Shader("shaders/vert.glsl", "shaders/frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"texture_array_sampler")
		self.shader.use()

		# pyglet stuff

		pyglet.clock.schedule_interval(self.update, 1.0 / 60)
		self.mouse_captured = False

		# player stuff

		self.player = Player(self.world, self.shader, self.width, self.height)

		# misc stuff

		self.holding = 44  # 5

	def update(self, delta_time):
		# print(f"FPS: {1.0 / delta_time}")

		if not self.mouse_captured:
			self.player.input = [0, 0, 0]

		self.player.update(delta_time)

	def on_draw(self):
		self.player.update_matrices()

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)

		# draw stuff

		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)

		gl.glClearColor(0.0, 0.0, 0.0, 0.0)
		self.clear()
		self.world.draw()

		gl.glFinish()

	# input functions

	def on_resize(self, width, height):
		print(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.player.view_width = width
		self.player.view_height = height

	def on_mouse_press(self, x, y, button, modifiers):
		if not self.mouse_captured:
			self.mouse_captured = True
			self.set_exclusive_mouse(True)

			return

		# handle breaking/placing blocks

		def hit_callback(current_block, next_block):
			if button == pyglet.window.mouse.RIGHT:
				self.world.try_set_block(current_block, self.holding, self.player.collider)
			elif button == pyglet.window.mouse.LEFT:
				self.world.set_block(next_block, 0)
			elif button == pyglet.window.mouse.MIDDLE:
				self.holding = self.world.get_block_number(next_block)

		x, y, z = self.player.position
		y += self.player.eyelevel

		hit_ray = HitRay(self.world, self.player.rotation, (x, y, z))

		while hit_ray.distance < HIT_RANGE:
			if hit_ray.step(hit_callback):
				break

	def on_mouse_motion(self, x, y, dx, dy):
		if self.mouse_captured:
			sensitivity = 0.004

			self.player.rotation[0] += dx * sensitivity
			self.player.rotation[1] += dy * sensitivity

			self.player.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.player.rotation[1]))

	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
		self.on_mouse_motion(x, y, dx, dy)

	def on_key_press(self, symbol, modifiers):
		if not self.mouse_captured:
			return

		if symbol == pyglet.window.key.D:
			self.player.input[0] += 1
		elif symbol == pyglet.window.key.A:
			self.player.input[0] -= 1
		elif symbol == pyglet.window.key.W:
			self.player.input[2] += 1
		elif symbol == pyglet.window.key.S:
			self.player.input[2] -= 1

		elif symbol == pyglet.window.key.SPACE:
			self.player.input[1] += 1
		elif symbol == pyglet.window.key.LSHIFT:
			self.player.input[1] -= 1
		elif symbol == pyglet.window.key.LCTRL:
			self.player.target_speed = SPRINTING_SPEED

		elif symbol == pyglet.window.key.F:
			self.player.flying = not self.player.flying

		elif symbol == pyglet.window.key.G:
			self.holding = random.randint(1, len(self.world.block_types) - 1)

		elif symbol == pyglet.window.key.O:
			self.world.save.save()

		elif symbol == pyglet.window.key.R:
			# how large is the world?

			max_y = 0

			max_x, max_z = (0, 0)
			min_x, min_z = (0, 0)

			for pos in self.world.chunks:
				x, y, z = pos

				max_y = max(max_y, (y + 1) * CHUNK_HEIGHT)

				max_x = max(max_x, (x + 1) * CHUNK_WIDTH)
				min_x = min(min_x, x * CHUNK_WIDTH)

				max_z = max(max_z, (z + 1) * CHUNK_LENGTH)
				min_z = min(min_z, z * CHUNK_LENGTH)

			# get random X & Z coordinates to teleport the player to

			x = random.randint(min_x, max_x)
			z = random.randint(min_z, max_z)

			# find height at which to teleport to, by finding the first non-air block from the top of the world

			for y in range(CHUNK_HEIGHT - 1, -1, -1):
				if not self.world.get_block_number((x, y, z)):
					continue

				self.player.teleport((x, y + 1, z))
				break

		elif symbol == pyglet.window.key.ESCAPE:
			self.mouse_captured = False
			self.set_exclusive_mouse(False)

	def on_key_release(self, symbol, modifiers):
		if not self.mouse_captured:
			return

		if symbol == pyglet.window.key.D:
			self.player.input[0] -= 1
		elif symbol == pyglet.window.key.A:
			self.player.input[0] += 1
		elif symbol == pyglet.window.key.W:
			self.player.input[2] -= 1
		elif symbol == pyglet.window.key.S:
			self.player.input[2] += 1

		elif symbol == pyglet.window.key.SPACE:
			self.player.input[1] -= 1
		elif symbol == pyglet.window.key.LSHIFT:
			self.player.input[1] += 1
		elif symbol == pyglet.window.key.LCTRL:
			self.player.target_speed = WALKING_SPEED


class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer=True, major_version=3, minor_version=3, depth_size=16)
		self.window = Window(
			config=self.config, width=800, height=600, caption="Minecraft clone", resizable=True, vsync=False
		)

	def run(self):
		pyglet.app.run()


if __name__ == "__main__":
	with cProfile.Profile() as profiler:
		game = Game()
		profiler.dump_stats("stats.prof")

	game.run()
