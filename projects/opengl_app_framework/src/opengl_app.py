import glfw
from OpenGL.GL import *
from src.model import Model
from src.shader import Shader

class OpenGLApp:
	window = None
	_title: str = "OpenGL App"
	size: tuple[int, int] = (800, 600)
	_loaded_models = []

	mouse_pos = (0, 0)
	width: int
	height: int

	keys = set()
	mouse_buttons = set()

	_key_callbacks = None
	_mouse_button_callbacks = None
	_mouse_move_callbacks = None
	_mouse_scroll_callbacks = None

	@staticmethod
	def _create_window(width, height, title):
		if not glfw.init():
			raise Exception("GLFW can't be initialized")

		window = glfw.create_window(width, height, title, None, None)
		if not window:
			glfw.terminate()
			raise Exception("GLFW window can't be created")

		glfw.make_context_current(window)
		OpenGLApp.width = width
		OpenGLApp.height = height
		return window

	def run(self):
		# Create the window
		self.window = OpenGLApp._create_window(*OpenGLApp.size, OpenGLApp._title)

		# Register callbacks
		glfw.set_key_callback(self.window, self._key_callback)
		glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)
		glfw.set_cursor_pos_callback(self.window, self._cursor_pos_callback)

		# Setup user environment
		self.setup()
		glfw.focus_window(self.window)
		while not glfw.window_should_close(self.window):
			# Poll events
			glfw.poll_events()
			glClear(GL_COLOR_BUFFER_BIT)
			# Call update function and pass the current time
			self.update(glfw.get_time())
			# Swap the front and back buffers
			glfw.swap_buffers(self.window)
		# Clean up
		self.exit()
		glfw.terminate()

	def setup(self):
		raise NotImplemented

	def update(self, t):
		raise NotImplemented

	def exit(self):
		raise NotImplemented

	def on_key_event(self, key, action):
		pass

	def on_mouse_button_event(self, button, action, mods):
		pass

	#def on_mouse_move(self, mouse_x, mouse_y):
	#	pass

	def _key_callback(self, window, key, scancode, action, mods):
		if action == glfw.PRESS:
			self.keys.add(key)
		elif action == glfw.RELEASE:
			self.keys.discard(key)
		self.on_key_event(key, action)

	def _mouse_button_callback(self, window, button, action, mods):
		if action == glfw.PRESS:
			self.mouse_buttons.add(button)
		elif action == glfw.RELEASE:
			self.mouse_buttons.discard(button)
		self.on_mouse_button_event(button, action, mods)

	def _cursor_pos_callback(self, window, xpos, ypos):
		self.mouse_pos = (xpos, self.height-ypos)
		#self.on_mouse_move(xpos, -ypos)

	# --- Utility Functions ---
	@staticmethod
	def load_model(model_path: str, **kwargs) -> Model:
		model = Model(model_path, **kwargs)
		return model

	@staticmethod
	def load_shader(shader_path: str) -> Shader:
		shader = Shader(shader_path)
		shader.use()
		return shader

	@staticmethod
	def text(text: str, position: tuple[float, float, float], rotation: tuple[float, float, float] = (0, 0, 0)):
		pass

	@staticmethod
	def set_window(width: int, height: int, title: str):
		OpenGLApp.size = (width, height)
		OpenGLApp.title = title

	@staticmethod
	def register_key_callback(key, callback):
		OpenGLApp._key_callbacks[key] = callback

	@staticmethod
	def register_mouse_button_callback(button, callback):
		OpenGLApp._mouse_button_callbacks[button] = callback

	@staticmethod
	def register_mouse_move_callback(callback):
		OpenGLApp._mouse_move_callbacks.append(callback)

	@staticmethod
	def register_mouse_scroll_callback(callback):
		OpenGLApp._mouse_scroll_callbacks.append(callback)
