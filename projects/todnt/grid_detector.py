from dataclasses import dataclass

import numpy as np
import cv2

import default_configs
from utils import line_intersection, MaskUtils, ImageProcessorUtils, fit_x_over_y, profiler_attach
from geometry import Line, Box, Point


class GridDetectionError(Exception):
	""" If the grid detection fails for whatever non-fatal reason, this exception class will be thrown."""
	pass


@dataclass(frozen=True)
class _GridRegionCandidate:
	header_box: Box
	grid_box: Box

	@property
	def header_height(self) -> float:
		return self.header_box.h

	@property
	def grid_height(self) -> float:
		return self.grid_box.h

	@property
	def grid_width(self) -> float:
		return self.grid_box.w


@dataclass(frozen=True)
class _GridCandidate(_GridRegionCandidate):
	vertical_lines: list[Line]
	horizontal_lines: list[Line]

	@property
	def horizontal_line_count(self) -> int:
		return len(self.horizontal_lines)

	@property
	def vertical_line_count(self) -> int:
		return len(self.vertical_lines)


@dataclass(frozen=True)
class _GridScore:
	header: float
	grid_height: float
	grid_width: float
	horizontal_lines: float
	vertical_lines: float
	vertical_slant: float

	@property
	def region_score(self) -> float:
		return (self.header + self.grid_height + self.grid_width) / 3

	@property
	def line_score(self) -> float:
		return (self.horizontal_lines + self.vertical_lines + self.vertical_slant) / 3

	@property
	def total(self) -> float:
		return (self.region_score + self.line_score) / 2

	def __str__(self) -> str:
		return (
			f"Score: {self.total:.3f}\n"
			f"\tHeader:             {self.header:.3f}\n"
			f"\tGrid height:        {self.grid_height:.3f}\n"
			f"\tGrid width:         {self.grid_width:.3f}\n"
			f"\tHorizontal lines:   {self.horizontal_lines:.3f}\n"
			f"\tVertical lines:     {self.vertical_lines:.3f}\n"
			f"\tVertical slant:     {self.vertical_slant:.3f}\n"
		)


@dataclass(frozen=True)
class _GridSearchResult:
	angle: float
	threshold: int
	tolerance: float | None
	candidate: _GridCandidate
	score: _GridScore


