# Source File Documentation

## File: `todnt\default_configs.py`

### Module Description
> Configuration values for the OCR and other aspects of the application.<br><br>The data structure used in this file is designed to be easy to read and used. Some parts of the program are able to turn these arguments into GUI elements.

### Contents

<details>
<summary><b>Imports & Dependencies</b></summary><br>

`cv2`, `dataclasses.dataclass`, `dataclasses.field`, `pathlib.Path`, `typing.Any`, `typing.Dict`

</details>

<details>
<summary><b>Module Variables & Constants</b></summary><br>

| Variable | Type | Default Value |
| :--- | :--- | :--- |
| `SRC_DIR` | `...` | `Path(__file__).resolve().parent` |
| `PROJECT_ROOT` | `...` | `SRC_DIR.parent` |

</details>

<details>
<summary><b>Standalone Functions</b></summary><br>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `config_param` | Helper factory to group variable value and description metadata cleanly. | `default_value: Any, description: str = 'No description.'` | `field()`, `Any` |

</details>

<details>
<summary><b>Class:</b> <code>PathArgs</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_Configuration container for directory and file paths._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `src_dir` | Source directory path. | `Path` | `SRC_DIR` |
| `project_root` | Project root directory path. | `Path` | `PROJECT_ROOT` |
| `input_folder` | Folder containing input files. | `str` | `'input'` |
| `output_folder` | Folder for output files. | `str` | `'output'` |
| `temp_folder` | Folder for temporary processing files. | `str` | `'temp'` |
| `debug_folder` | Folder for debug visual logs. | `str` | `'debug'` |
| `models_folder` | Folder containing fine-tuned OCR models. | `str` | `'fine_tuned_models'` |
| `training_data_folder` | Folder for labeled data directory. | `str` | `'labeled_data_NEW'` |
| `history_file` | Deprecated. | `str` | `'processed_files_hist.json'` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `@property input_dir` | ... | `self` | `Path` |
| `@property output_dir` | ... | `self` | `Path` |
| `@property temp_dir` | ... | `self` | `Path` |
| `@property debug_dir` | ... | `self` | `Path` |
| `@property models_dir` | ... | `self` | `Path` |
| `@property training_data_dir` | ... | `self` | `Path` |
| `@property history_file_dir` | ... | `self` | `Path` |
| `get_temp_file` | ... | `self, filename: str` | `Path` |

</details>

<details>
<summary><b>Class:</b> <code>DebugArgs</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_Configuration for GridConverter debugging options_


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `colour_whole_grid` | RGB colour value drawn around the discovered outer grid bounds. | `tuple` | `(0, 200, 0)` |
| `colour_header` | RGB colour marking out the bounding space of the table header columns. | `tuple` | `(0, 200, 0)` |
| `colour_cell` | RGB colour marking regular isolated data row boxes. | `tuple` | `(0, 0, 255)` |
| `colour_empty_cell` | RGB indicator colour to flag cells registering no feature shapes. | `tuple` | `(200, 150, 255)` |
| `colour_text_box` | Colour highlighting individual tight character boundary crops. | `tuple` | `(100, 0, 100)` |
| `line_thickness` | Standard pixel thickness applied to master visual debug elements. | `int` | `4` |
| `line_thickness_whole_grid` | Outer frame boundary drawing thickness. | `int` | `4` |
| `line_thickness_header` | Header panel line drawing thickness. | `int` | `4` |
| `line_thickness_cell` | Inner cell grid lines extraction markup thickness. | `int` | `2` |
| `text_font` | Font type. | `int` | `cv2.FONT_HERSHEY_SIMPLEX` |
| `text_scale` | Font size. | `float` | `1.0` |
| `text_weight` | Stroke line thickness thickness. | `int` | `3` |

</details>

