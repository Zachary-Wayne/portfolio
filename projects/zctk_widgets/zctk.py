"""
ZCTk: extensions for CustomTkinter, written for TODNT's GUI.

Excerpt from TODNT's zachscustomtkinter.py. The same file's live widget inspector is shown separately
as the Tkinter Live Inspector project. Needs Python 3.14+ (annotations refer to classes defined later).
"""
import math
import sys
import time
import tkinter as tk
from dataclasses import dataclass
from typing import Any, Literal, Callable, Optional, List, Dict

import customtkinter as ctk
import numpy as np

from app_style import Font


@dataclass(slots=True)
class _ButtonCondition:
	check: Callable[[], bool]
	fail_message: str
	container: Optional[ctk.CTkBaseClass] = None

	def __init__(
			self,
			evaluation_func: Callable[[], bool],
			fail_message: str,
			container_frame: Optional[ctk.CTkFrame] = None
	):
		self.check = evaluation_func
		self.fail_message = fail_message
		self.container = container_frame


@dataclass(slots=True)
class _NotificationData:
	widget: ZCTkFloatingTextBox
	width: int
	height: int
	x: int
	y: int
	target_x: int
	target_y: int
	is_dismissing: bool = False


class ZCTkLabeledContainer(ctk.CTkFrame):
	def __init__(
			self,
			master: Any,
			text: str = "",
			label_font: tuple[str, int, str] | None = None,
			label_text_colour: str | tuple[str, str] | None = None,
			label_fg_colour: str | tuple[str, str] | None = None,
			container_fg_colour: str | tuple[str, str] | None = None,
			container_border_width: int | str | None = None,
			container_border_colour: str | tuple[str, str] | None = None,
			**kwargs
	):
		super().__init__(master, **kwargs)

		label_opts = {
			"font": label_font,
			"text_color": label_text_colour,
			"fg_color": label_fg_colour
		}

		self.grid_rowconfigure(1, weight=1)
		self.grid_columnconfigure(0, weight=1)

		self.label = ctk.CTkLabel(self, text=text, **{k: v for k, v in label_opts.items() if v is not None})
		self.label.pack(side="top", anchor="w", padx=15, pady=(8, 2))

	@property
	def content(self) -> ctk.CTkFrame:
		return self


