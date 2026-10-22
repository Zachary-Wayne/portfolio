"""
Excerpt from TODNT's utils.py: record intermediate images from the grid
detector and export them as animated GIFs for debugging.
"""
from typing import Tuple, Union

import numpy as np
from PIL import Image


class MaskDebugger:
	_masks: dict[Tuple[int, int], np.ndarray] = {}
	_frames: list[np.ndarray] = []

	_max_frame_h: int = 0
	_max_frame_w: int = 0

	_cur_row: int = 0

	background_colour: Union[int, Tuple[int, int, int]] = (120, 180, 190)

	@classmethod
	def add_mask(cls, mask_array: Union[np.ndarray, list], swap_axes=False) -> None:
		mask = np.asarray(mask_array, dtype=bool)

		if mask.ndim == 1:
			mask = np.expand_dims(mask, axis=0)
			mask = np.repeat(mask, 10, axis=0)
		elif mask.ndim == 2:
			# noinspection PyTupleAssignmentBalance
			h, w = mask.shape
			if h < 10:
				mask = np.repeat(mask, 10, axis=0)
			if w < 10:
				mask = np.repeat(mask, 10, axis=1)

		existing_cols = [col for (r, col) in cls._masks.keys() if r == cls._cur_row]
		col = max(existing_cols) + 1 if existing_cols else 0

		if swap_axes:
			mask = np.swapaxes(mask, 0, 1)
		cls._masks[(cls._cur_row, col)] = mask

	@classmethod
	def new_row(cls) -> None:
		cls._cur_row += 1

	@classmethod
	def _render_current_canvas(cls, padding: Tuple[int, int]) -> np.ndarray:
		if not cls._masks:
			pad_y, pad_x = padding
			shape = (pad_y, pad_x, 3) if isinstance(cls.background_colour, (tuple, list)) else (pad_y, pad_x)
			return np.full(shape, cls.background_colour, dtype=np.uint8)

		pad_y, pad_x = padding

		coords = np.array(list(cls._masks.keys()))
		max_row = coords[:, 0].max()
		max_col = coords[:, 1].max()

		row_heights = np.zeros(max_row + 1, dtype=int)
		col_widths = np.zeros(max_col + 1, dtype=int)

		for (r, c), mask in cls._masks.items():
			h, w = mask.shape
			if h > row_heights[r]: row_heights[r] = h
			if w > col_widths[c]: col_widths[c] = w

		row_offsets = np.zeros(max_row + 2, dtype=int)
		row_offsets[0] = pad_y
		row_offsets[1:] = pad_y + np.cumsum(row_heights + pad_y)
		total_y = row_offsets[max_row] + row_heights[max_row] + pad_y

		col_offsets = np.zeros(max_col + 2, dtype=int)
		col_offsets[0] = pad_x
		col_offsets[1:] = pad_x + np.cumsum(col_widths + pad_x)
		total_x = col_offsets[max_col] + col_widths[max_col] + pad_x

		is_rgb = isinstance(cls.background_colour, (tuple, list)) and len(cls.background_colour) == 3
		canvas_shape = (total_y, total_x, 3) if is_rgb else (total_y, total_x)

		canvas = np.full(canvas_shape, cls.background_colour, dtype=np.uint8)

		for (r, c), mask in cls._masks.items():
			y_start = row_offsets[r]
			x_start = col_offsets[c]
			h, w = mask.shape
			canvas_slice = canvas[y_start: y_start + h, x_start: x_start + w]
			if is_rgb:
				canvas_slice[~mask] = (0, 0, 0)
				canvas_slice[mask] = (255, 255, 255)
			else:
				canvas_slice[~mask] = 0
				canvas_slice[mask] = 255

		return canvas

	"""
	@classmethod
	def display_all(cls, padding: Tuple[int, int] = (10, 10)) -> None:
		if not cls._masks:
			print("MaskDebugger: No masks to display.")
			return

		canvas = cls._render_current_canvas(padding)
		plt.figure(figsize=(10, 10))
		plt.imshow(canvas, cmap='gray')
		plt.axis('off')
		plt.show()
	"""

	@classmethod
	def save_frame(cls, padding: Tuple[int, int] = (10, 10)) -> None:
		if not cls._masks:
			return
		canvas = cls._render_current_canvas(padding)
		h, w = canvas.shape[:2]
		cls._max_frame_h = max(cls._max_frame_h, h)
		cls._max_frame_w = max(cls._max_frame_w, w)
		cls._frames.append(canvas)
		cls.clear()

	@classmethod
	def export_gif(cls, output_path: str = "masks_animation.gif", fps: int = 20) -> None:
		if not cls._frames:
			if not cls._masks:
				print("MaskDebugger: No masks or saved frames stored to export.")
				return
			canvas = cls._render_current_canvas((10, 10))
			img = Image.fromarray(canvas.astype(np.uint8))
			duration_ms = int(1000 / fps)
			img.save(output_path, save_all=True, duration=duration_ms, loop=0)
			print("MaskDebugger: No masks or saved frames stored to export.")
			return

		is_rgb = isinstance(cls.background_colour, (tuple, list)) and len(cls.background_colour) == 3
		standardized_frames = []

		for frame in cls._frames:
			h, w = frame.shape[:2]
			pad_h = cls._max_frame_h - h
			pad_w = cls._max_frame_w - w

			if pad_h > 0 or pad_w > 0:
				if is_rgb:
					padded_frame = np.pad(
						frame,
						((0, pad_h), (0, pad_w), (0, 0)),
						mode='constant'
					)
					if pad_h > 0:
						padded_frame[h:, :, :] = cls.background_colour
					if pad_w > 0:
						padded_frame[:h, w:, :] = cls.background_colour
				else:
					padded_frame = np.pad(
						frame,
						((0, pad_h), (0, pad_w)),
						mode='constant',
						constant_values=cls.background_colour
					)
				standardized_frames.append(padded_frame)
			else:
				standardized_frames.append(frame)

		print(f"MaskDebugger: Exporting GIF with {len(standardized_frames)} frames to {output_path}...")

		pil_images = [Image.fromarray(frame.astype(np.uint8)) for frame in standardized_frames]
		duration_ms = int(1000 / fps)

		pil_images[0].save(
			output_path,
			save_all=True,
			append_images=pil_images[1:],
			duration=duration_ms,
			loop=0
		)
		print(f"MaskDebugger: Saved GIF to {output_path}.")

	@classmethod
	def clear(cls) -> None:
		cls._masks = {}
		cls._cur_row = 0

	@classmethod
	def clear_all(cls) -> None:
		cls._masks, cls._frames = {}, []
		cls._max_frame_h, cls._max_frame_w = 0, 0
		cls._cur_row = 0