<details>
<summary><b>Class:</b> <code>GridDetectorArgs</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_Configuration container for grid detection options. These have been configured to work with the 2026 trade sheets._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `min_tolerance` | The minimum percentage for averaging calculations. | `float` | `0.5` |
| `max_tolerance` | ... | `float` | `0.9` |
| `tolerance_step` | ... | `float` | `0.05` |
| `min_threshold` | The minimum mask threshold value. | `int` | `50` |
| `max_threshold` | The maximum mask threshold value. | `int` | `200` |
| `threshold_step` | The value to increment the threshold by on detection error. | `int` | `5` |
| `min_angle` | ... | `float` | `-1` |
| `max_angle` | ... | `float` | `1` |
| `angle_accuracy` | How accurate of an angle to search to | `float` | `0.01` |
| `angle_steps` | How many angles to search | `float` | `10` |
| `angle_start` | Unused for now. | `float` | `0.0` |
| `grid_padding` | The number of pixel padding around the detected grid box. | `int` | `40` |
| `expected_horizontal_lines` | The number of rows(+1) the grid is expected to have. | `int` | `18` |
| `expected_vertical_lines` | The number of columns(+1) the grid is expected to have. | `int` | `10` |
| `grid_width_ratio` | Width ratio of the detected grid. | `float` | `0.85` |
| `grid_height_ratio` | Height ratio of the detected grid. | `float` | `0.75` |
| `header_height` | Height of the detected header in pixels. | `float` | `70` |
| `print_verbose` | Print debug log information. | `bool` | `True` |

</details>

<details>
<summary><b>Class:</b> <code>ImageProcessingArgs</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_Configuration arguments for image processing._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `add_text_margin_px` | Margin cushion added around individual extracted alphanumeric structures. | `int` | `10` |
| `add_cell_padding_px` | Internal tracking padding buffer clearance enforced inside array cells. | `int` | `20` |
| `crop_text_bound` | Crop precisely to the tightest text bounding footprint before engine analysis. | `bool` | `True` |
| `denoise_strength` | Gaussian/Bilateral filter smoothing filter parameter index setting level. | `int` | `0` |
| `convert_to_greyscale` | Toggle force-converting target input textures to greyscale before evaluation loops. | `bool` | `False` |

</details>

<details>
<summary><b>Class:</b> <code>SessionConfigArgs</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_Configuration container for session options_


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `path_args` | ... | `PathArgs` | `PathArgs()` |
| `image_processing_args` | ... | `ImageProcessingArgs` | `ImageProcessingArgs()` |
| `grid_detector_args` | ... | `GridDetectorArgs` | `GridDetectorArgs()` |
| `debug_args` | ... | `DebugArgs` | `DebugArgs()` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `export_parameter_manifest` | Will print all the config values in a formated manifest | `self` | `Any`, `Dict` |

</details>

## File: `todnt\grid_detector.py`

### Contents

<details>
<summary><b>Imports & Dependencies</b></summary><br>

`cv2`, `dataclasses.dataclass`, `default_configs`, `geometry.Box`, `geometry.Line`, `geometry.Point`, `numpy`, `utils.ImageProcessorUtils`, `utils.MaskUtils`, `utils.fit_x_over_y`, `utils.line_intersection`, `utils.profiler_attach`

</details>

<details>
<summary><b>Class:</b> <code>GridDetectionError(Exception)</code></summary><br>

_If the grid detection fails for whatever non-fatal reason, this exception class will be thrown._

</details>

<details>
<summary><b>Class:</b> <code>_GridRegionCandidate</code></summary><br>

<b>Decorators:</b> <code>@dataclass(frozen=True)</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `header_box` | ... | `Box` | `...` |
| `grid_box` | ... | `Box` | `...` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `@property header_height` | ... | `self` | *None* |
| `@property grid_height` | ... | `self` | *None* |
| `@property grid_width` | ... | `self` | *None* |

</details>

<details>
<summary><b>Class:</b> <code>_GridCandidate(_GridRegionCandidate)</code></summary><br>

<b>Decorators:</b> <code>@dataclass(frozen=True)</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `vertical_lines` | ... | `list[Line]` | `...` |
| `horizontal_lines` | ... | `list[Line]` | `...` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `@property horizontal_line_count` | ... | `self` | *None* |
| `@property vertical_line_count` | ... | `self` | *None* |

</details>

<details>
<summary><b>Class:</b> <code>_GridScore</code></summary><br>