class ZCTkFloatingTextBox(ctk.CTkCanvas):
	def __init__(
			self,
			master: Any,
			text: str = "",
			label_font: tuple[str, int, str] | None = None,
			label_text_colour: str | tuple[str, str] | None = None,
			label_fg_colour: str | tuple[str, str] | None = 'transparent',
			container_fg_colour: str | tuple[str, str] | None = 'transparent',
			container_border_width: int | str | None = None,
			container_border_colour: str | tuple[str, str] | None = None,
			justify: Literal["left", "center", "right"] = "left",
			anchor: Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"] = "nw",
			**kwargs
	):

		kwargs.setdefault("highlightthickness", 0)
		super().__init__(master, **kwargs)

		self._text = text
		self._font = label_font or ("Arial", 12, "normal")
		self._justify = justify
		self._anchor = anchor

		current_mode = 1 if ctk.get_appearance_mode() == "Dark" else 0

		self._text_colour = "black" if current_mode == 0 else "white"
		if label_text_colour is not None:
			self._text_colour = label_text_colour[current_mode] if isinstance(label_text_colour, tuple) else label_text_colour

		self._box_colour = "#dbdbdb" if current_mode == 0 else "#2b2b2b"
		if container_fg_colour is not None and container_fg_colour != 'transparent':
			self._box_colour = container_fg_colour[current_mode] if isinstance(container_fg_colour, tuple) else container_fg_colour

		self._border_colour = None
		if container_border_colour is not None:
			self._border_colour = container_border_colour[current_mode] if isinstance(container_border_colour, tuple) else container_border_colour

		self._border_width = 0
		if container_border_width is not None:
			self._border_width = int(container_border_width)

		self._radius = 15
		self._padding = 10

		self.draw_component()

	def draw_component(self):
		self.delete("all")

		test_txt = self.create_text(
			0,
			0,
			text=self._text,
			font=self._font,
			anchor=self._anchor,
			justify=self._justify
		)
		x1, y1, x2, y2 = self.bbox(test_txt)
		self.delete(test_txt)

		text_width = x2 - x1
		text_height = y2 - y1

		box_width = text_width + (self._padding * 2) + (self._border_width * 2)
		box_height = text_height + (self._padding * 2) + (self._border_width * 2)

		self.configure(width=box_width, height=box_height)

		r = self._radius
		x1_pos, y1_pos = self._border_width, self._border_width
		x2_pos, y2_pos = box_width - self._border_width, box_height - self._border_width

		points = (
			x1_pos + r, y1_pos, x1_pos + r, y1_pos,
			x2_pos - r, y1_pos, x2_pos - r, y1_pos,
			x2_pos, y1_pos,
			x2_pos, y1_pos + r, x2_pos, y1_pos + r,
			x2_pos, y2_pos - r, x2_pos, y2_pos - r,
			x2_pos, y2_pos,
			x2_pos - r, y2_pos, x2_pos - r, y2_pos,
			x1_pos + r, y2_pos, x1_pos + r, y2_pos,
			x1_pos, y2_pos,
			x1_pos, y2_pos - r, x1_pos, y2_pos - r,
			x1_pos, y1_pos + r, x1_pos, y1_pos + r,
			x1_pos, y1_pos
		)

		poly_opts = {"fill": self._box_colour, "smooth": True}
		if self._border_width > 0 and self._border_colour:
			poly_opts["outline"] = self._border_colour
			poly_opts["width"] = self._border_width

		self.create_polygon(points, **poly_opts)

		x_pos = self._padding + self._border_width
		y_pos = self._padding + self._border_width

		if "e" in self._anchor:
			x_pos = box_width - (self._padding + self._border_width)
		elif "w" not in self._anchor:
			x_pos = box_width // 2

		if "s" in self._anchor:
			y_pos = box_height - (self._padding + self._border_width)
		elif "n" not in self._anchor:
			y_pos = box_height // 2

		self.create_text(
			x_pos,
			y_pos,
			text=self._text,
			font=self._font,
			fill=self._text_colour,
			anchor=self._anchor,
			justify=self._justify
		)


class ZCTkNotificationManager:
	def __init__(
			self,
			master,
			frame_timer: ZCTkDeltaTimer,
			max_notifications=5,
	):
		self.master = master
		self.frame_timer = frame_timer
		self.max_notifications = max_notifications
		self.notifications: List[_NotificationData] = []
		self._animate_loop_running = False

	def show_notification(self, frame: ZCTkFloatingTextBox):
		frame.master = self.master

		self.master.update_idletasks()

		width = frame.winfo_reqwidth()
		height = frame.winfo_reqheight()

		start_x = -width
		target_x = 20

		notif_data = _NotificationData(widget=frame, width=width, height=height, x=start_x, y=10, target_x=target_x, target_y=10)

		self.notifications.append(notif_data)

		active_notifications = [n for n in self.notifications if not n.is_dismissing]
		if len(active_notifications) > self.max_notifications:
			excess_count = len(active_notifications) - self.max_notifications
			for i in range(excess_count):
				old_notif = active_notifications[i]
				old_notif.is_dismissing = True

		self._reposition_all()

		if self.notifications:
			notif_data.y = notif_data.target_y

		# frame.draw_component()

		if not self._animate_loop_running:
			self._animate_loop_running = True
			self._update_animations()

		self.master.after(3500, lambda: self._dismiss_specific(notif_data))

	def _reposition_all(self):
		current_y = 10
		spacing = 10

		for notif in self.notifications:
			if not notif.is_dismissing:
				notif.target_y = current_y
				current_y += notif.height + spacing

	def _update_animations(self):
		if not self.notifications:
			self._animate_loop_running = False
			return

		dt = self.frame_timer.dt
		to_remove = []

		for notif in self.notifications:
			if not notif.widget.winfo_exists():
				to_remove.append(notif)
				continue

			if notif.is_dismissing:
				end_x = -2 * notif.width
				diff_x = notif.x - end_x
				if diff_x > 0.5:
					notif.x -= diff_x * (1 - math.exp(-1.1 * dt))
					if notif.x + notif.width <= 0:
						notif.widget.destroy()
						to_remove.append(notif)
					else:
						notif.widget.place(x=notif.x, y=notif.y)
				else:
					notif.widget.destroy()
					to_remove.append(notif)
			else:
				diff_x = notif.target_x - notif.x
				if abs(diff_x) > 0.5:
					notif.x += diff_x * (1 - math.exp(-2 * dt))
				else:
					notif.x = notif.target_x

				diff_y = notif.target_y - notif.y
				if abs(diff_y) > 0.5:
					notif.y += diff_y * (1 - math.exp(-2 * dt))
				else:
					notif.y = notif.target_y
				notif.widget.place(x=notif.x, y=notif.y)

		if to_remove:
			for notif in to_remove:
				if notif in self.notifications:
					self.notifications.remove(notif)
			self._reposition_all()

		self.master.after(5, self._update_animations)

	def _dismiss_specific(self, notif):
		if notif in self.notifications and not notif.is_dismissing:
			notif.is_dismissing = True
			self._reposition_all()


