"""
Configuration values for the OCR and other aspects of the application.

The data structure used in this file is designed to be easy to read and used. Some parts of the program are able to turn these arguments into GUI elements.
"""
import cv2

from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, field

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent


def config_param(default_value: Any, description: str = "No description."):
	"""Helper factory to group variable value and description metadata cleanly."""
	return field(default=default_value, metadata={"description": description})


@dataclass
class PathArgs:
	"""Configuration container for directory and file paths."""
	src_dir: Path = config_param(SRC_DIR, "Source directory path.")
	project_root: Path = config_param(PROJECT_ROOT, "Project root directory path.")
	input_folder: str = config_param("input", "Folder containing input files.")
	output_folder: str = config_param("output", "Folder for output files.")
	temp_folder: str = config_param("temp", "Folder for temporary processing files.")
	debug_folder: str = config_param("debug", "Folder for debug visual logs.")
	models_folder: str = config_param("fine_tuned_models", "Folder containing fine-tuned OCR models.")
	training_data_folder: str = config_param("labeled_data_NEW", "Folder for labeled data directory.")
	history_file: str = config_param("processed_files_hist.json", "Deprecated.")

	@property
	def input_dir(self) -> Path: return self.project_root / self.input_folder

	@property
	def output_dir(self) -> Path: return self.project_root / self.output_folder

	@property
	def temp_dir(self) -> Path: return self.project_root / self.temp_folder

	@property
	def debug_dir(self) -> Path: return self.project_root / self.debug_folder

	@property
	def models_dir(self) -> Path: return self.project_root / self.models_folder

	@property
	def training_data_dir(self) -> Path: return self.models_dir / self.training_data_folder

	@property
	def history_file_dir(self) -> Path: return self.models_dir / self.history_file

	"""Returns a full string path to a file inside the temp directory."""

	def get_temp_file(self, filename: str) -> Path:    return self.temp_dir / filename

	"""
	from pathlib import Path

	SRC_DIR = Path(__file__).resolve().parent
	PROJECT_ROOT = SRC_DIR.parent
	INPUT_DIR = str(PROJECT_ROOT / "input")
	OUTPUT_DIR = str(PROJECT_ROOT / "output")
	TEMP_DIR = str(PROJECT_ROOT / "temp")
	DEBUG_DIR = str(PROJECT_ROOT / "debug")
	MODELS_DIR = Path(PROJECT_ROOT / "fine_tuned_models")
	NEW_SCANS_DIR = str(PROJECT_ROOT / "new_scans")
	LABELED_DATA = str(MODELS_DIR / "labeled_data")
	HISTORY_FILE = str(MODELS_DIR / "processed_files_hist.json")


	def get_temp_file(filename: str) -> str:
		\"""Helper to quickly get an absolute path to a file inside the temp folder.\"""
		return str(PROJECT_ROOT / "temp" / filename)


	MODEL_1 = str(MODELS_DIR / "model_1")
	MODEL_2 = str(MODELS_DIR / "model_2")
	MODEL_3 = str(MODELS_DIR / "model_3")
	MODEL_4 = str(MODELS_DIR / "model_4")
	MODEL_5 = str(MODELS_DIR / "model_5")
	MODEL_6 = str(MODELS_DIR / "model_6")
	"""


@dataclass
class DebugArgs:
	"""Configuration for GridConverter debugging options"""
	colour_whole_grid: tuple = config_param((0, 200, 0), "RGB colour value drawn around the discovered outer grid bounds.")
	colour_header: tuple = config_param((0, 200, 0), "RGB colour marking out the bounding space of the table header columns.")
	colour_cell: tuple = config_param((0, 0, 255), "RGB colour marking regular isolated data row boxes.")
	colour_empty_cell: tuple = config_param((200, 150, 255), "RGB indicator colour to flag cells registering no feature shapes.")
	colour_text_box: tuple = config_param((100, 0, 100), "Colour highlighting individual tight character boundary crops.")

	line_thickness: int = config_param(4, "Standard pixel thickness applied to master visual debug elements.")
	line_thickness_whole_grid: int = config_param(4, "Outer frame boundary drawing thickness.")
	line_thickness_header: int = config_param(4, "Header panel line drawing thickness.")
	line_thickness_cell: int = config_param(2, "Inner cell grid lines extraction markup thickness.")

	text_font: int = config_param(cv2.FONT_HERSHEY_SIMPLEX, "Font type.")
	text_scale: float = config_param(1.0, "Font size.")
	text_weight: int = config_param(3, "Stroke line thickness thickness.")