<b>Decorators:</b> <code>@dataclass(frozen=True)</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `header` | ... | `float` | `...` |
| `grid_height` | ... | `float` | `...` |
| `grid_width` | ... | `float` | `...` |
| `horizontal_lines` | ... | `float` | `...` |
| `vertical_lines` | ... | `float` | `...` |
| `vertical_slant` | ... | `float` | `...` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `@property region_score` | ... | `self` | *None* |
| `@property line_score` | ... | `self` | *None* |
| `@property total` | ... | `self` | *None* |
| `__str__` | ... | `self` | *None* |

</details>

<details>
<summary><b>Class:</b> <code>_GridSearchResult</code></summary><br>

<b>Decorators:</b> <code>@dataclass(frozen=True)</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `angle` | ... | `float` | `...` |
| `threshold` | ... | `int` | `...` |
| `tolerance` | ... | `float \| None` | `...` |
| `candidate` | ... | `_GridCandidate` | `...` |
| `score` | ... | `_GridScore` | `...` |

</details>

<details>
<summary><b>Class:</b> <code>GridDetector</code></summary><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `img` | ... | `np.ndarray` | `...` |
| `img_grey` | ... | `np.ndarray` | `...` |
| `img_debug` | ... | `np.ndarray` | `...` |
| `img_processed` | ... | `np.ndarray` | `...` |
| `mask` | ... | `np.ndarray` | `...` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `__init__` | ... | `self, img: np.ndarray, args: default_configs.GridDetectorArgs = default_configs.GridDetectorArgs()` | `ImageProcessorUtils.greyscale()`, `default_configs.GridDetectorArgs()`, `ImageProcessorUtils`, `Line` |
| `_score_candidate` | ... | `self, candidate: _GridCandidate` | `_GridScore()`, `error()`, `np.abs()`, `np.array()`, `np.mean()`, `np.median()` |
| `_get_regions` | ... | `self` | `Box()`, `MaskUtils.average_axis()`, `MaskUtils.find_longest_streak()`, `MaskUtils.first_index()`, `MaskUtils.last_index()`, `Box`, `MaskUtils` |
| `_get_horizontal_lines` | ... | `self, grid_box: Box, tolerance` | `Line()`, `MaskUtils.average_axis()`, `MaskUtils.group_mask_features()`, `Point()`, `np.array()`, `np.empty()`, `np.maximum()`, `np.mean()`, `Box`, `Line`, `MaskUtils`, `Point` |
| `_get_vertical_lines` | ... | `self, grid_box: Box, horizontal_lines, tolerance` | `GridDetectionError()`, `Line()`, `MaskUtils.average_axis()`, `MaskUtils.group_mask_features()`, `Point()`, `fit_x_over_y()`, `np.array()`, `self._get_vertical_line_consensus()`, `Box`, `GridDetectionError`, `Line`, `MaskUtils`, `Point` |
| `_get_vertical_line_consensus` | ... | `self, y1: int, y2: int` | `Line()`, `Point()`, `fit_x_over_y()`, `np.array()`, `np.median()`, `self._line_x_at_y()`, `Line`, `Point` |
| `_line_x_at_y` | ... | `line: Line, y: float` | `Line` |
| `_reshape_grid` | ... | `horizontal_lines: list[Line], vertical_lines: list[Line]` | `Box()`, `Line()`, `line_intersection()`, `Box`, `Line` |
| `_get_cell_grid` | ... | `self, horizontal_lines: list[Line], vertical_lines: list[Line]` | `Box()`, `cv2.polylines()`, `line_intersection()`, `Box`, `Line`, `Point` |
| `_draw_debug` | ... | `self, header_box, grid_box, horizontal_lines, vertical_lines` | `cv2.imwrite()`, `cv2.line()`, `cv2.polylines()` |
| `_evaluate_angle` | ... | `self, angle: float` | `ImageProcessorUtils.rotate()`, `_GridCandidate()`, `_GridSearchResult()`, `self._get_regions()`, `self._score_candidate()`, `GridDetectionError`, `ImageProcessorUtils` |
| `_find_angle_range` | ... | `self, min_angle: float, max_angle: float` | `GridDetectionError()`, `np.argmin()`, `np.linspace()`, `self._evaluate_angle()`, `self._find_angle_range()`, `GridDetectionError` |
| `_search_lines` | ... | `self, angle: float, max_threshold_limit: int` | `ImageProcessorUtils.rotate()`, `_GridCandidate()`, `_GridSearchResult()`, `np.arange()`, `self._get_horizontal_lines()`, `self._get_regions()`, `self._get_vertical_lines()`, `self._score_candidate()`, `GridDetectionError`, `ImageProcessorUtils` |
| `detect_grid` | ... | `self, start_angle: float \| None = None` | `GridDetectionError()`, `ImageProcessorUtils.greyscale()`, `ImageProcessorUtils.rotate()`, `self._draw_debug()`, `self._evaluate_angle()`, `self._find_angle_range()`, `self._get_cell_grid()`, `self._reshape_grid()`, `self._search_lines()`, `GridDetectionError`, `ImageProcessorUtils` |

