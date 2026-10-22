import torch
from warnings import filterwarnings

filterwarnings('ignore')
torch.cuda.empty_cache()

import os
import re
import numpy
import PIL
from PIL import Image
import typing
import gc
import transformers
import utils
from torch.utils.data import Dataset, random_split

gc.collect()

"""
My computer hardware:

NPU - Intel(R) AI Boost - Useless for training because it is interface only, pointless for production.
GPU - NVIDIA RTX A400 (4GB) - Not enough memory for fast OCR training, this is the bottleneck.
CPU - Intel(R) Core(TM) Ultra 7 265 (2.40 GHz) - Has a lot of cores! Pretty good for training and production.
CPU - Intel(R) Graphics - No comments.
"""


def get_optimal_device() -> torch.device:
	if hasattr(torch, "cuda") and torch.cuda.is_available():
		_device = torch.device("cuda")
	elif hasattr(torch, "npu") and torch.cuda.is_available():
		_device = torch.device("npu")
	else:
		_device = torch.device("cpu")
	print(f"Using device: {_device}")
	return _device


class OCRImageDataset(Dataset):
	"""
	Dataset for loading images where the ground truth text is embedded inside the PNG metadata.
	"""
	image_files: list[str]
	root_dir: str

	def __init__(self, root_dir: str, processor, max_length: int = 64):
		self.root_dir = root_dir
		self.processor = processor
		self.max_length = max_length
		self.image_files = [f for f in os.listdir(root_dir) if f.lower().endswith('.png')]

	def __len__(self):
		return len(self.image_files)

	def __getitem__(self, idx: int):
		img_path = os.path.join(self.root_dir, self.image_files[idx])
		image = PIL.Image.open(img_path).convert("RGB")
		text = image.info.get("ground_truth", "")
		pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze(0)
		labels = self.processor.tokenizer(text, padding="max_length", truncation=True, max_length=self.max_length).input_ids
		labels = [label if label != self.processor.tokenizer.pad_token_id else -100 for label in labels]
		return {"pixel_values": pixel_values, "labels": torch.tensor(labels)}


