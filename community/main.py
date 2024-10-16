import sys
import math
import ctypes
import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False

import pyglet.gl as gl

import matrix
import shader
import camera

import block_type
import texture_manager

import world

import hit

class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)

		# create world

		self.world = world.World()
		
		# create shader

		self.shader = shader.Shader("vert.glsl", "frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"texture_array_sampler")
		self.shader.use()

		# pyglet stuff

		pyglet.clock.schedule_interval(self.update, 1.0 / 10000)
		self.mouse_captured = False

		# camera stuff

		self.camera = camera.Camera(self.shader, self.width, self.height)

		# other stuff

		sys.setswitchinterval(0.000000001)
		self.holding = 7
		self.sprinting = False
		self.flying = False

		self.time_of_day = 0.0  # Represents time of day, 0.0 to 1.0 where 0.0 is midnight and 0.5 is noon
		self.cycle_speed = 0.01  # Speed of the day-night cycle

        # Define sky colors for different times of the day
		self.sky_colors = {
            'midnight': (15/255, 15/255, 45/255, 1.0),
            'dawn': (135/255, 206/255, 250/255, 1.0),
            'noon': (135/255, 206/255, 250/255, 1.0),
            'dusk': (250/255, 128/255, 114/255, 1.0),
            'night': (25/255, 25/255, 112/255, 1.0)
        }

	def interpolate_color(self, color1, color2, factor):
		return tuple(c1 + (c2 - c1) * factor for c1, c2 in zip(color1, color2))

	def update_sky_color(self):
		if self.time_of_day < 0.25:
            # Dawn
			factor = self.time_of_day / 0.25
			color = self.interpolate_color(self.sky_colors['midnight'], self.sky_colors['dawn'], factor)
		elif self.time_of_day < 0.5:
            # Noon
			factor = (self.time_of_day - 0.25) / 0.25
			color = self.interpolate_color(self.sky_colors['dawn'], self.sky_colors['noon'], factor)
		elif self.time_of_day < 0.75:
            # Dusk
			factor = (self.time_of_day - 0.5) / 0.25
			color = self.interpolate_color(self.sky_colors['noon'], self.sky_colors['dusk'], factor)
		else:
            # Night to Midnight
			factor = (self.time_of_day - 0.75) / 0.25
			color = self.interpolate_color(self.sky_colors['dusk'], self.sky_colors['night'], factor)

            # Additional blending for smoother transition from night to midnight
			if self.time_of_day > 0.99:
				additional_factor = (self.time_of_day - 0.99) / 0.01
				color = self.interpolate_color(color, self.sky_colors['midnight'], additional_factor)

		gl.glClearColor(*color)
	
	def update(self, delta_time):
		if not self.mouse_captured:
			self.camera.input = [0, 0, 0]

		self.camera.update_camera(delta_time, self.sprinting, self.world, self.flying)
		

		
		self.time_of_day += self.cycle_speed * delta_time
		self.time_of_day %= 1.0  # Keep time_of_day in the range [0.0, 1.0]

        # Update the sky color
		self.update_sky_color()
	
	def on_draw(self):
		self.world.process_load_queue(self.camera.position)
		self.camera.update_matrices()

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)

		# draw stuff

		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)
		self.clear()
		self.world.draw()

		gl.glFinish()
	
	# input functions

	def on_resize(self, width, height):
		gl.glViewport(0, 0, width, height)

		self.camera.width = width
		self.camera.height = height
	
	def on_mouse_press(self, x, y, button, modifiers):
		if not self.mouse_captured:
			self.mouse_captured = True
			self.set_exclusive_mouse(True)

			return

		def hit_callback(current_block, next_block):
			if self.world.get_block_number(current_block) != 14 and 0 <= current_block[1] < 128:
				if button == pyglet.window.mouse.RIGHT:
					if self.camera.check_collision(self.world, self.camera.position):
						self.world.set_block(current_block, self.holding)
				elif button == pyglet.window.mouse.LEFT: self.world.set_block(next_block, 0)
				elif button == pyglet.window.mouse.MIDDLE: self.holding = self.world.get_block_number(next_block)
		
		hit_ray = hit.Hit_ray(self.world, self.camera.rotation, self.camera.position)

		while hit_ray.distance < hit.HIT_RANGE:
			if hit_ray.step(hit_callback):
				break
	
	def on_mouse_motion(self, x, y, delta_x, delta_y):
		if self.mouse_captured:
			sensitivity = 0.004

			self.camera.rotation[0] += delta_x * sensitivity
			self.camera.rotation[1] += delta_y * sensitivity

			self.camera.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.camera.rotation[1]))
	
	def on_mouse_drag(self, x, y, delta_x, delta_y, buttons, modifiers):
		self.on_mouse_motion(x, y, delta_x, delta_y)

	def on_key_press(self, key, modifiers):
		if not self.mouse_captured:
			return

		if key == pyglet.window.key.D: 
			self.camera.input[0] += 2
		elif key == pyglet.window.key.A: 
			self.camera.input[0] -= 2
		elif key == pyglet.window.key.W: 
			self.camera.input[2] += 2
		elif key == pyglet.window.key.S: 
			self.camera.input[2] -= 2
		elif key == pyglet.window.key.LCTRL and self.camera.input[2] > 0: 
			self.sprinting = True
		elif key == pyglet.window.key.R: 
			self.camera.position = [0, 80, 0]
		elif key == pyglet.window.key.F: 
			self.flying = not self.flying

		elif key == pyglet.window.key.SPACE:
			if self.flying:
				self.camera.input[1] += 2  # Stop ascending
			else:
				# Don't reset input[1] directly; let the gravity handle it
				if self.camera.is_jumping:
					self.camera.input[1] -= 1  # Prevent further jumping mid-air

				else:
					self.camera.input[1] += 1
					self.camera.is_jumping = True


		elif key == pyglet.window.key.LSHIFT:
			if self.flying:
				self.camera.input[1] -= 2  # Descend in flying mode

		elif key == pyglet.window.key.ESCAPE:
			self.mouse_captured = False
			self.set_exclusive_mouse(False)


	def on_key_release(self, key, modifiers):
		if not self.mouse_captured:
			return

		if   key == pyglet.window.key.D: self.camera.input[0] -= 2
		elif key == pyglet.window.key.A: self.camera.input[0] += 2
		elif key == pyglet.window.key.W: self.camera.input[2] -= 2
		elif key == pyglet.window.key.S: self.camera.input[2] += 2
		elif key == pyglet.window.key.LCTRL: self.sprinting = False

		elif key == pyglet.window.key.SPACE:
			if self.flying:
				self.camera.input[1] -= 2  # Stop ascending
			else:
				self.camera.input[1] = 0  # Reset jump
				self.camera.is_jumping = False

		elif key == pyglet.window.key.LSHIFT:
			if self.flying:
				self.camera.input[1] += 2  # Stop descending



class Game:
	def __init__(self):
		self.config = gl.Config(major_version = 3, depth_size = 16)
		self.window = Window(config = self.config, width = 800, height = 600, caption = "Minecraft clone", resizable = True, vsync = False)
	
	def run(self):
		pyglet.app.run()

if __name__ == "__main__":
	game = Game()
	game.run()
