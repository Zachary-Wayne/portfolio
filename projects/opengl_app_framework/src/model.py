from PyGLM import glm
import numpy as np
import pywavefront
import os
import struct

from OpenGL.GL import *

from src.shader import Shader
from src.utils import Utils
from src.drawable import Drawable


class Model(Drawable):
	def __init__(self, model_path: str, force_obj: bool = False):
		self.vertices = []
		self.normals = []

		ext = os.path.splitext(model_path)[1]

		if ext == '.obj':
			bin_path = model_path.replace('.obj', '.bin')
			if not force_obj and os.path.exists(bin_path):
				print(f"Using cached binary model: {bin_path}")
				self._load_bin(bin_path)
			else:
				print(f"Loading OBJ model: {model_path}")
				self._load_obj(model_path)
				self._save_bin(bin_path)
		elif ext == '.bin':
			print(f"Loading binary model: {model_path}")
			self._load_bin(model_path)
		else:
			raise ValueError(f"Unsupported model file extension: {ext}")
		# Prepare vertex array and buffer
		self.vao = glGenVertexArrays(1)
		vbo = glGenBuffers(1)

		glBindVertexArray(self.vao)
		glBindBuffer(GL_ARRAY_BUFFER, vbo)

		# Upload vertex data to the GPU
		self.vertex_data = np.array(self.vertices, dtype=np.float32)
		# self.normal_data = np.array(self.normals, dtype=np.float32)  # Assuming normals are generated

		combined = self._interleaved_array()

		glBufferData(GL_ARRAY_BUFFER, combined.nbytes, combined, GL_STATIC_DRAW)

		# Define the position attribute
		glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * self.vertex_data.itemsize, ctypes.c_void_p(0))
		glEnableVertexAttribArray(0)

		# Define the normal attribute
		glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * self.vertex_data.itemsize,
							  ctypes.c_void_p(3 * self.vertex_data.itemsize))
		glEnableVertexAttribArray(1)


		# Unbind vao and vbo
		glBindBuffer(GL_ARRAY_BUFFER, 0)
		glBindVertexArray(0)

	#@Utils.time_task
	def _load_obj(self, path: str):
		self.mesh = pywavefront.Wavefront(path, collect_faces=True)

		for _, mesh in self.mesh.meshes.items():
			for face in mesh.faces:
				for i in face:
					self.vertices.extend(self.mesh.vertices[i])
					self.normals.extend(self.mesh.parser.normals[i])
		self.vertices = np.array(self.vertices)
		self.normals = np.array(self.normals)

	def _save_bin(self, path: str):
		with open(path, 'wb') as bin_file:
			num_vertices = len(self.vertices) // 3  # Calculate number of vertices
			bin_file.write(struct.pack('I', num_vertices))
			bin_file.write(struct.pack(f'{len(self.vertices)}f', *self.vertices))
			bin_file.write(struct.pack(f'{len(self.normals)}f', *self.normals))

	@Utils.time_task
	def _load_bin(self, path: str):
		with open(path, 'rb') as bin_file:
			num_vertices = struct.unpack('I', bin_file.read(4))[0]
			self.vertices = list(struct.unpack(f'{num_vertices * 3}f', bin_file.read(4 * num_vertices * 3)))
			self.normals = list(struct.unpack(f'{num_vertices * 3}f', bin_file.read(4 * num_vertices * 3)))

	def _interleaved_array(self):
		num_vertices = len(self.vertices) // 3
		combined = np.zeros((num_vertices, 6), dtype=np.float32)

		for i in range(num_vertices):
			combined[i, 0:3] = self.vertices[i * 3:i * 3 + 3]  # Vertex coordinates
			combined[i, 3:6] = self.normals[i * 3:i * 3 + 3]  # Normal coordinates


		return combined.flatten()

	def draw(self, shader: Shader = None, position = (0, 0, 0), scale = (1, 1, 1), rotation = (0, 0, 0)):
		model = glm.mat4(1)

		model = glm.translate(model, glm.vec3(position))
		model = glm.rotate(model, glm.radians(rotation[0]), glm.vec3(1, 0, 0))
		model = glm.rotate(model, glm.radians(rotation[1]), glm.vec3(0, 1, 0))
		model = glm.rotate(model, glm.radians(rotation[2]), glm.vec3(0, 0, 1))
		model = glm.scale(model, glm.vec3(scale))

		if shader is not None:
			shader.set_uniform("model", model, "mat4")
		elif model != glm.mat4(1):
			print("WARNING: No shader provided. Transforms will not be applied to the model.")

		glBindVertexArray(self.vao)
		total_vertices = len(self.vertices) // 3
		#glDrawArraysInstanced(GL_TRIANGLES, 0, total_vertices, 3)
		glDrawArrays(GL_TRIANGLES, 0, total_vertices)
		glBindVertexArray(0)

	def __call__(self, **kwargs):
		self.draw(**kwargs)

def save_as_obj(vertices, normals, indexes, path: str):
	obj_content = []
	for v in vertices:
		obj_content.append(f"v {' '.join(map(str, v))}")
	for n in normals:
		obj_content.append(f"vn {' '.join(map(str, n))}")
	for i in range(0, len(indexes), 3):
		obj_content.append(
			f"f {indexes[i] + 1}//{indexes[i] + 1} {indexes[i + 1] + 1}//{indexes[i + 1] + 1} {indexes[i + 2] + 1}//{indexes[i + 2] + 1}")

	obj_output = "\n".join(obj_content)
	with open(path, 'w') as obj_file:
		obj_file.write(obj_output)