class OCRResourceManager:
	"""Singleton resource manager for managing, executing, and fine-tuning OCR models."""
	_instance = None
	_easy_ocr_reader = None
	_easy_ocr_detector = None
	_tr_ocr_processor = None
	_tr_ocr_model = None
	_device = None

	# noinspection Annotator
	_tr_ocr_model_dir = "microsoft/trocr-base-handwritten"

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super(OCRResourceManager, cls).__new__(cls)
			cls._instance._device = get_optimal_device()
		return cls._instance

	@property
	def device(self) -> torch.device:
		return self._device

	@property
	def is_gpu_available(self) -> bool:
		return self.device.type != "cpu"

	@property
	def easy_ocr_reader(self):
		if self._easy_ocr_reader is None:
			print(f"Creating new EasyOCR reader on device: {self.device}")
			import easyocr
			self._easy_ocr_reader = easyocr.Reader(['en'], gpu=True)  # gpu=self.is_gpu_available)
		return self._easy_ocr_reader

	@property
	def easy_ocr_detector(self):
		if self._easy_ocr_detector is None:
			if self._easy_ocr_reader is not None:
				print("Creating new detector from existing reader")
				self._easy_ocr_detector = self._easy_ocr_reader.detector
			else:
				print("Creating new standalone detector")
				import easyocr
				self._easy_ocr_detector = easyocr.Reader(['en'], gpu=self.is_gpu_available, recognizer=False)
		return self._easy_ocr_detector

	@property
	def tr_ocr_processor(self):
		if self._tr_ocr_processor is None:
			print("Creating new processor loader")
			from transformers import TrOCRProcessor
			self._tr_ocr_processor = TrOCRProcessor.from_pretrained(self._tr_ocr_model_dir)
		return self._tr_ocr_processor

	@property
	def tr_ocr_model(self):
		if self._tr_ocr_model is None:
			print(f"Creating new model loader and pushing to {self.device}")
			from transformers import VisionEncoderDecoderModel
			model = VisionEncoderDecoderModel.from_pretrained(self._tr_ocr_model_dir)

			model.config.decoder_start_token_id = self.tr_ocr_processor.tokenizer.cls_token_id
			model.config.pad_token_id = self.tr_ocr_processor.tokenizer.pad_token_id
			model.config.vocab_size = model.config.decoder.vocab_size

			self._tr_ocr_model = model.to(self.device)
		return self._tr_ocr_model

	def load_tr_ocr(self, model_folder_path: str):
		if not os.path.exists(model_folder_path):
			raise FileNotFoundError(f"Specified local path does not exist: '{model_folder_path}'")

		print(f"Switching to model: {model_folder_path}")
		self._tr_ocr_model_dir = model_folder_path
		self._tr_ocr_model = None
		self._tr_ocr_processor = None

	def save_model(self, output_directory: str):
		if self._tr_ocr_model is None:
			raise ValueError("No model is currently initialized to save.")

		os.makedirs(output_directory, exist_ok=True)
		raw_model = getattr(self._tr_ocr_model, "_orig_mod", self._tr_ocr_model)
		raw_model.save_pretrained(output_directory)
		self.tr_ocr_processor.save_pretrained(output_directory)
		print(f"Model and processor successfully saved to {output_directory}")

	def train_tr_ocr(self, training_data_path: str, output_directory: str):
		from transformers import (
			Seq2SeqTrainer,
			Seq2SeqTrainingArguments,
		)

		train_device = self.device
		print(f"FINE TUNING '{self._tr_ocr_model_dir}' utilizing device: {train_device}")

		epochs = 20
		batch_size = 2
		gradient_accumulation_steps = 16
		learning_rate = 1e-5
		val_split = 0.15
		dataset_max_length = 128
		logging_steps = 20
		seed = 83

		dataset = OCRImageDataset(training_data_path, self.tr_ocr_processor, max_length=dataset_max_length)

		if len(dataset) == 0:
			raise ValueError(f"No valid training data found in {training_data_path}")

		val_size = int(len(dataset) * val_split)
		train_size = len(dataset) - val_size

		train_dataset, val_dataset = random_split(dataset, [train_size, val_size], generator=torch.Generator().manual_seed(seed))

		model = self.tr_ocr_model
		model.gradient_checkpointing_enable()
		model.config.use_cache = False

		training_args = Seq2SeqTrainingArguments(
			output_dir=os.path.join(output_directory, "checkpoints"),
			per_device_train_batch_size=batch_size,
			per_device_eval_batch_size=batch_size,
			gradient_accumulation_steps=gradient_accumulation_steps,
			num_train_epochs=epochs,
			learning_rate=learning_rate,
			logging_steps=logging_steps,
			eval_strategy="epoch",
			save_strategy="epoch",
			save_total_limit=1,
			load_best_model_at_end=True,
			metric_for_best_model="eval_loss",
			greater_is_better=False,
			fp16=(train_device.type == "cuda"),
			optim="adafactor" if train_device.type == "cuda" else "adamw_torch",
			predict_with_generate=False,
			dataloader_num_workers=8,
			dataloader_pin_memory=True,
			report_to="none"
		)

		trainer = Seq2SeqTrainer(
			model=model,
			args=training_args,
			train_dataset=train_dataset,
			eval_dataset=(val_dataset if val_size > 0 else None),
			data_collator=transformers.default_data_collator,
		)

		if train_device.type == "cuda":
			gc.collect()
			torch.cuda.empty_cache()
			print(f"GPU Memory Allocated: {torch.cuda.memory_allocated() / 1024 ** 3:.2f} GB")
			print(f"GPU Memory Reserved: {torch.cuda.memory_reserved() / 1024 ** 3:.2f} GB")

		print(f"Starting fine-tuning for {epochs} epochs...")
		trainer.train()

		self.save_model(output_directory)
		self.load_tr_ocr(output_directory)

	def _read_typed(self, image: numpy.ndarray, valid_output_set: list[str] = None) -> list[str]:
		results = self.easy_ocr_reader.readtext(image)
		if not valid_output_set:
			return results

		extracted_chunks = []
		for _, text, _ in results:
			if re.search(r'\s{2,}', text):
				extracted_chunks.extend(text.split())
			else:
				extracted_chunks.append(text)

		validated_outputs = []
		for chunk in extracted_chunks:
			ranked_candidates = utils.rank_matches(chunk, valid_output_set)
			if ranked_candidates:
				validated_outputs.append(ranked_candidates[0])
		return validated_outputs

	def _read_handwritten(self, image: PIL.Image.Image) -> typing.Tuple[str, float]:
		generation_output = self.tr_ocr_model.generate(
			self.tr_ocr_processor(image, return_tensors="pt").pixel_values.to(self.device),
			num_beams=4,
			max_length=20,  # The number of characters the output can be.
			return_dict_in_generate=True,
			output_scores=True
		)

		generated_ids = generation_output.sequences
		generated_text = self.tr_ocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
		log_score = generation_output.sequences_scores[0]
		confidence_score = torch.exp(log_score).item()

		return generated_text, confidence_score

	def find_text_position(self, image: numpy.ndarray, **kwargs):
		_, boxes = self.easy_ocr_detector.detect(image, height_ths=0.2, width_ths=0.2, **kwargs)
		return boxes

	def read(
			self,
			image: numpy.ndarray | PIL.Image.Image,
			mode: typing.Literal["PRINTED", "WRITTEN"],
			valid_output_set: list[str] = None
	):
		if mode == "PRINTED":
			if isinstance(image, PIL.Image.Image):
				image = numpy.array(image)
			return self._read_typed(image, valid_output_set)
		elif mode == "WRITTEN":
			if isinstance(image, numpy.ndarray):
				image = PIL.Image.fromarray(image)
			return self._read_handwritten(image)

		raise ValueError(f"Unsupported mode: {mode}")
