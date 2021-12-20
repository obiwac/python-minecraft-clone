import pyglet.window

import controller
import math

class Keyboard_Mouse(controller.Controller):
	def __init__(self, game):
		super().__init__(game)

		self.game.on_mouse_press = self.on_mouse_press
		self.game.on_mouse_motion = self.on_mouse_motion
		self.game.on_mouse_drag = self.on_mouse_drag

		self.game.on_key_press = self.on_key_press
		self.game.on_key_release = self.on_key_release

	def on_mouse_press(self, x, y, button, modifiers):
		if not self.game.mouse_captured:
			self.game.mouse_captured = True
			self.game.set_exclusive_mouse(True)

			return

		if button == pyglet.window.mouse.RIGHT: self.interact(self.InteractMode.Place)
		elif button == pyglet.window.mouse.LEFT: self.interact(self.InteractMode.Break)
		elif button == pyglet.window.mouse.MIDDLE: self.interact(self.InteractMode.Pick)

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		if self.game.mouse_captured:
			sensitivity = 0.004

			self.game.camera.rotation[0] += delta_x * sensitivity
			self.game.camera.rotation[1] += delta_y * sensitivity

			self.game.camera.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.game.camera.rotation[1]))

	def on_mouse_drag(self, x, y, delta_x, delta_y, buttons, modifiers):
		self.on_mouse_motion(x, y, delta_x, delta_y)

	def on_key_press(self, key, modifiers):
		if not self.game.mouse_captured:
			return

		if key == pyglet.window.key.D: self.start_move(self.MoveMode.Right)
		elif key == pyglet.window.key.A: self.start_move(self.MoveMode.Left)
		elif key == pyglet.window.key.W: self.start_move(self.MoveMode.Forward)
		elif key == pyglet.window.key.S: self.start_move(self.MoveMode.Backward)
		elif key == pyglet.window.key.SPACE : self.start_move(self.MoveMode.Up)
		elif key == pyglet.window.key.LSHIFT: self.start_move(self.MoveMode.Down)

		elif key == pyglet.window.key.LCTRL : self.start_modifier(self.ModifierMode.Sprint)

		elif key == pyglet.window.key.G: self.misc(self.MiscMode.Random)
		elif key == pyglet.window.key.O: self.misc(self.MiscMode.Save)
		elif key == pyglet.window.key.ESCAPE: self.misc(self.MiscMode.Escape)

	def on_key_release(self, key, modifiers):
		if not self.game.mouse_captured:
			return

		if key == pyglet.window.key.D: self.end_move(self.MoveMode.Right)
		elif key == pyglet.window.key.A: self.end_move(self.MoveMode.Left)
		elif key == pyglet.window.key.W: self.end_move(self.MoveMode.Forward)
		elif key == pyglet.window.key.S: self.end_move(self.MoveMode.Backward)
		elif key == pyglet.window.key.SPACE : self.end_move(self.MoveMode.Up)
		elif key == pyglet.window.key.LSHIFT: self.end_move(self.MoveMode.Down)

		elif key == pyglet.window.key.LCTRL : self.end_modifier(self.ModifierMode.Sprint)