class ZCTkLabeledInput(ctk.CTkFrame):
	def __init__(
			self,
			master: Any,
			label_text: str = "Field:",
			orientation: Literal["vertical", "horizontal"] = "vertical",
			label_font: tuple[str, int, str] | None = None,
			label_text_colour: str | tuple[str, str] | None = None,
			entry_placeholder_text: str = "",
			entry_width: int | None = None,
			entry_height: int | None = None,
			entry_font: tuple[str, int, str] | None = None,
			entry_state: str = "normal",
			entry_show: str | None = None,
			entry_textvariable: Any | None = None,
			**kwargs
	):
		super().__init__(master, **kwargs)

		label_opts = {
			"font": label_font,
			"text_color": label_text_colour
		}
		entry_opts = {
			"placeholder_text": entry_placeholder_text,
			"state": entry_state,
			"width": entry_width,
			"height": entry_height,
			"font": entry_font,
			"show": entry_show,
			"textvariable": entry_textvariable
		}

		is_horiz = orientation == "horizontal"
		self.grid_columnconfigure(1 if is_horiz else 0, weight=1)
		if not is_horiz:
			self.grid_rowconfigure(1, weight=1)

		self.label = ctk.CTkLabel(
			self, text=label_text, **{k: v for k, v in label_opts.items() if v is not None}
		)
		self.label.grid(row=0, column=0, sticky="w", padx=5, pady=2)

		self.entry = ctk.CTkEntry(
			self, **{k: v for k, v in entry_opts.items() if v is not None}
		)
		self.entry.grid(
			row=0 if is_horiz else 1,
			column=1 if is_horiz else 0,
			sticky="ew", padx=5, pady=5
		)

	def get(self) -> str: return self.entry.get()

	def insert(self, index, string: str): self.entry.insert(index, string)

	def delete(self, first_index, last_index=None): self.entry.delete(first_index, last_index)