</details>

## File: `todnt\ocr_resource_manager.py`

### Contents

<details>
<summary><b>Imports & Dependencies</b></summary><br>

`PIL`, `PIL.Image`, `gc`, `numpy`, `os`, `re`, `torch`, `torch.utils.data.Dataset`, `torch.utils.data.random_split`, `transformers`, `typing`, `utils`, `warnings.filterwarnings`

</details>

<details>
<summary><b>Standalone Functions</b></summary><br>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `get_optimal_device` | ... | `None` | `torch.cuda.is_available()`, `torch.device()` |

</details>

<details>
<summary><b>Class:</b> <code>OCRImageDataset(Dataset)</code></summary><br>

_Dataset for loading images where the ground truth text is embedded inside the PNG metadata._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `image_files` | ... | `list[str]` | `...` |
| `root_dir` | ... | `str` | `...` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `__init__` | ... | `self, root_dir: str, processor, max_length: int = 64` | `os.listdir()` |
| `__len__` | ... | `self` | *None* |
| `__getitem__` | ... | `self, idx: int` | `PIL.Image.open()`, `PIL.Image.open(img_path).convert()`, `self.processor()`, `self.processor(image, return_tensors='pt').pixel_values.squeeze()`, `self.processor.tokenizer()`, `torch.tensor()`, `PIL` |

</details>

<details>
<summary><b>Class:</b> <code>OCRResourceManager</code></summary><br>

_Singleton resource manager for managing, executing, and fine-tuning OCR models._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `_instance` | ... | `...` | `None` |
| `_easy_ocr_reader` | ... | `...` | `None` |
| `_easy_ocr_detector` | ... | `...` | `None` |
| `_tr_ocr_processor` | ... | `...` | `None` |
| `_tr_ocr_model` | ... | `...` | `None` |
| `_device` | ... | `...` | `None` |
| `_tr_ocr_model_dir` | ... | `...` | `'microsoft/trocr-base-handwritten'` |


