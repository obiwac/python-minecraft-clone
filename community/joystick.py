import pyglet.input

import controller
import camera
import math
import time

class Joystick_controller(controller.Controller):
	def __init__(self, game):
		super().__init__(game)

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
		if not self.game.mouse_captured or not self.joysticks:
			return

		self.game.camera.rotation[0] += self.joystick_rpos[0] * self.camera_sensitivity
		self.game.camera.rotation[1] += -self.joystick_rpos[1] * self.camera_sensitivity

		self.game.camera.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.game.camera.rotation[1]))

		if round(abs(self.joystick_tpos)) and (self.last_update + self.update_delay) <= time.process_time():
			if round(self.joystick_tpos) > 0: self.interact(self.InteractMode.PLACE)
			elif round(self.joystick_tpos) < 0: self.interact(self.InteractMode.BREAK)

			self.last_update = time.process_time()

	def on_joybutton_press(self, joystick, button):
		if not self.game.mouse_captured:
			return

		if button == 1: self.misc(self.MiscMode.RANDOM)
		elif button == 2: self.interact(self.InteractMode.PICK)
		elif button == 3: self.misc(self.MiscMode.SAVE)

		elif button == 0: self.start_move(self.MoveMode.UP)
		elif button == 9: self.start_move(self.MoveMode.DOWN)

		elif button == 8:
			if self.game.camera.target_speed == camera.SPRINTING_SPEED: self.end_modifier(self.ModifierMode.SPRINT)
			elif self.game.camera.target_speed == camera.WALKING_SPEED: self.start_modifier(self.ModifierMode.SPRINT)

	def on_joybutton_release(self, joystick, button):
		if not self.game.mouse_captured:
			return

		if button == 0: self.end_move(self.MoveMode.UP)
		elif button == 9: self.end_move(self.MoveMode.DOWN)

	def on_joyaxis_motion(self, joystick, axis, value):
		if abs(value) < self.joystick_deadzone:
			value = 0

		if axis == "x":
			if math.ceil(value) > 0 and self.joystick_pos[0] == 0: self.start_move(self.MoveMode.RIGHT)
			elif math.floor(value) < 0 and self.joystick_pos[0] == 0: self.start_move(self.MoveMode.LEFT)
			elif value == 0 and math.ceil(self.joystick_pos[0]) > 0: self.end_move(self.MoveMode.RIGHT)
			elif value == 0 and math.floor(self.joystick_pos[0]) < 0: self.end_move(self.MoveMode.LEFT)
			
			self.joystick_pos[0] = value
		elif axis == "y":
			if math.ceil(value) > 0 and self.joystick_pos[1] == 0: self.start_move(self.MoveMode.BACKWARD)
			elif math.floor(value) < 0 and self.joystick_pos[1] == 0: self.start_move(self.MoveMode.FORWARD)
			elif value == 0 and math.ceil(self.joystick_pos[1]) > 0: self.end_move(self.MoveMode.BACKWARD)
			elif value == 0 and math.floor(self.joystick_pos[1]) < 0: self.end_move(self.MoveMode.FORWARD)

			self.joystick_pos[1] = value

		if axis == "rx": self.joystick_rpos[0] = value
		if axis == "ry": self.joystick_rpos[1] = value

		if axis == "z": self.joystick_tpos = value

	def on_joyhat_motion(self, joystick, hat_x, hat_y):
		pass