"""
This module contains functions that set up and runs various pipeline tasks, such as converting PNGs to CSVs, labelling grids, and training OCR models.
This module does NOT contain the algorithms used in any process, but is rather the handler between the file IO and the underlying systems.

TL;DR, this module is the Input Output handler between the user and the math.
"""
import io
import os
import tkinter as tk
import uuid
from dataclasses import dataclass
from datetime import datetime
from tkinter import ttk
from typing import Generator, Union

import pymupdf as fitz
from PIL import Image, UnidentifiedImageError

from default_configs import SessionConfigArgs
from image_converter import ImageConverter
from ocr_resource_manager import OCRResourceManager

from training_data import TrainingDataGrid
from training_data_gatherer import GridTrainingDataGathererApp


def run_conversion_session(
		input_path: str,
		output_path: str,
		session_config: SessionConfigArgs
) -> Generator[tuple[int, int, list[str]], None, None]:
	"""
	This function acts as the primary entry point for document conversion.
	It automatically detects grids from standard images or PDFs, handles batch or single-file inputs, and writes the extracted table data to CSV files.
	"""
	try:
		yield from _png_to_csv(input_path, output_path, session_config)
	except UnidentifiedImageError:
		print("This is not an image file! Attempting PDF bulk conversion.")
		for event in png_input_generator(input_path, session_config):
			if isinstance(event, PageDoneEvent):
				print(f"Done with page {event.current_index}...")
			elif isinstance(event, GridFoundEvent):
				yield from _png_to_csv(event.saved_path, output_path, session_config)
			elif isinstance(event, GridNotFoundEvent):
				print(f"No grid found.")


def print_conversion_session(input_path: str, output_path: str, session_config: SessionConfigArgs, ) -> None:
	"""Run a conversion session and render its output for a CLI."""
	previous_row = None
	for row_idx, _, row in run_conversion_session(input_path, output_path, session_config):
		row_str = "\t".join(row)
		if row_idx == previous_row:
			print(f"\r{row_str}", end="", flush=True)
		else:
			print(f"\n{row_str}", end="", flush=True)
		previous_row = row_idx
	print()


def _png_to_csv(
		input_path: str,
		output_path: str,
		session_config: SessionConfigArgs,
) -> Generator[tuple[int, int, list[str]], None, None]:
	"""Determines the output destination path and converts the document to CSV."""
	is_csv_target = output_path.lower().endswith(".csv")

	source_location = ""
	with Image.open(input_path) as img:
		source_location = str(img.info.get("source_location"))

	if is_csv_target:
		parent_dir = os.path.dirname(output_path)
		target_filename = os.path.basename(source_location)
		csv_destination_path = os.path.join(parent_dir, target_filename) if parent_dir else target_filename
	else:
		csv_destination_path = os.path.join(output_path, source_location)

	converter = ImageConverter(input_path, session_config)
	# converter.save_debug_grid_image(os.path.join(session_config.path_args.debug_dir, "debug_cells.png"))
	yield from converter.export_to_csv_generator(csv_destination_path)


def run_labelling_session(input_path: str, model_path: str | None, session_config: SessionConfigArgs):
	"""This function processes an input image, detects its grid structure, and initializes the labelling application"""
	print(f"Started labelling: {input_path}")

	converter = ImageConverter(input_path, session_config=session_config)
	converter.save_debug_grid_image(os.path.join(session_config.path_args.debug_dir, "debug_cells.png"))
	training_data_grid: TrainingDataGrid = converter.gather_training_data()

	if model_path:
		OCRResourceManager().load_tr_ocr(model_path)

	if len(training_data_grid) > 0:
		root_window = tk.Toplevel()

		local_style = ttk.Style(root_window)
		local_style.theme_use("clam")

		# noinspection PyTypeChecker
		_ = GridTrainingDataGathererApp(
			root_window,
			source_image_path=input_path,
			ocr_interface_image=converter.processed_image,
			data_training_grid=training_data_grid,
			training_data_dir=str(SessionConfigArgs().path_args.training_data_dir)
		)

		root_window.wait_window()
	# print(f"Saved {input_path} to history.")
	else:
		print("No text cells found.")


def run_training_session(new_model_path: str, session_config: SessionConfigArgs):
	"""Trains a new OCR model using accumulated training data at the location specified in the config args, and saves it to a specified path."""
	OCRResourceManager().train_tr_ocr(str(session_config.path_args.training_data_dir), new_model_path)


def debug_grid_detector(
		input_path: str,
		session_config: SessionConfigArgs
):
	"""For debugging the grid detector."""
	print(f"Debugging: {input_path}")
	converter = ImageConverter(input_path, session_config=session_config)
	converter.save_debug_grid_image(os.path.join(session_config.path_args.debug_dir, "debug_image.png"))


@dataclass
class StartFileEvent:
	filename: str
	total_pages: int


@dataclass
class PageDoneEvent:
	filename: str
	current_index: int


@dataclass
class GridFoundEvent:
	filename: str
	saved_path: str
	thumbnail: Image.Image
	display_name: str


@dataclass
class GridNotFoundEvent:
	pass


@dataclass
class EndFileEvent:
	filename: str


@dataclass
class StreamCompleteEvent:
	pass


