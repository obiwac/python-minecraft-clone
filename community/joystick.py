import pyglet.input
import math
import hit
import time
import random

class Joystick_controller:
	def __init__(self, game):
		self.game = game
		self.joysticks = pyglet.input.get_joysticks()
		self.camera_sensitivity = 0.007
		self.joystick_deadzone = 0.25
		self.update_delay = 0.1
		self.last_update = 0

		for joystick in self.joysticks:
			joystick.on_joybutton_press = self.on_joybutton_press
			joystick.on_joybutton_release = self.on_joybutton_release
			joystick.on_joyaxis_motion = self.on_joyaxis_motion
			joystick.on_joyhat_motion = self.on_joyhat_motion
			joystick.open()

		self.joystick_pos = [0, 0]
		self.joystick_rpos = [0, 0]
		self.joystick_tpos = 0
		
		self.joystick_center = [0, 0]
		self.joystick_rcenter = [0, 0]

		self.joystick_buttons = []

	def update_controller(self):
		if not self.game.mouse_captured:
			return

		self.game.camera.rotation[0] += self.joystick_rpos[0] * self.camera_sensitivity
		self.game.camera.rotation[1] += -self.joystick_rpos[1] * self.camera_sensitivity

		self.game.camera.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.game.camera.rotation[1]))

		if 9 not in self.joystick_buttons and 0 not in self.joystick_buttons:
			self.game.camera.input[1] = 0
		elif 9 in self.joystick_buttons and 0 in self.joystick_buttons:
			self.game.camera.input[1] = 0
		elif 9 in self.joystick_buttons:
			self.game.camera.input[1] = -1
		elif 0 in self.joystick_buttons:
			self.game.camera.input[1] = 1

		if self.joystick_pos[0] > 0:
			self.game.camera.input[0] = 1
		elif self.joystick_pos[0] < 0:
			self.game.camera.input[0] = -1
		else:
			self.game.camera.input[0] = 0

		if self.joystick_pos[1] > 0:
			self.game.camera.input[2] = -1
		elif self.joystick_pos[1] < 0:
			self.game.camera.input[2] = 1
		else:
			self.game.camera.input[2] = 0

		if 1 in self.joystick_buttons:
			self.game.holding = random.randint(1, len(self.game.world.block_types) - 1)

		if 3 in self.joystick_buttons:
			self.game.world.save.save()

		if (round(abs(self.joystick_tpos)) > 0 or 2 in self.joystick_buttons) and (self.last_update + self.update_delay) <= time.process_time():
			def hit_callback(current_block, next_block):
				if round(self.joystick_tpos) > 0:
					self.game.world.set_block(current_block, self.game.holding)
				elif round(self.joystick_tpos) < 0:
					self.game.world.set_block(next_block, 0)
				elif 2 in self.joystick_buttons:
					self.game.holding = self.game.world.get_block_number(next_block)

			hit_ray = hit.Hit_ray(self.game.world, self.game.camera.rotation, self.game.camera.position)

			while hit_ray.distance < hit.HIT_RANGE:
				if hit_ray.step(hit_callback):
					break

			self.last_update = time.process_time()

	def on_joybutton_press(self, joystick, button):
		if not button in self.joystick_buttons:
			self.joystick_buttons.append(button)

		print(button)

	def on_joybutton_release(self, joystick, button):
		if button in self.joystick_buttons:
			del self.joystick_buttons[self.joystick_buttons.index(button)]

	def on_joyaxis_motion(self, joystick, axis, value):
		if abs(value) < self.joystick_deadzone:
			value = 0

		if axis == "x":
			self.joystick_pos[0] = value
		elif axis == "y":
			self.joystick_pos[1] = value

		if axis == "rx":
			self.joystick_rpos[0] = value
		if axis == "ry":
			self.joystick_rpos[1] = value

		if axis == "z":
			self.joystick_tpos = value

	def on_joyhat_motion(self, joystick, hat_x, hat_y):
		pass