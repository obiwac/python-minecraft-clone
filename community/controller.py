import pyglet.input

import baseinput
import player
import math
import time

class Controller(baseinput.BaseInput):
	def __init__(self, game):
		super().__init__(game)
		self.controller_manager = pyglet.input.ControllerManager()

		self.camera_sensitivity = 2.5
		self.joystick_deadzone = 0.25
		self.update_delay = 0.15
		self.last_update = 0

		self.joystick_move = [0, 0]
		self.joystick_look = [0, 0]
		self.joystick_interact = [0, 0]

		self.main_controller = None
		self.try_get_main_controller()

		@self.controller_manager.event
		def on_connect(controller):
			if self.main_controller is None:
				self.new_main_controller(controller)

			print("Connect:", controller)

		@self.controller_manager.event
		def on_disconnect(controller):
			if self.main_controller == controller:
				self.main_controller = None
				self.try_get_main_controller()

			print("Disconnect:", controller)

	def try_get_main_controller(self):
		if self.main_controller is None:
			if len(self.controller_manager.get_controllers()) > 0:
				self.new_main_controller(self.controller_manager.get_controllers()[0])

	def new_main_controller(self, controller):
		self.main_controller = controller
		self.main_controller.open()

		@self.main_controller.event
		def on_stick_motion(controller, stick, x, y):
			if controller == self.main_controller:
				if stick == "left":
					self.joystick_move = [x, y]
				elif stick == "right":
					self.joystick_look = [x, y]

	def update_controller(self, delta_time):
		if not self.game.mouse_captured or self.main_controller is None:
			return

		self.joystick_move = self.apply_deadzone([self.main_controller.leftx, self.main_controller.lefty])
		self.joystick_look = self.apply_deadzone([self.main_controller.rightx, self.main_controller.righty])
		self.joystick_interact = [self.main_controller.lefttrigger, self.main_controller.righttrigger]

		self.game.player.rotation[0] += self.joystick_look[0] * self.camera_sensitivity * delta_time
		self.game.player.rotation[1] += self.joystick_look[1] * self.camera_sensitivity * delta_time

		self.game.player.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.game.player.rotation[1]))

		if round(max(self.joystick_interact)) > 0 and (self.last_update + self.update_delay) <= time.process_time():
			if round(self.joystick_interact[0]) > 0:
				if self.interact(self.InteractMode.BREAK):
					self.main_controller.rumble_play_weak(1, duration=0.05)
			if round(self.joystick_interact[1]) > 0: self.interact(self.InteractMode.PLACE)

			self.last_update = time.process_time()

		if self.main_controller.x: self.interact(self.InteractMode.PICK)
		if self.main_controller.y: self.misc(self.MiscMode.RANDOM)
		if self.main_controller.b: self.misc(self.MiscMode.SAVE)

		if self.main_controller.leftstick:
			if self.game.player.target_speed == player.SPRINTING_SPEED: self.end_modifier(self.ModifierMode.SPRINT)
			elif self.game.player.target_speed == player.WALKING_SPEED: self.start_modifier(self.ModifierMode.SPRINT)

		self.game.controls[0] = round(self.joystick_move[0])
		self.game.controls[1] = round(int(self.main_controller.a == True) - int(self.main_controller.rightstick == True))
		self.game.controls[2] = round(self.joystick_move[1])

		for axis in range(3): self.update_move(axis)

	def apply_deadzone(self, value):
		if abs(value[0]) < self.joystick_deadzone: value[0] = 0
		if abs(value[1]) < self.joystick_deadzone: value[1] = 0
		return value
		
