from enum import IntEnum, Enum


class Colour(IntEnum):
	FILL = 0x1e1e2e
	SURFACE = 0xebebf7

	TEXT_DARK = 0x11111b
	TEXT_LIGHT = 0xcdd6f4
	MUTED = 0x6c7086
	DISABLED = 0x45475a

	ACCENT_1 = 0x89b4fa
	ACCENT_2 = 0xf9e2af
	SUCCESS = 0xa6e3a1
	LABEL = 0x6c7086

	CELL_ALT = 0x1f1f1f
	CELL_HIGHLIGHT = 0xeeeeee
	CELL_DISABLED = 0x313244
	CELL_DISABLED_TEXT = 0x7f849c
	CELL_SELECTED = 0x89b4fa

	RECT_HIGH = 0x00fff4
	RECT_LOW = 0x111111
	LOW_CONFIDENCE = 0xff9999
	HIGH_CONFIDENCE = 0x99ff99

	@property
	def hex_str(self) -> str:
		return f"#{self.value:06x}"


class Font(Enum):
	FAMILY = "Segoe UI"
	MONO_FAMILY = "Cascadia Code"

	HUGE = 20
	LARGE = 16
	MEDIUM = 14
	SMALL = 12
	TINY = 10

	@property
	def regular(self):
		return Font.FAMILY.value, self.value

	@property
	def bold(self):
		return Font.FAMILY.value, self.value, "bold"

	@property
	def italic(self):
		return Font.FAMILY.value, self.value, "italic"

	@property
	def mono(self):
		return Font.MONO_FAMILY.value, self.value
