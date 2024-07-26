import pyglet

pyglet.options["shadow_window"] = False  # no need for shadow window
pyglet.options["debug_gl"] = False  # makes things slow, so disable it

import pyglet.gl as gl


class Window(pyglet.window.Window):  # create a class extending pyglet.window.Window
	def __init__(self, **args):
		super().__init__(**args)  # pass on arguments to pyglet.window.Window.__init__ function

	def on_draw(self):
		gl.glClearColor(1.0, 0.5, 1.0, 1.0)  # set clear colour
		self.clear()  # clear screen

	def on_resize(self, width, height):
		print(f"Resize {width} * {height}")  # print out window size


class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer=True, major_version=3, minor_version=3)  # use modern opengl
		self.window = Window(
			config=self.config, width=800, height=600, caption="Minecraft clone", resizable=True, vsync=False
		)  # vsync with pyglet causes problems on some computers, so disable it

	def run(self):
		pyglet.app.run()  # run our application


if __name__ == "__main__":  # only run the game if source file is the one run
	game = Game()  # create game object
	game.run()