@dataclass
class GridDetectorArgs:
	"""Configuration container for grid detection options. These have been configured to work with the 2026 trade sheets."""
	min_tolerance: float = config_param(0.5, "The minimum percentage for averaging calculations.")
	max_tolerance: float = config_param(0.9)
	tolerance_step: float = config_param(0.05)

	min_threshold: int = config_param(50, "The minimum mask threshold value.")
	max_threshold: int = config_param(200, "The maximum mask threshold value.")
	threshold_step: int = config_param(5, "The value to increment the threshold by on detection error.")

	min_angle: float = config_param(-1)
	max_angle: float = config_param(1)
	angle_accuracy: float = config_param(0.01, "How accurate of an angle to search to")
	angle_steps: float = config_param(10, "How many angles to search")
	angle_start: float = config_param(0.0, "Unused for now.")

	grid_padding: int = config_param(40, "The number of pixel padding around the detected grid box.")

	expected_horizontal_lines: int = config_param(18, "The number of rows(+1) the grid is expected to have.")
	expected_vertical_lines: int = config_param(10, "The number of columns(+1) the grid is expected to have.")
	grid_width_ratio: float = config_param(0.85, "Width ratio of the detected grid.")
	grid_height_ratio: float = config_param(0.75, "Height ratio of the detected grid.")
	header_height: float = config_param(70, "Height of the detected header in pixels.")

	# window_radius: int = config_param(10, "Pixel radius of the scanning window for intersection identification.")

	print_verbose: bool = config_param(True, "Print debug log information.")


@dataclass
class ImageProcessingArgs:
	"""Configuration arguments for image processing."""
	# deskew_method: Callable = config_param(ImageDeskewer.with_hough, "Algorithm strategy handle applied to calculate global document skew corrections.")
	# deskew_min_angle: float = config_param(-2)
	# deskew_max_angle: float = config_param(2)
	# deskew_starting_angle: float = config_param(0)
	# deskew_angle_step_count: float = config_param(50)
	add_text_margin_px: int = config_param(10, "Margin cushion added around individual extracted alphanumeric structures.")
	add_cell_padding_px: int = config_param(20, "Internal tracking padding buffer clearance enforced inside array cells.")
	crop_text_bound: bool = config_param(True, "Crop precisely to the tightest text bounding footprint before engine analysis.")
	denoise_strength: int = config_param(0, "Gaussian/Bilateral filter smoothing filter parameter index setting level.")
	convert_to_greyscale: bool = config_param(False, "Toggle force-converting target input textures to greyscale before evaluation loops.")


@dataclass
class SessionConfigArgs:
	"""Configuration container for session options"""
	path_args: PathArgs = field(default_factory=PathArgs)
	image_processing_args: ImageProcessingArgs = field(default_factory=ImageProcessingArgs)
	grid_detector_args: GridDetectorArgs = field(default_factory=GridDetectorArgs)
	debug_args: DebugArgs = field(default_factory=DebugArgs)

	def export_parameter_manifest(self) -> Dict[str, Dict[str, Any]]:
		""" Will print all the config values in a formated manifest """
		manifest = {}

		sub_configs = {
			"path_args": self.path_args,
			"image_processing_args": self.image_processing_args,
			"grid_detector_args": self.grid_detector_args,
			"debug_args": self.debug_args
		}

		for category, config_obj in sub_configs.items():
			manifest[category] = {}
			# noinspection PyUnresolvedReferences
			for field_name, field_def in config_obj.__dataclass_fields__.items():
				current_val = getattr(config_obj, field_name)
				description = field_def.metadata.get("description", "No description.")

				manifest[category][field_name] = {
					"variable_name": field_name,
					"value": current_val,
					"description": description
				}
		return manifest