PipelineEvent = Union[StartFileEvent, PageDoneEvent, GridFoundEvent, GridNotFoundEvent, EndFileEvent, StreamCompleteEvent]


def png_input_generator(  # TODO: Figure out why everything is being saved to p9
		input_path: str | list[str],
		session_config: SessionConfigArgs,
		target_page: int = None
) -> Generator[PipelineEvent, None, None]:
	output_path = str(session_config.path_args.temp_dir)
	os.makedirs(output_path, exist_ok=True)

	base_dir = _get_base_directory(input_path)
	timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

	img_paths = []
	pdf_paths = []
	for file_path in _get_input_files(input_path):
		if file_path.lower().endswith(".pdf"):
			pdf_paths.append(file_path)
		else:
			img_paths.append(file_path)

	for img_path in img_paths:
		img_name = str(os.path.basename(img_path))
		source_path = os.path.relpath(img_path, base_dir) if base_dir else img_name
		yield StartFileEvent(filename=img_name, total_pages=1)

		# try:
		with Image.open(img_path) as image:
			if _has_existing_grid_metadata(image):
				print(f"Input image at {img_path} already has grid info!")

				img_thumb = image.copy()
				img_thumb.thumbnail((300, 300))
				yield GridFoundEvent(
					filename=img_name,
					saved_path=img_path,
					thumbnail=img_thumb,
					display_name=img_name
				)
			else:
				unique_key = source_path
				file_path = os.path.join(output_path, f"{uuid.uuid5(uuid.NAMESPACE_URL, unique_key).hex}.png")
				converter = ImageConverter(image, session_config)
				converter.save_with_metadata(img_path, file_path)

				img_thumb = Image.fromarray(converter.processed_image)
				img_thumb.thumbnail((300, 300))
				if file_path:
					yield GridFoundEvent(
						filename=img_name,
						saved_path=file_path,
						thumbnail=img_thumb,
						display_name=img_name
					)

		yield PageDoneEvent(filename=img_name, current_index=1)
		# except Exception as e:
		#	yield GridNotFoundEvent()
		#	print(e)

		yield EndFileEvent(filename=img_name)

	for pdf_path in pdf_paths:
		source_path = os.path.relpath(pdf_path, base_dir) if base_dir else os.path.basename(pdf_path)
		pdf_name = str(os.path.basename(pdf_path))
		pdf_base_name = os.path.splitext(pdf_name)[0]

		with fitz.open(pdf_path) as pdf_document:
			total_pages = len(pdf_document)
			pages_to_process = (
				[target_page]
				if target_page is not None and 0 <= target_page < total_pages
				else range(total_pages)
			)

			yield StartFileEvent(filename=pdf_name, total_pages=len(pages_to_process))
			parent_folder_name = f"{pdf_base_name}_{timestamp}"

			for idx, page_number in enumerate(pages_to_process):
				page = pdf_document.load_page(page_number)
				pix = page.get_pixmap(dpi=300)
				img_data = pix.tobytes("png")
				page_name = f"p{page_number + 1}"

				with Image.open(io.BytesIO(img_data)) as image:
					page = f"page_{page_number + 1}"
					file_path = os.path.join(output_path, f"{uuid.uuid5(uuid.NAMESPACE_URL, f"{source_path}{page}").hex}.png")
					converter = ImageConverter(image, session_config)
					try:
						converter.save_with_metadata(f'{parent_folder_name}/{page}', file_path)
					except Exception as e:
						print(e)
						continue

					img_thumb = Image.fromarray(converter.processed_image)
					img_thumb.thumbnail((300, 300))

					yield GridFoundEvent(
						filename=pdf_name,
						saved_path=file_path,
						thumbnail=img_thumb,
						display_name=page
					)

				yield PageDoneEvent(filename=pdf_name, current_index=idx + 1)

			yield EndFileEvent(filename=pdf_name)


def _get_input_files(input_paths, max_depth: int | None = None):
	"""Yields valid image and PDF file paths recursively from input sources."""
	if isinstance(input_paths, str):
		input_paths = [input_paths]

	valid_extensions = {".jpg", ".jpeg", ".png", ".pdf"}

	for path in input_paths:
		if os.path.isfile(path):
			if os.path.splitext(path)[1].lower() in valid_extensions:
				yield path
		elif os.path.isdir(path):
			for folder, dirs, files in os.walk(path):
				rel_dir = os.path.relpath(folder, path)
				depth = 0 if rel_dir == "." else len(rel_dir.split(os.sep))

				if max_depth is not None and depth >= max_depth:
					dirs.clear()

				if max_depth is not None and depth > max_depth:
					continue

				for file in files:
					if os.path.splitext(file)[1].lower() in valid_extensions:
						yield os.path.join(folder, file)


def _get_base_directory(input_path: str | list[str]) -> str:
	"""Determines the common root directory path from various input types."""
	if isinstance(input_path, list):
		return os.path.commonpath([os.path.dirname(p) for p in input_path]) if input_path else ""
	return os.path.dirname(input_path) if os.path.isfile(input_path) else input_path


def _has_existing_grid_metadata(image: Image.Image) -> bool:
	"""Checks whether an image file already contains embedded grid metadata tags."""
	required_keys = {"whole_grid_box", "header_box", "cell_grid"}
	return required_keys.issubset(image.info)
