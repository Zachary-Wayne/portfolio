"""
A minimal sketch using the OpenGLApp framework: a full-screen shader that follows the mouse.

Run from this folder with `pip install glfw PyOpenGL PyGLM pywavefront numpy`.
"""
import numpy as np
from OpenGL.GL import *

from src.opengl_app import OpenGLApp


class Demo(OpenGLApp):
	OpenGLApp.set_window(800, 800, "OpenGLApp demo")

	def setup(self):
		self.shader = self.load_shader("shaders/demo.glsl")
		self.shader.set_uniform("u_resolution", np.array([800, 800], dtype=np.float32), "vec2")
		self.shader.set_uniform("u_tme", 0.0, "float")  # Misspelt on purpose: prints "Did you mean 'u_time'?"

	def update(self, t):
		glDrawArrays(GL_TRIANGLES, 0, 6)
		self.shader.set_uniform("u_time", t, "float")
		self.shader.set_uniform("u_mouse", np.array(self.mouse_pos, dtype=np.float32), "vec2")

	def on_key_event(self, key, action):
		if key == 256 and action == 1:  # Escape
			self.exit()

	def exit(self):
		import glfw
		glfw.set_window_should_close(self.window, True)


if __name__ == "__main__":
	Demo().run()
