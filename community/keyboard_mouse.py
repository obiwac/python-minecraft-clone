import pyglet.window

import controller
import math
import imgui

class Keyboard_Mouse(controller.Controller):
	def __init__(self, game):
		super().__init__(game)

		self.game.window.on_mouse_press = self.on_mouse_press
		self.game.window.on_mouse_motion = self.on_mouse_motion
		self.game.window.on_mouse_drag = self.on_mouse_drag

		self.game.window.on_key_press = self.on_key_press
		self.game.window.on_key_release = self.on_key_release

	def on_mouse_press(self, x, y, button, modifiers):
		if not imgui.get_io().want_capture_mouse:
			if not self.game.window.mouse_captured:
				self.game.window.mouse_captured = True
				self.game.window.set_exclusive_mouse(True)

				return

			if button == pyglet.window.mouse.RIGHT: self.interact(self.InteractMode.PLACE)
			elif button == pyglet.window.mouse.LEFT: self.interact(self.InteractMode.BREAK)
			elif button == pyglet.window.mouse.MIDDLE: self.interact(self.InteractMode.PICK)

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		if not imgui.get_io().want_capture_mouse:
			if self.game.window.mouse_captured:
				sensitivity = 0.004

				self.game.player.rotation[0] += delta_x * sensitivity
				self.game.player.rotation[1] += delta_y * sensitivity

				self.game.player.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.game.player.rotation[1]))

	def on_mouse_drag(self, x, y, delta_x, delta_y, buttons, modifiers):
		if not imgui.get_io().want_capture_mouse:
			self.on_mouse_motion(x, y, delta_x, delta_y)

	def on_key_press(self, key, modifiers):
		if not imgui.get_io().want_capture_keyboard:
			if not self.game.window.mouse_captured:
				return

			if key == pyglet.window.key.D: self.start_move(self.MoveMode.RIGHT)
			elif key == pyglet.window.key.A: self.start_move(self.MoveMode.LEFT)
			elif key == pyglet.window.key.W: self.start_move(self.MoveMode.FORWARD)
			elif key == pyglet.window.key.S: self.start_move(self.MoveMode.BACKWARD)
			elif key == pyglet.window.key.SPACE : self.start_move(self.MoveMode.UP)
			elif key == pyglet.window.key.LSHIFT: self.start_move(self.MoveMode.DOWN)

			elif key == pyglet.window.key.LCTRL : self.start_modifier(self.ModifierMode.SPRINT)

			elif key == pyglet.window.key.F: self.misc(self.MiscMode.FLY)
			elif key == pyglet.window.key.G: self.misc(self.MiscMode.RANDOM)
			elif key == pyglet.window.key.O: self.misc(self.MiscMode.SAVE)
			elif key == pyglet.window.key.R: self.misc(self.MiscMode.TELEPORT)
			elif key == pyglet.window.key.ESCAPE: self.misc(self.MiscMode.ESCAPE)
			elif key == pyglet.window.key.F6: self.misc(self.MiscMode.SPEED_TIME)
			elif key == pyglet.window.key.F11: self.misc(self.MiscMode.FULLSCREEN)
			elif key == pyglet.window.key.F3: self.misc(self.MiscMode.TOGGLE_F3)
			elif key == pyglet.window.key.F10: self.misc(self.MiscMode.TOGGLE_AO)

	def on_key_release(self, key, modifiers):
		if not imgui.get_io().want_capture_keyboard:
			if not self.game.window.mouse_captured:
				return

			if key == pyglet.window.key.D: self.end_move(self.MoveMode.RIGHT)
			elif key == pyglet.window.key.A: self.end_move(self.MoveMode.LEFT)
			elif key == pyglet.window.key.W: self.end_move(self.MoveMode.FORWARD)
			elif key == pyglet.window.key.S: self.end_move(self.MoveMode.BACKWARD)
			elif key == pyglet.window.key.SPACE : self.end_move(self.MoveMode.UP)
			elif key == pyglet.window.key.LSHIFT: self.end_move(self.MoveMode.DOWN)

			elif key == pyglet.window.key.LCTRL : self.end_modifier(self.ModifierMode.SPRINT)