class ZCTkScrollableSelectionGroup(ctk.CTkFrame):
	def __init__(
			self,
			master: Any,
			items: list | None = None,
			command: Any = None,
			scroll_label_text: str = "",
			scroll_label_font: tuple[str, int, str] | None = None,
			scroll_fg_colour: str | tuple[str, str] | None = None,
			checkbox_padx: int = 10,
			checkbox_pady: int = 5,
			checkbox_font: tuple[str, int, str] | None = None,
			checkbox_fg_colour: str | tuple[str, str] | None = None,
			checkbox_hover_colour: str | tuple[str, str] | None = None,
			checkbox_text_colour: str | tuple[str, str] | None = None,
			**kwargs
	):
		super().__init__(master, **kwargs)

		scroll_opts = {
			"label_text": scroll_label_text,
			"fg_color": scroll_fg_colour,
			"label_font": scroll_label_font
		}
		self._cb_grid_kwargs = {"padx": checkbox_padx, "pady": checkbox_pady}

		checkbox_config = {
			"font": checkbox_font,
			"fg_color": checkbox_fg_colour,
			"hover_color": checkbox_hover_colour,
			"text_color": checkbox_text_colour
		}
		self._checkbox_config = {k: v for k, v in checkbox_config.items() if v is not None}

		self.scroll_container = ctk.CTkScrollableFrame(
			self, **{k: v for k, v in scroll_opts.items() if v is not None}
		)
		self.scroll_container.pack(fill="both", expand=True)

		self.command = command
		self.variables = {}
		self.checkboxes = {}

		if items:
			self.add_items(items)

	def add_items(self, items: list):
		for item in items:
			if item in self.checkboxes:
				continue

			var = tk.StringVar(value="off")
			cb = ctk.CTkCheckBox(
				self.scroll_container,
				text=item,
				variable=var,
				onvalue="on",
				offvalue="off",
				command=self._on_check_changed,
				**self._checkbox_config
			)
			cb.pack(**self._cb_grid_kwargs)

			self.variables[item] = var
			self.checkboxes[item] = cb

	def _on_check_changed(self):
		if self.command:
			self.command(self.get_checked_items())

	def get_checked_items(self) -> list:
		return [item for item, var in self.variables.items() if var.get() == "on"]


class ZCTkMenuBar(ctk.CTkFrame):
	def __init__(
			self,
			master: Any,
			menu_width: int = 65,
			menu_height: int = 26,
			menu_font: tuple[str, int, str] | None = None,
			menu_button_colour: str | tuple[str, str] | None = None,
			menu_button_hover_colour: str | tuple[str, str] | None = None,
			menu_text_colour: str | tuple[str, str] | None = None,
			**kwargs
	):
		kwargs.setdefault("fg_color", "transparent")
		kwargs.setdefault("height", 32)
		kwargs.setdefault("corner_radius", 0)
		super().__init__(master, **kwargs)

		btn_opts = {
			"width": menu_width,
			"height": menu_height,
			"font": menu_font,
			"button_color": menu_button_colour,
			"button_hover_color": menu_button_hover_colour,
			"text_color": menu_text_colour
		}
		self._shared_button_config = {k: v for k, v in btn_opts.items() if v is not None}
		self.menus = {}

	def add_cascade(self, label: str, options: list, command=None):
		cfg = {**self._shared_button_config, "values": options}
		if command:
			cfg["command"] = command

		dropdown = ctk.CTkOptionMenu(self, **cfg)
		dropdown.set(label)
		dropdown.pack(side="left", padx=2, pady=3)

		self.menus[label.lower()] = dropdown
		return dropdown

	def get_menu(self, label: str):
		return self.menus.get(label.lower())


