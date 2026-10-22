import numpy as np
from PyGLM import glm
from OpenGL.GL import *
import OpenGL.GL.shaders
from OpenGL.GL.shaders import compileProgram, compileShader
import re

from src.utils import Utils
from src.mappings import GL_TYPE_MAP, GL_UNIFORM_MAP

class Shader:
	uniforms_not_found = []
	def __init__(self, filename):
		self.loaded = False
		self.shader_program = None
		self.shader_name = filename.split('/')[-1]
		# Validate the filename extension
		if not filename.endswith(".glsl"):
			raise ValueError(f"Shader file at '{filename}' must end in .glsl")

		# Read the shader source from file
		with open(filename, 'r') as file:
			shader_source = file.read()

		# Separate the shader code into vertex and fragment parts
		self.vertex_shader_source, self.fragment_shader_source = self._parse_shader_source(shader_source)

		print(f"Loaded shader '{self.shader_name}'")

	def _parse_shader_source(self, source):

		vertex_section = re.findall(r"/// VERTEX_START(.*?)/// VERTEX_END", source, re.DOTALL)
		fragment_section = re.findall(r"/// FRAGMENT_START(.*?)/// FRAGMENT_END", source, re.DOTALL)

		if vertex_section:
			vertex_shader = vertex_section[0].strip()
		else:
			raise ValueError(f"Vertex shader section not found in {self.shader_name}")

		if fragment_section:
			fragment_shader = fragment_section[0].strip()
		else:
			raise ValueError(f"Fragment shader section not found in {self.shader_name}")

		return vertex_shader, fragment_shader

	@staticmethod
	def _print_shader_error(_error):
		print("SHADER ERROR\n")
		error_message, shader_source, shader_type = _error.args
		error_string = ""
		for line in error_message.split("ERROR: ")[1:]:
			error_string += line.replace("\\n", "")
		source_string = ""
		for i, line in enumerate(shader_source[0].decode('utf-8').split('\n')):
			source_string += f"{i+1}: {line}\n"

		fstring = (f"Shader source:\n{source_string}\n"
				   f"Shader compilation error:\n{error_string}\n\n"
				   f"Shader type: {shader_type}")

		print(fstring)
		exit(-1)

	def use(self):
		try:
			# Compile the vertex and fragment shaders
			vertex_shader = compileShader(self.vertex_shader_source, GL_VERTEX_SHADER)
			fragment_shader = compileShader(self.fragment_shader_source, GL_FRAGMENT_SHADER)

			# Create the shader program
			self.shader_program = compileProgram(vertex_shader, fragment_shader)

			glValidateProgram(self.shader_program)
			if not glGetProgramiv(self.shader_program, GL_VALIDATE_STATUS):
				_error = glGetProgramInfoLog(self.shader_program)
				print(f"Shader Program Validation error in '{self.shader_name}': {_error}")
		except OpenGL.GL.shaders.ShaderCompilationError as e:
			self._print_shader_error(e)

		# Use the shader program in the current OpenGL context
		glUseProgram(self.shader_program)
		print(f"Compiled shader '{self.shader_name}'.")

		num_uniforms = glGetProgramiv(self.shader_program, GL_ACTIVE_UNIFORMS)
		if num_uniforms == 0:
			print(f"Shader '{self.shader_name}' has no uniforms.")
			return
		print(f"Shader '{self.shader_name}' has {num_uniforms} uniforms:")
		for i in range(num_uniforms):
			uniform_name, _, uniform_type = glGetActiveUniform(self.shader_program, i)
			print(f"\t{GL_TYPE_MAP[uniform_type]}: {uniform_name.decode('utf-8')}")

		self.loaded = True

	def set_uniform(self, key, value, value_type):
		if key in self.uniforms_not_found:
			return
		location = glGetUniformLocation(self.shader_program, key)
		if location == -1:
			# A reminder that unused uniforms in the shader program will be removed during compilation
			current_closest = (None, int(1e9))
			for i in range(glGetProgramiv(self.shader_program, GL_ACTIVE_UNIFORMS)):
				uniform_name, _, uniform_type = glGetActiveUniform(self.shader_program, i)
				distance = Utils.levenshtein_distance(key, uniform_name.decode('utf-8'))
				if distance < current_closest[1]:
					current_closest = (uniform_name.decode('utf-8'), distance)
			if current_closest[0] is None:
				print(f"Warning: Uniform '{key}' not found in shader program.")
				self.uniforms_not_found.append(key)
			else:
				print(f"Warning: Uniform '{key}' not found in shader program."
					  f"\n-\tDid you mean '{current_closest[0]}'?")
				self.uniforms_not_found.append(key)
			return

		try:
			"""
			if isinstance(value, int):
				glProgramUniform1i(self.shader_program, location, value)
			elif isinstance(value, float):
				glProgramUniform1f(self.shader_program, location, value)
			elif isinstance(value, bool):
				glProgramUniform1i(self.shader_program, location, int(value))
			elif isinstance(value, glm.vec2):
				glProgramUniform2fv(self.shader_program, location, 1, glm.value_ptr(value))
			elif isinstance(value, glm.vec3):
				glProgramUniform3fv(self.shader_program, location, 1, glm.value_ptr(value))
			elif isinstance(value, glm.vec4):
				glProgramUniform4fv(self.shader_program, location, 1, glm.value_ptr(value))
			elif isinstance(value, glm.mat4):
				glUniformMatrix4fv(location, 1, GL_FALSE, glm.value_ptr(value))
			elif isinstance(value, np.ndarray) and value.ndim == 1 and value.size == 2:
				glUniform2fv(location, 1, value)
			elif isinstance(value, np.ndarray) and value.ndim == 1 and value.size == 3:
				glUniform3fv(location, 1, value)
			elif isinstance(value, np.ndarray) and value.ndim == 1 and value.size == 4:
				glUniform4fv(location, 1, value)
			elif isinstance(value, np.ndarray) and value.ndim == 2 and value.shape[1] == 2:
				value = np.column_stack((value, np.zeros_like(value[:, 0])))
				value = value.astype(np.float32)
				glProgramUniformMatrix2fv(self.shader_program, location, 1, GL_FALSE, value)
			elif isinstance(value, np.ndarray) and value.ndim == 2 and value.shape[1] == 3:
				value = np.column_stack((value, np.zeros_like(value[:, 0]))).astype(np.float32)
				glProgramUniformMatrix3fv(self.shader_program, location, 1, GL_FALSE, value)
			elif isinstance(value, np.ndarray) and value.ndim == 2 and value.shape[1] == 4:
				value = np.column_stack((value, np.ones_like(value[:, 0]))).astype(np.float32)
				glProgramUniformMatrix4fv(self.shader_program, location, 1, GL_FALSE, value)
			elif isinstance(value, np.ndarray) and value.ndim == 1:
				glProgramUniform1fv(self.shader_program, location, len(value), value)
			"""
			GL_UNIFORM_MAP[value_type](self.shader_program, location, value)
		except (ValueError, error.GLError) as e:
			if isinstance(value, np.ndarray):
				if value.ndim == 1:
					value_type = f'vec{value.size}\t ({type(value).__name__})'
				elif value.ndim == 2:
					value_type = f'mat{value.shape[0]}\t ({type(value).__name__})'
				else:
					value_type = type(value).__name__
			else:
				value_type = type(value).__name__
			uniform_name, _, uniform_type = glGetActiveUniform(self.shader_program, location)
			key_type = GL_TYPE_MAP[uniform_type]
			value_str = str(value)
			if len(value_str) > 50: # Cutoff for long strings
				value_str = value_str[:50] + f"... ({len(value_str) - 50} more symbols)"
			print(f"Warning: Uniform '{uniform_name.decode('utf-8')}' received an incompatible type:"
				  f"\n\tExpected:\t{key_type}"
				  f"\n\tReceived:\t{value_type}"
				  f"\n\tValue:\t \t{value_str}")

			# exit(-1)