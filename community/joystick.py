import pyglet.input

import controller
import threading
import player
import math
import time

class Joystick_controller(controller.Controller):
	def __init__(self, game):
		super().__init__(game)
		self.init_joysticks(pyglet.input.get_joysticks())

		self.camera_sensitivity = 0.007
		self.joystick_deadzone = 0.25
		self.update_delay = 0.15
		self.last_update = 0

		self.joystick_move = [0, 0]
		self.joystick_look = [0, 0]
		self.joystick_interact = [0, 0]

		self.joystick_updater = threading.Thread(target=self.updater, daemon=True, name="Joystick Updater")
		self.joystick_updater.start()

	def updater(self):
		while True:
			if len(pyglet.input.get_joysticks()) != len(self.joysticks):
				self.init_joysticks(pyglet.input.get_joysticks())
			
			time.sleep(2)

	def init_joysticks(self, joysticks):
		self.joysticks = joysticks

		for joystick in self.joysticks:
			joystick.on_joybutton_press = self.on_joybutton_press
			joystick.on_joybutton_release = self.on_joybutton_release
			joystick.on_joyaxis_motion = self.on_joyaxis_motion
			joystick.on_joyhat_motion = self.on_joyhat_motion
			joystick.open(exclusive=True)

	def update_controller(self):
		if not self.game.mouse_captured or not self.joysticks:
			return

		self.game.player.rotation[0] += self.joystick_look[0] * self.camera_sensitivity
		self.game.player.rotation[1] += -self.joystick_look[1] * self.camera_sensitivity

		self.game.player.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.game.player.rotation[1]))

		if round(max(self.joystick_interact)) > 0 and (self.last_update + self.update_delay) <= time.process_time():
			if round(self.joystick_interact[0]) > 0: self.interact(self.InteractMode.BREAK)
			if round(self.joystick_interact[1]) > 0: self.interact(self.InteractMode.PLACE)

			self.last_update = time.process_time()

	def on_joybutton_press(self, joystick, button):
		if "xbox" in joystick.device.name.lower():
			if button == 1: self.misc(self.MiscMode.RANDOM)
			elif button == 2: self.interact(self.InteractMode.PICK)
			elif button == 3: self.misc(self.MiscMode.SAVE)

			elif button == 0: self.start_move(self.MoveMode.UP)
			elif button == 9: self.start_move(self.MoveMode.DOWN)

			elif button == 8:
				if self.game.player.target_speed == player.SPRINTING_SPEED: self.end_modifier(self.ModifierMode.SPRINT)
				elif self.game.player.target_speed == player.WALKING_SPEED: self.start_modifier(self.ModifierMode.SPRINT)

		elif "wireless controller" == joystick.device.name.lower():
			if button == 2: self.misc(self.MiscMode.RANDOM)
			elif button == 0: self.interact(self.InteractMode.PICK)
			elif button == 3: self.misc(self.MiscMode.SAVE)

			elif button == 1: self.start_move(self.MoveMode.UP)
			elif button == 11: self.start_move(self.MoveMode.DOWN)

			elif button == 10:
				if self.game.player.target_speed == player.SPRINTING_SPEED: self.end_modifier(self.ModifierMode.SPRINT)
				elif self.game.player.target_speed == player.WALKING_SPEED: self.start_modifier(self.ModifierMode.SPRINT)

	def on_joybutton_release(self, joystick, button):
		if "xbox" in joystick.device.name.lower():
			if button == 0: self.end_move(self.MoveMode.UP)
			elif button == 9: self.end_move(self.MoveMode.DOWN)

		elif "wireless controller" == joystick.device.name.lower():
			if button == 1: self.end_move(self.MoveMode.UP)
			elif button == 11: self.end_move(self.MoveMode.DOWN)

	def on_joyaxis_motion(self, joystick, axis, value):
		if abs(value) < self.joystick_deadzone:
			value = 0

		if "xbox" in joystick.device.name.lower():
			if axis == "x":
				if math.ceil(value) > 0 and self.joystick_move[0] == 0: self.start_move(self.MoveMode.RIGHT)
				elif math.floor(value) < 0 and self.joystick_move[0] == 0: self.start_move(self.MoveMode.LEFT)
				elif value == 0 and math.ceil(self.joystick_move[0]) > 0: self.end_move(self.MoveMode.RIGHT)
				elif value == 0 and math.floor(self.joystick_move[0]) < 0: self.end_move(self.MoveMode.LEFT)
			
				self.joystick_move[0] = value
			elif axis == "y":
				if math.ceil(value) > 0 and self.joystick_move[1] == 0: self.start_move(self.MoveMode.BACKWARD)
				elif math.floor(value) < 0 and self.joystick_move[1] == 0: self.start_move(self.MoveMode.FORWARD)
				elif value == 0 and math.ceil(self.joystick_move[1]) > 0: self.end_move(self.MoveMode.BACKWARD)
				elif value == 0 and math.floor(self.joystick_move[1]) < 0: self.end_move(self.MoveMode.FORWARD)

				self.joystick_move[1] = value

			if axis == "rx": self.joystick_look[0] = value
			if axis == "ry": self.joystick_look[1] = value

			if axis == "z":
				if value < 0: self.joystick_interact[0] = -value
				if value > 0: self.joystick_interact[1] = value

		elif "wireless controller" == joystick.device.name.lower():
			if axis == "x":
				if math.ceil(value) > 0 and self.joystick_move[0] == 0: self.start_move(self.MoveMode.RIGHT)
				elif math.floor(value) < 0 and self.joystick_move[0] == 0: self.start_move(self.MoveMode.LEFT)
				elif value == 0 and math.ceil(self.joystick_move[0]) > 0: self.end_move(self.MoveMode.RIGHT)
				elif value == 0 and math.floor(self.joystick_move[0]) < 0: self.end_move(self.MoveMode.LEFT)
			
				self.joystick_move[0] = value
			elif axis == "y":
				if math.ceil(value) > 0 and self.joystick_move[1] == 0: self.start_move(self.MoveMode.BACKWARD)
				elif math.floor(value) < 0 and self.joystick_move[1] == 0: self.start_move(self.MoveMode.FORWARD)
				elif value == 0 and math.ceil(self.joystick_move[1]) > 0: self.end_move(self.MoveMode.BACKWARD)
				elif value == 0 and math.floor(self.joystick_move[1]) < 0: self.end_move(self.MoveMode.FORWARD)

				self.joystick_move[1] = value

			if axis == "z": self.joystick_look[0] = value
			if axis == "rz": self.joystick_look[1] = value

			if axis == "rx": self.joystick_interact[0] = value
			if axis == "ry": self.joystick_interact[1] = value

			print(axis)

	def on_joyhat_motion(self, joystick, hat_x, hat_y):
		pass