class ZCTkConditionalButton(ctk.CTkButton):
	def __init__(
			self,
			master: Any,
			error_message: str,
			delta_timer: ZCTkDeltaTimer,
			notification_manager: ZCTkNotificationManager,
			conditions: Optional[List[_ButtonCondition]] = None,
			**kwargs
	):
		self.original_command = kwargs.get("command", None)
		kwargs["command"] = self._on_click
		super().__init__(master, **kwargs)

		self.delta_timer = delta_timer
		self.error_message = error_message
		self.notification_manager = notification_manager
		self.conditions: List[_ButtonCondition] = conditions if conditions is not None else []
		self._active_container_animations: Dict[Any, Any] = {}
		self._active_button_animation: bool = False

	def add_condition(
			self,
			evaluation_func: Callable[[], bool],
			fail_message: str,
			container_frame: Optional[ctk.CTkFrame] = None
	):
		condition = _ButtonCondition(evaluation_func, f"\t- {fail_message}", container_frame)
		self.conditions.append(condition)

	def clear_conditions(self):
		self.conditions.clear()

	def _on_click(self):
		failed_condition_containers = []
		all_error_messages = [self.error_message]

		for condition in self.conditions:
			container = condition.container
			if condition.check():
				if container not in failed_condition_containers:
					failed_condition_containers.append(container)
					all_error_messages.append(condition.fail_message)

		if failed_condition_containers:
			for container in failed_condition_containers:
				bg_color = container.cget("fg_color")
				if bg_color in ["transparent", None]:
					bg_color = self.master.cget("fg_color")

				if isinstance(bg_color, (list, tuple)):
					bg_color = bg_color[1] if ctk.get_appearance_mode() == "Dark" else bg_color[0]

				if container in self._active_container_animations:
					self.after_cancel(self._active_container_animations[container])

				self._border_animation(container, self._hex_to_rgb("#CC0000"), self._hex_to_rgb(bg_color))

			if not self._active_button_animation:
				self._active_button_animation = True
				self._button_animation(super().cget("fg_color"), super().cget("hover_color"))

			self.notification_manager.show_notification(
				ZCTkFloatingTextBox(None, '\n'.join(all_error_messages))
			)
		else:
			if self.original_command:
				self.original_command()

	def _border_animation(
			self,
			container,
			rgb_1,
			rgb_2,
			fade_in_time: float = 0.2,
			hold_time: float = 1.0,
			fade_out_time: float = 0.5,
			elapsed: float = 0,
			max_thickness: int = 4
	):
		elapsed += self.delta_timer.dt
		t1 = fade_in_time
		t2 = t1 + hold_time
		total_time = t2 + fade_out_time

		if elapsed >= total_time:
			try:
				container.configure(border_width=0)
			except (tk.TclError, AttributeError):
				pass
			self._active_container_animations.pop(container, None)
			return

		try:
			c1, c2 = np.array(rgb_1), np.array(rgb_2)
			if elapsed <= t1:
				a = np.interp(elapsed, [0, t1], [0.0, 1.0])
				rgb = (c2 + (c1 - c2) * a).astype(int).tolist()
				border_width = int(np.interp(elapsed, [0, t1], [0, max_thickness]))
			elif elapsed <= t2:
				rgb = rgb_1
				border_width = max_thickness
			else:
				a = np.interp(elapsed, [t2, total_time], [0.0, 1.0])
				rgb = (c1 + (c2 - c1) * a).astype(int).tolist()
				border_width = int(np.interp(elapsed, [t2, total_time], [max_thickness, 0]))

			hex_border = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
			container.configure(border_width=border_width, border_color=hex_border)
		except (tk.TclError, AttributeError, TypeError, IndexError):
			pass

		self._active_container_animations[container] = self.after(
			16, lambda: self._border_animation(
				container, rgb_1, rgb_2, fade_in_time, hold_time, fade_out_time, elapsed, max_thickness
			)
		)

	def _button_animation(
			self,
			original_fg_color,
			original_hover_color,
			elapsed: float = 0,
			duration: float = 0.4
	):
		elapsed += self.delta_timer.dt
		if elapsed >= duration:
			self.configure(fg_color=original_fg_color, hover_color=original_hover_color)
			self._active_button_animation = False
			return

		try:
			mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0

			current_fg_base = original_fg_color[mode_idx] if isinstance(original_fg_color, (list, tuple)) else original_fg_color
			current_hover_base = original_hover_color[mode_idx] if isinstance(original_hover_color, (list, tuple)) else original_hover_color

			a = np.interp(elapsed, [0, duration], [0.0, 1.0])
			shake_frequency = 4.0
			amplitude = 18.0 * (1.0 - a)
			current_offset = int(amplitude * np.sin(a * shake_frequency * 2.0 * np.pi))

			if self.grid_info():
				self.grid_configure(padx=(current_offset, 0) if current_offset >= 0 else (0, -current_offset))
			elif self.pack_info():
				self.pack_configure(padx=(current_offset, 0) if current_offset >= 0 else (0, -current_offset))

			c1_fg, c2_fg = np.array(self._hex_to_rgb("#990000")), np.array(self._hex_to_rgb(current_fg_base))
			c1_hover, c2_hover = np.array(self._hex_to_rgb("#CC0000")), np.array(self._hex_to_rgb(current_hover_base))

			rgb_fg = (c1_fg + (c2_fg - c1_fg) * a).astype(int).tolist()
			rgb_hover = (c1_hover + (c2_hover - c1_hover) * a).astype(int).tolist()

			hex_fg = f"#{rgb_fg[0]:02x}{rgb_fg[1]:02x}{rgb_fg[2]:02x}"
			hex_hover = f"#{rgb_hover[0]:02x}{rgb_hover[1]:02x}{rgb_hover[2]:02x}"

			self.configure(fg_color=(hex_fg, hex_fg), hover_color=(hex_hover, hex_hover))

		except (tk.TclError, AttributeError, TypeError, IndexError) as e:
			print(e)

		self.after(16, lambda: self._button_animation(original_fg_color, original_hover_color, elapsed, duration))

	@staticmethod
	def _hex_to_rgb(hex_str):
		if not hex_str or not isinstance(hex_str, str) or not hex_str.startswith('#'):
			return 30, 30, 30
		hex_str = hex_str.lstrip('#')
		if len(hex_str) == 3:
			hex_str = ''.join([c * 2 for c in hex_str])
		try:
			return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))
		except ValueError:
			return 30, 30, 30