<b>Methods:</b>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `__new__` | ... | `cls` | `get_optimal_device()`, `super(OCRResourceManager, cls).__new__()`, `OCRResourceManager` |
| `@property device` | ... | `self` | *None* |
| `@property is_gpu_available` | ... | `self` | *None* |
| `@property easy_ocr_reader` | ... | `self` | `easyocr.Reader()` |
| `@property easy_ocr_detector` | ... | `self` | `easyocr.Reader()` |
| `@property tr_ocr_processor` | ... | `self` | `TrOCRProcessor.from_pretrained()`, `TrOCRProcessor` |
| `@property tr_ocr_model` | ... | `self` | `VisionEncoderDecoderModel.from_pretrained()`, `model.to()`, `VisionEncoderDecoderModel` |
| `load_tr_ocr` | ... | `self, model_folder_path: str` | `FileNotFoundError()`, `os.path.exists()`, `FileNotFoundError` |
| `save_model` | ... | `self, output_directory: str` | `ValueError()`, `os.makedirs()`, `raw_model.save_pretrained()`, `self.tr_ocr_processor.save_pretrained()` |
| `train_tr_ocr` | ... | `self, training_data_path: str, output_directory: str` | `OCRImageDataset()`, `Seq2SeqTrainer()`, `Seq2SeqTrainingArguments()`, `ValueError()`, `gc.collect()`, `model.gradient_checkpointing_enable()`, `random_split()`, `self.load_tr_ocr()`, `self.save_model()`, `torch.Generator()`, `torch.Generator().manual_seed()`, `torch.cuda.empty_cache()`, `torch.cuda.memory_allocated()`, `torch.cuda.memory_reserved()`, `trainer.train()`, `OCRImageDataset`, `Seq2SeqTrainer`, `Seq2SeqTrainingArguments` |
| `_read_typed` | ... | `self, image: numpy.ndarray, valid_output_set: list[str] = None` | `re.search()`, `self.easy_ocr_reader.readtext()`, `utils.rank_matches()` |
| `_read_handwritten` | ... | `self, image: PIL.Image.Image` | `self.tr_ocr_model.generate()`, `self.tr_ocr_processor()`, `self.tr_ocr_processor(image, return_tensors='pt').pixel_values.to()`, `self.tr_ocr_processor.batch_decode()`, `torch.exp()`, `torch.exp(log_score).item()`, `PIL` |
| `find_text_position` | ... | `self, image: numpy.ndarray, **kwargs` | `self.easy_ocr_detector.detect()` |
| `read` | ... | `self, image: numpy.ndarray \| PIL.Image.Image, mode: typing.Literal['PRINTED', 'WRITTEN'], valid_output_set: list[str] = None` | `PIL.Image.fromarray()`, `ValueError()`, `numpy.array()`, `self._read_handwritten()`, `self._read_typed()`, `PIL` |

</details>

## File: `todnt\pipelines.py`

### Module Description
> This module contains functions that set up and runs various pipeline tasks, such as converting PNGs to CSVs, labelling grids, and training OCR models.<br>This module does NOT contain the algorithms used in any process, but is rather the handler between the file IO and the underlying systems.<br><br>TL;DR, this module is the Input Output handler between the user and the math.

### Contents

<details>
<summary><b>Imports & Dependencies</b></summary><br>

`PIL.Image`, `PIL.UnidentifiedImageError`, `dataclasses.dataclass`, `datetime.datetime`, `default_configs.SessionConfigArgs`, `image_converter.ImageConverter`, `io`, `ocr_resource_manager.OCRResourceManager`, `os`, `pymupdf`, `tkinter`, `tkinter.ttk`, `training_data.TrainingDataGrid`, `training_data_gatherer.GridTrainingDataGathererApp`, `typing.Generator`, `typing.Union`, `uuid`

</details>

<details>
<summary><b>TODOs & Tasks</b></summary><br>

| Line | Description |
| :--- | :--- |
| 171 | TODO: Figure out why everything is being saved to p9 |

</details>

<details>
<summary><b>Module Variables & Constants</b></summary><br>

| Variable | Type | Default Value |
| :--- | :--- | :--- |
| `PipelineEvent` | `...` | `Union[StartFileEvent, PageDoneEvent, GridFoundEvent, GridNotFoundEvent, EndFileEvent, StreamCompleteEvent]` |

</details>

<details>
<summary><b>Standalone Functions</b></summary><br>