class GridDetector:
	img: np.ndarray
	img_grey: np.ndarray
	img_debug: np.ndarray
	img_processed: np.ndarray
	mask: np.ndarray

	def __init__(self, img: np.ndarray, args: default_configs.GridDetectorArgs = default_configs.GridDetectorArgs()):
		self.img = img
		self.args = args
		self.img_grey = ImageProcessorUtils.greyscale(img)
		self.img_debug = img.copy()
		self.img_processed = img.copy()

		self._vertical_line_history: list[list[Line]] = []
		self._vertical_line_history_max = 64

	def _score_candidate(self, candidate: _GridCandidate) -> _GridScore:
		image_height, image_width = self.img.shape[:2]

		def error(value, expected):
			return abs(value - expected) / expected

		vertical_slopes = []
		for line in candidate.vertical_lines:
			dy = line.end.y - line.start.y
			dx = line.end.x - line.start.x
			if dy != 0:
				vertical_slopes.append(dx / dy)
		if vertical_slopes:
			median_slope = np.median(vertical_slopes)
			slant_error = np.mean(np.abs(np.array(vertical_slopes) - median_slope))
		else:
			slant_error = 1

		return _GridScore(
			header=error(candidate.header_height, self.args.header_height),
			grid_height=error(candidate.grid_height, self.args.grid_height_ratio * image_height),
			grid_width=error(candidate.grid_width, self.args.grid_width_ratio * image_width),
			horizontal_lines=error(candidate.horizontal_line_count / self.args.expected_horizontal_lines, 1),
			vertical_lines=error(candidate.vertical_line_count / self.args.expected_vertical_lines, 1),
			vertical_slant=float(min(1, slant_error))
		)

	def _get_regions(self) -> tuple[Box, Box]:
		horizontal_mask = MaskUtils.average_axis(self.mask, 'x', self.args.min_tolerance)

		(header_top, header_bottom), header_height = MaskUtils.find_longest_streak(horizontal_mask)
		grid_bottom = MaskUtils.last_index(horizontal_mask)
		header_mask = self.mask[header_top:header_bottom]

		vertical_header_mask = MaskUtils.average_axis(header_mask, 'y', self.args.min_tolerance)

		right = MaskUtils.first_index(vertical_header_mask, 1)
		left = MaskUtils.last_index(vertical_header_mask, 1)

		header_box = Box([left, header_top], [right, header_bottom])
		grid_box = Box([left, header_bottom], [right, grid_bottom])

		return header_box, grid_box

	def _get_horizontal_lines(self, grid_box: Box, tolerance) -> list[Line]:
		padding = self.args.grid_padding
		y_offset = grid_box.top - padding
		y_end = grid_box.bottom + padding
		xl_1 = grid_box.left - padding
		xl_2 = grid_box.left + padding
		xr_1 = grid_box.right - padding
		xr_2 = grid_box.right + padding

		left_mask = MaskUtils.average_axis(self.mask[y_offset:y_end, xl_1:xl_2], 'x', tolerance)
		right_mask = MaskUtils.average_axis(self.mask[y_offset:y_end, xr_1:xr_2], 'x', tolerance)

		left_bounds_rel = MaskUtils.group_mask_features(left_mask, min_size=2, min_spacing=100)
		right_bounds_rel = MaskUtils.group_mask_features(right_mask, min_size=2, min_spacing=100)

		left_abs = np.maximum(np.array(left_bounds_rel) + y_offset, grid_box.y) if left_bounds_rel else np.empty((0, 2), dtype=int)
		right_abs = np.maximum(np.array(right_bounds_rel) + y_offset, grid_box.y) if right_bounds_rel else np.empty((0, 2), dtype=int)

		left_means = np.mean(left_abs, axis=1, dtype=int)
		right_means = np.mean(right_abs, axis=1, dtype=int)

		horizontal_lines = [Line(Point(xl_1, y1), Point(xr_2, y2)) for y1, y2 in zip(left_means, right_means)]
		return horizontal_lines

	def _get_vertical_lines(self, grid_box: Box, horizontal_lines, tolerance) -> list[Line]:
		t_y1 = grid_box.y - self.args.grid_padding
		t_y2 = grid_box.p3.y + self.args.grid_padding
		all_points = []
		# MaskDebugger.clear()
		for top_line, bottom_line in zip(horizontal_lines[:-1], horizontal_lines[1:]):
			y1, y2 = top_line.start.y, bottom_line.end.y
			y = (y1 + y2) // 2
			vertical_row_mask = MaskUtils.average_axis(self.mask[y1:y2], 'y', tolerance)
			vertical_features = MaskUtils.group_mask_features(vertical_row_mask, min_spacing=100, min_size=2, max_size=10)
			# MaskDebugger.add_mask(MaskUtils.bounds_to_mask(vertical_features, len(vertical_row_mask)))
			# MaskDebugger.new_row()
			all_points.append([((bound[0] + bound[1]) // 2, y) for bound in vertical_features])
		feature_counts = [len(row) for row in all_points]
		if not feature_counts:
			return []
		expected_count = max(set(feature_counts), key=feature_counts.count)
		valid_rows = [row for row in all_points if len(row) == expected_count]
		# MaskDebugger.save_frame()
		if len(valid_rows) <= len(all_points) // 2:
			raise GridDetectionError("Majority of rows do not have a consistent number of vertical features.")
		arr = np.array(valid_rows)
		y_coords, x_coords = arr[:, :, 1].T, arr[:, :, 0].T
		lines = []
		for y_c, x_c in zip(y_coords, x_coords):
			slope, intercept = fit_x_over_y(y_c, x_c)
			x1, x2 = slope * t_y1 + intercept, slope * t_y2 + intercept
			lines.append(Line(Point(int(round(x1)), int(round(t_y1))), Point(int(round(x2)), int(round(t_y2)))))
		self._vertical_line_history.append(lines)
		if len(self._vertical_line_history) > self._vertical_line_history_max:
			self._vertical_line_history.pop(0)
		return self._get_vertical_line_consensus(t_y1, t_y2)

	def _get_vertical_line_consensus(self, y1: int, y2: int) -> list[Line]:
		if not self._vertical_line_history:
			return []
		counts = [len(lines) for lines in self._vertical_line_history]
		expected_count = max(set(counts), key=counts.count)
		history = [lines for lines in self._vertical_line_history if len(lines) == expected_count]
		if not history:
			return []
		y_mid = (y1 + y2) / 2
		for lines in history:
			lines.sort(key=lambda _line: self._line_x_at_y(_line, y_mid))
		consensus = []
		for i in range(expected_count):
			slopes, intercepts = [], []
			for lines in history:
				line = lines[i]
				slope, intercept = fit_x_over_y(np.array([line.start.y, line.end.y]), np.array([line.start.x, line.end.x]))
				slopes.append(slope)
				intercepts.append(intercept)
			slope, intercept = float(np.median(slopes)), float(np.median(intercepts))
			x1, x2 = slope * y1 + intercept, slope * y2 + intercept
			consensus.append(Line(Point(int(round(x1)), int(round(y1))), Point(int(round(x2)), int(round(y2)))))
		return consensus

	@staticmethod
	def _line_x_at_y(line: Line, y: float) -> float:
		if line.end.y == line.start.y: return float(line.start.x)
		slope = ((line.end.x - line.start.x) / (line.end.y - line.start.y))
		return line.start.x + slope * (y - line.start.y)

	@staticmethod
	def _reshape_grid(horizontal_lines: list[Line], vertical_lines: list[Line]) -> tuple[list[Line], list[Line], Box]:
		new_horizontal_lines: list[Line] = []
		for line in horizontal_lines:
			new_left_point = line_intersection(line, vertical_lines[0])
			new_right_point = line_intersection(line, vertical_lines[-1])
			new_horizontal_lines.append(Line(new_left_point, new_right_point))
		new_vertical_lines: list[Line] = []
		for line in vertical_lines:
			new_top_point = line_intersection(line, horizontal_lines[0])
			new_bottom_point = line_intersection(line, horizontal_lines[-1])
			new_vertical_lines.append(Line(new_top_point, new_bottom_point))
		top_left = new_horizontal_lines[0].start
		top_right = new_horizontal_lines[0].end
		bottom_right = new_horizontal_lines[-1].start
		bottom_left = new_horizontal_lines[-1].end
		new_grid_box = Box(top_left, top_right, bottom_right, bottom_left)

		return new_horizontal_lines, new_vertical_lines, new_grid_box

	def _get_cell_grid(self, horizontal_lines: list[Line], vertical_lines: list[Line]) -> list[list[Box]]:
		intersection_matrix: list[list[Point]] = []
		for horizontal_line in horizontal_lines:
			intersection_row: list[Point] = []
			for vertical_line in vertical_lines:
				i = line_intersection(horizontal_line, vertical_line)
				intersection_row.append(i)
			intersection_matrix.append(intersection_row)
		num_rows = len(horizontal_lines) - 1
		num_cols = len(vertical_lines) - 1
		cell_grid: list[list[Box]] = []
		for row_index in range(num_rows):
			cell_row: list[Box] = []
			for col_index in range(num_cols):
				tl = intersection_matrix[row_index][col_index]
				tr = intersection_matrix[row_index][col_index + 1]
				br = intersection_matrix[row_index + 1][col_index + 1]
				bl = intersection_matrix[row_index + 1][col_index]
				cell = Box(tl, tr, br, bl)
				cv2.polylines(self.img_processed, [cell.np_pts], isClosed=True, color=(255, 255, 255), thickness=5, )
				cell_row.append(cell)
			cell_grid.append(cell_row)
		return cell_grid

	def _draw_debug(self, header_box, grid_box, horizontal_lines, vertical_lines):
		for line in horizontal_lines: cv2.line(self.img_debug, line[0], line[1], color=(155, 200, 100), thickness=2)
		for line in vertical_lines: cv2.line(self.img_debug, line[0], line[1], color=(0, 155, 255), thickness=2)
		cv2.polylines(self.img_debug, [header_box.np_pts], isClosed=True, color=(170, 102, 102), thickness=3)
		cv2.polylines(self.img_debug, [grid_box.np_pts], isClosed=True, color=(102, 170, 170), thickness=3)
		cv2.imwrite('debug_no_grid.png', self.img_processed)
		cv2.imwrite('debug_regions.png', self.img_debug)

	def _evaluate_angle(self, angle: float) -> list[_GridSearchResult]:
		grey = ImageProcessorUtils.rotate(self.img_grey, angle)
		results: list[_GridSearchResult] = []

		for threshold in range(self.args.min_threshold, self.args.max_threshold, self.args.threshold_step):
			self.mask = grey >= threshold
			try:
				header_box, grid_box = self._get_regions()
			except (GridDetectionError, ValueError, IndexError):
				continue

			candidate = _GridCandidate(header_box=header_box, grid_box=grid_box, horizontal_lines=[], vertical_lines=[])
			score = self._score_candidate(candidate)
			results.append(_GridSearchResult(angle=angle, threshold=threshold, tolerance=None, candidate=candidate, score=score))

		return results

	def _find_angle_range(self, min_angle: float, max_angle: float) -> tuple[float, float]:
		if max_angle - min_angle <= self.args.angle_accuracy:
			return min_angle, max_angle

		sample_count = 7
		angles = np.linspace(min_angle, max_angle, sample_count, dtype=float)
		angle_results: dict[float, list[_GridSearchResult]] = {}

		for angle in angles:
			if results := self._evaluate_angle(float(angle)):
				angle_results[float(angle)] = results

		if not angle_results:
			raise GridDetectionError(f"No valid grid regions between {min_angle:.3f}° and {max_angle:.3f}°")

		best_angle = min(angle_results, key=lambda _angle: min(r.score.region_score for r in angle_results[_angle]))
		best_index = int(np.argmin([abs(angle - best_angle) for angle in angles]))

		left_index, right_index = max(0, best_index - 1), min(sample_count - 1, best_index + 1)
		return self._find_angle_range(float(angles[left_index]), float(angles[right_index]))

	def _search_lines(self, angle: float, max_threshold_limit: int) -> _GridSearchResult | None:
		grey = ImageProcessorUtils.rotate(self.img_grey, float(angle))
		tolerances = np.arange(self.args.min_tolerance, (self.args.max_tolerance + self.args.tolerance_step), self.args.tolerance_step, dtype=float)
		best_result: _GridSearchResult | None = None
		best_score = float("inf")
		for threshold in range(self.args.min_threshold, max_threshold_limit, self.args.threshold_step):  # Lines don't need a big threshold
			self.mask = grey >= threshold
			try:
				header_box, grid_box = self._get_regions()
			except (GridDetectionError, ValueError, IndexError):
				continue
			for tolerance in tolerances:
				try:
					horizontal_lines = self._get_horizontal_lines(grid_box, float(tolerance))
					if len(horizontal_lines) < 2: continue
					vertical_lines = self._get_vertical_lines(grid_box, horizontal_lines, float(tolerance))
					if len(vertical_lines) < 2: continue
					candidate = _GridCandidate(header_box=header_box, grid_box=grid_box, horizontal_lines=horizontal_lines, vertical_lines=vertical_lines)
					score = self._score_candidate(candidate)
				except (GridDetectionError, ValueError, IndexError):
					continue
				result = _GridSearchResult(angle=float(angle), threshold=int(threshold), tolerance=float(tolerance), candidate=candidate, score=score)
				if score.line_score < best_score:
					best_score, best_result = score.line_score, result
		# MaskDebugger.export_gif()
		return best_result

	# @profiler_attach
	def detect_grid(self, start_angle: float | None = None):
		print('Looking for a grid...')
		start_angle = start_angle if start_angle is not None else self.args.angle_start
		min_angle, max_angle = self.args.min_angle, self.args.max_angle

		if start_angle is not None:
			angle_span = max(abs(max_angle - start_angle), abs(start_angle - min_angle))
			min_angle, max_angle = (max(min_angle, start_angle - angle_span), min(max_angle, start_angle + angle_span))

		min_angle, max_angle = self._find_angle_range(min_angle, max_angle)
		best_angle = (min_angle + max_angle) / 2
		print(f"Rotated image by {best_angle:.4f} degrees for best results.")

		angle_results = self._evaluate_angle(best_angle)
		if not angle_results:
			raise GridDetectionError(f"No valid grid candidates found at angle {best_angle:.4f}°")

		best_result = self._search_lines(best_angle, self.args.max_threshold)

		if best_result is None:
			raise GridDetectionError("No grid candidates found during line search.")

		print(f"Found grid! (Rating: {(1 - best_result.score.total) * 100:.0f}/100)")

		best_candidate, best_angle = best_result.candidate, best_result.angle

		self.img = ImageProcessorUtils.rotate(self.img, best_angle)
		self.img_grey = ImageProcessorUtils.greyscale(self.img)
		self.img_debug = self.img.copy()
		self.img_processed = self.img.copy()

		header_box = best_candidate.header_box
		horizontal_lines, vertical_lines, grid_box = self._reshape_grid(best_candidate.horizontal_lines, best_candidate.vertical_lines)
		cell_grid = self._get_cell_grid(horizontal_lines, vertical_lines)
		self._draw_debug(header_box, grid_box, horizontal_lines, vertical_lines)
		return cell_grid, grid_box, header_box, self.img_processed, best_angle


"""
detect_grid()
│
├── find_angle_range()
│   │
│   ├── evaluate_angle()
│   │   └── threshold search
│   │       └── get_regions()
│   │           └── region_score
│   │
│   ├── narrow interval
│   │
│   └── evaluate_angle() # Recurse until desired precision reached
│
└── search_lines()
    │
    ├── fine angles
    ├── thresholds
    ├── tolerances
    │
    ├── get_regions()
    ├── get_horizontal_lines()
    ├── get_vertical_lines()
    └── total score
"""