class ZCTkDeltaTimer:
	def __init__(self, master, target_fps=60, show_fps=True):
		self.master = master
		self._delay = max(1, int(1000 / target_fps))

		self._last_time = time.perf_counter()
		self._dt = 0.0
		self._is_running = True

		self._fps_label = None
		self._show_fps = show_fps

		if self._show_fps:
			self._create_fps_widget()

		self.master.bind("<Destroy>", lambda e: self.stop(), add="+")
		self._update_loop()

	def _create_fps_widget(self):
		self._fps_label = ctk.CTkLabel(
			self.master,
			text="FPS: 0",
			font=Font.TINY.mono,
			text_color="lightgreen",
			fg_color='transparent',
			padx=6,
			pady=2
		)
		self._fps_label.lift()
		self._position_fps_widget()

	def _position_fps_widget(self):
		if self._fps_label and self._fps_label.winfo_exists():
			self._fps_label.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

	def _update_loop(self):
		if not self._is_running:
			return

		current_time = time.perf_counter()
		self._dt = current_time - self._last_time
		self._last_time = current_time

		if self._show_fps and self._fps_label and self._fps_label.winfo_exists():
			fps = 1.0 / self._dt if self._dt > 0 else 0.0
			self._fps_label.configure(text=f"FPS: {int(fps)}")
			self._fps_label.lift()

		self.master.after(self._delay, self._update_loop)

	@property
	def dt(self):
		return self._dt

	def toggle_fps(self, show: bool):
		self._show_fps = show
		if self._show_fps:
			if not self._fps_label or not self._fps_label.winfo_exists():
				self._create_fps_widget()
			else:
				self._position_fps_widget()
		elif self._fps_label and self._fps_label.winfo_exists():
			self._fps_label.place_forget()

	def stop(self):
		self._is_running = False


class ZCTkTerminalRedirector:
	"""
	Allows print() calls to be directed to CTk text boxes, has line flush handling.
	"""

	def __init__(self, text_widget):
		self.text_widget = text_widget
		self.original_stdout = sys.stdout
		self.original_stderr = sys.stderr

	def write(self, string):
		self.original_stdout.write(string)

		if not string:
			return

		try:
			if string.startswith('\r'):
				string = string.lstrip('\r')
				if self.text_widget.get("end-2c") != "\n":
					last_line_index = self.text_widget.index("end-2c linestart")
					self.text_widget.delete(last_line_index, "end-1c")
				self.text_widget.insert("end-1c", string)
			else:
				self.text_widget.insert("end-1c", string)
			self.text_widget.see("end")
			self.text_widget.update_idletasks()
		except AttributeError:
			current_text = self.text_widget.cget("text")
			if string.startswith('\r'):
				string = string.lstrip('\r')
				if current_text and not current_text.endswith('\n'):
					lines = current_text.splitlines()
					if lines:
						lines[-1] = string
						new_text = "\n".join(lines)
					else:
						new_text = string
				else:
					new_text = current_text + string
			else:
				new_text = current_text + string
			self.text_widget.configure(text=new_text)
			self.text_widget.update_idletasks()

	def flush(self):
		self.original_stdout.flush()
		self.original_stderr.flush()