| Function | Description | Arguments | Calls / Instantiates |
| :--- | :--- | :--- | :--- |
| `run_conversion_session` | This function acts as the primary entry point for document conversion.<br>It automatically detects grids from standard images or PDFs, handles batch or single-file inputs, and writes the extracted table data to CSV files. | `input_path: str, output_path: str, session_config: SessionConfigArgs` | `_png_to_csv()`, `png_input_generator()`, `Generator`, `GridFoundEvent`, `GridNotFoundEvent`, `PageDoneEvent`, `SessionConfigArgs`, `UnidentifiedImageError` |
| `print_conversion_session` | Run a conversion session and render its output for a CLI. | `input_path: str, output_path: str, session_config: SessionConfigArgs` | `run_conversion_session()`, `SessionConfigArgs` |
| `_png_to_csv` | Determines the output destination path and converts the document to CSV. | `input_path: str, output_path: str, session_config: SessionConfigArgs` | `Image.open()`, `ImageConverter()`, `converter.export_to_csv_generator()`, `os.path.basename()`, `os.path.dirname()`, `Generator`, `Image`, `ImageConverter`, `SessionConfigArgs` |
| `run_labelling_session` | This function processes an input image, detects its grid structure, and initializes the labelling application | `input_path: str, model_path: str \| None, session_config: SessionConfigArgs` | `GridTrainingDataGathererApp()`, `ImageConverter()`, `OCRResourceManager()`, `OCRResourceManager().load_tr_ocr()`, `SessionConfigArgs()`, `converter.gather_training_data()`, `converter.save_debug_grid_image()`, `local_style.theme_use()`, `root_window.wait_window()`, `tk.Toplevel()`, `ttk.Style()`, `GridTrainingDataGathererApp`, `ImageConverter`, `OCRResourceManager`, `SessionConfigArgs`, `TrainingDataGrid` |
| `run_training_session` | Trains a new OCR model using accumulated training data at the location specified in the config args, and saves it to a specified path. | `new_model_path: str, session_config: SessionConfigArgs` | `OCRResourceManager()`, `OCRResourceManager().train_tr_ocr()`, `OCRResourceManager`, `SessionConfigArgs` |
| `debug_grid_detector` | For debugging the grid detector. | `input_path: str, session_config: SessionConfigArgs` | `ImageConverter()`, `converter.save_debug_grid_image()`, `ImageConverter`, `SessionConfigArgs` |
| `png_input_generator` | ... | `input_path: str \| list[str], session_config: SessionConfigArgs, target_page: int = None` | `EndFileEvent()`, `GridFoundEvent()`, `Image.fromarray()`, `Image.open()`, `ImageConverter()`, `PageDoneEvent()`, `StartFileEvent()`, `_get_base_directory()`, `_get_input_files()`, `_has_existing_grid_metadata()`, `converter.save_with_metadata()`, `datetime.now()`, `datetime.now().strftime()`, `fitz.open()`, `img_thumb.thumbnail()`, `io.BytesIO()`, `os.makedirs()`, `os.path.basename()`, `os.path.relpath()`, `os.path.splitext()`, `page.get_pixmap()`, `pdf_document.load_page()`, `pix.tobytes()`, `uuid.uuid5()`, `EndFileEvent`, `Generator`, `GridFoundEvent`, `Image`, `ImageConverter`, `PageDoneEvent`, `PipelineEvent`, `SessionConfigArgs`, `StartFileEvent` |
| `_get_input_files` | Yields valid image and PDF file paths recursively from input sources. | `input_paths, max_depth: int \| None = None` | `os.path.isdir()`, `os.path.isfile()`, `os.path.relpath()`, `os.path.splitext()`, `os.walk()` |
| `_get_base_directory` | Determines the common root directory path from various input types. | `input_path: str \| list[str]` | `os.path.commonpath()`, `os.path.dirname()`, `os.path.isfile()` |
| `_has_existing_grid_metadata` | Checks whether an image file already contains embedded grid metadata tags. | `image: Image.Image` | `required_keys.issubset()`, `Image` |

</details>

<details>
<summary><b>Class:</b> <code>StartFileEvent</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `filename` | ... | `str` | `...` |
| `total_pages` | ... | `int` | `...` |

</details>

<details>
<summary><b>Class:</b> <code>PageDoneEvent</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `filename` | ... | `str` | `...` |
| `current_index` | ... | `int` | `...` |

</details>

<details>
<summary><b>Class:</b> <code>GridFoundEvent</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `filename` | ... | `str` | `...` |
| `saved_path` | ... | `str` | `...` |
| `thumbnail` | ... | `Image.Image` | `...` |
| `display_name` | ... | `str` | `...` |

</details>

<details>
<summary><b>Class:</b> <code>GridNotFoundEvent</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_..._

</details>

<details>
<summary><b>Class:</b> <code>EndFileEvent</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_..._


<b>Class Attributes / Fields:</b>

| Attribute | Description | Type | Default Value |
| :--- | :--- | :--- | :--- |
| `filename` | ... | `str` | `...` |

</details>

<details>
<summary><b>Class:</b> <code>StreamCompleteEvent</code></summary><br>

<b>Decorators:</b> <code>@dataclass</code><br>

_..._

</details>
