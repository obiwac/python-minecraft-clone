
import math
import random
import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False

import pyglet.gl as gl

import player
import mob

import world

import hit

class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)

		# create world

		self.world = world.World(self.width, self.height)

		# pyglet stuff

		pyglet.clock.schedule_interval(self.update, 1.0 / 60)
		self.mouse_captured = False

		# misc stuff

		self.frame = 0
		self.holding = 19 # 5

	def update(self, delta_time):
		self.frame += 1
		# print(f"FPS: {1.0 / delta_time}")

		if not self.mouse_captured:
			self.world.player.input = [0, 0, 0]

		self.world.player.update(delta_time)

		# update other entities

		for entity in self.world.entities:
			entity.update(delta_time)

	def on_draw(self):
		self.world.player.update_matrices()

		# draw stuff

		gl.glEnable(gl.GL_DEPTH_TEST)

		gl.glClearColor(0.0, 0.0, 0.0, 0.0)
		self.clear()

		self.world.draw()

		gl.glFinish()

	# input functions

	def on_resize(self, width, height):
		print(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.world.player.view_width = width
		self.world.player.view_height = height

	def on_mouse_press(self, x, y, button, modifiers):
		if not self.mouse_captured:
			self.mouse_captured = True
			self.set_exclusive_mouse(True)

			return

		# handle breaking/placing blocks

		def hit_callback(current_block, next_block):
			if button == pyglet.window.mouse.RIGHT: self.world.try_set_block(current_block, self.holding, self.world.player.collider)
			elif button == pyglet.window.mouse.LEFT: self.world.set_block(next_block, 0)
			elif button == pyglet.window.mouse.MIDDLE: self.holding = self.world.get_block_number(next_block)

		x, y, z = self.world.player.position
		y += self.world.player.eyelevel

		hit_ray = hit.Hit_ray(self.world, self.world.player.rotation, (x, y, z))

		while hit_ray.distance < hit.HIT_RANGE:
			if hit_ray.step(hit_callback):
				break

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		if self.mouse_captured:
			sensitivity = 0.004

			self.world.player.rotation[0] += delta_x * sensitivity
			self.world.player.rotation[1] += delta_y * sensitivity

			self.world.player.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.world.player.rotation[1]))

	def on_mouse_drag(self, x, y, delta_x, delta_y, buttons, modifiers):
		self.on_mouse_motion(x, y, delta_x, delta_y)

	def on_key_press(self, key, modifiers):
		if not self.mouse_captured:
			return

		if   key == pyglet.window.key.D: self.world.player.input[0] += 1
		elif key == pyglet.window.key.A: self.world.player.input[0] -= 1
		elif key == pyglet.window.key.W: self.world.player.input[2] += 1
		elif key == pyglet.window.key.S: self.world.player.input[2] -= 1

		elif key == pyglet.window.key.SPACE : self.world.player.input[1] += 1
		elif key == pyglet.window.key.LSHIFT: self.world.player.input[1] -= 1
		elif key == pyglet.window.key.LCTRL : self.world.player.target_speed = player.SPRINTING_SPEED

		elif key == pyglet.window.key.F:
			self.world.player.flying = not self.world.player.flying

		elif key == pyglet.window.key.G:
			self.holding = random.randint(1, len(self.world.block_types) - 1)

		elif key == pyglet.window.key.N:
			self.world.player.ghost = not self.world.player.ghost

		elif key == pyglet.window.key.O:
			self.world.save.save()

		elif key == pyglet.window.key.R:
			self.world.player.reset()

		elif key == pyglet.window.key.B:
			for entity in self.world.entities:
				entity.reset()

		elif key == pyglet.window.key.E:
			_mob = mob.Mob(self.world, random.choice([*self.world.entity_types.values()]))
			self.world.entities.append(_mob)

			_mob.teleport(self.world.player.position)

		elif key == pyglet.window.key.ESCAPE:
			self.mouse_captured = False
			self.set_exclusive_mouse(False)

	def on_key_release(self, key, modifiers):
		if not self.mouse_captured:
			return

		if   key == pyglet.window.key.D: self.world.player.input[0] -= 1
		elif key == pyglet.window.key.A: self.world.player.input[0] += 1
		elif key == pyglet.window.key.W: self.world.player.input[2] -= 1
		elif key == pyglet.window.key.S: self.world.player.input[2] += 1

		elif key == pyglet.window.key.SPACE : self.world.player.input[1] -= 1
		elif key == pyglet.window.key.LSHIFT: self.world.player.input[1] += 1
		elif key == pyglet.window.key.LCTRL : self.world.player.target_speed = player.WALKING_SPEED

class Game:
	def __init__(self):
		self.config = gl.Config(major_version = 3, minor_version = 3, depth_size = 16)
		self.window = Window(config = self.config, width = 800, height = 600, caption = "Minecraft clone", resizable = True, vsync = False)

	def run(self):
		pyglet.app.run()

if __name__ == "__main__":
	game = Game()
	game.run()