class GridDebugger:
	"""Captures colour images (OpenCV RGB) and compiles them into an animated GIF."""
	_frames = []

	@classmethod
	def capture_image(cls, rgb_image: np.ndarray) -> None:
		if rgb_image is None:
			return
		cls._frames.append(rgb_image)

	@classmethod
	def export_gif(cls, output_path: str = "debug_animation.gif", fps: int = 5) -> None:
		if not cls._frames:
			print("GridDebugger: No frames captured to export.")
			return
		else:
			print(f"GridDebugger: Exporting GIF with {len(cls._frames)} frames to {output_path}...")

		target_h, target_w = cls._frames[0].shape[:2]
		processed_frames = []
		for frame in cls._frames:
			if frame.shape[:2] != (target_h, target_w):
				frame = np.array(Image.fromarray(frame).resize((target_w, target_h), Image.Resampling.BILINEAR))
			processed_frames.append(frame)

		pil_images = [Image.fromarray(frame.astype(np.uint8)) for frame in processed_frames]
		duration_ms = int(1000 / fps)

		pil_images[0].save(
			output_path,
			save_all=True,
			append_images=pil_images[1:],
			duration=duration_ms,
			loop=0
		)
		print(f"GridDebugger: Saved GIF to {output_path}.")

	@classmethod
	def clear(cls) -> None:
		cls._frames = []
