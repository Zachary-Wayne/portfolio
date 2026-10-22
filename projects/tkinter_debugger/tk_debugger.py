"""
Excerpt from TODNT's utils.py: a live element inspector for Tkinter apps.
Colour and Font are TODNT's design-token enums (app_style.py).
"""
import tkinter as tk
from tkinter import ttk

from app_style import Colour, Font


class TkDebugger:
	"""
	Displays some useful debug information about Tkinter app windows, uses Colour and Font enums.

	Example Usage:
	   if __name__ == "__main__":
		root = tk.Tk()
		app = MainApp(root)
		debugger = TkDebugger(root)
		root.mainloop()
	"""

	def __init__(self, root: tk.Tk):
		self.root = root
		self.active = True
		self.last_widget = None

		self.overlay = tk.Toplevel(self.root)
		self.overlay.withdraw()
		self.overlay.overrideredirect(True)
		self.overlay.attributes("-topmost", True)

		self.highlighter = tk.Frame(
			self.overlay,
			bg="#000001",
			highlightbackground="yellow",
			highlightthickness=3,
			bd=0
		)
		self.highlighter.pack(fill="both", expand=True)

		try:
			self.overlay.attributes("-transparentcolor", "#000001")
		except tk.TclError:
			try:
				self.overlay.attributes("-alpha", 0.4)
			except tk.TclError:
				pass

		self.hud = tk.Toplevel(self.root)
		self.hud.withdraw()
		self.hud.overrideredirect(True)
		self.hud.attributes("-topmost", True)
		self.hud.configure(bg="#1e1e2e", bd=1, relief="solid")

		self.info_label = tk.Label(
			self.hud,
			justify="left",
			anchor="w",
			bg="#1e1e2e",
			fg="#cdd6f4",
			font=("Courier", 10),
			padx=8,
			pady=8
		)
		self.info_label.pack()

		self.root.bind_all("<Motion>", self._inspect_element)
		self.root.bind_all("<Control-Shift-D>", self._toggle_debugger)
		self.root.bind_all("<Button-3>", self._copy_to_clipboard)

	@staticmethod
	def _get_color_map():
		return {c.hex_str.lower(): f"Colour.{c.name}" for c in Colour}

	@staticmethod
	def _get_font_map():
		font_map = {}
		style_names = [
			name for name, attr in vars(Font).items()
			if isinstance(attr, property)
		]

		sizes = [f for f in Font if isinstance(f.value, int)]

		for f in sizes:
			for style in style_names:
				try:
					font_tuple = getattr(f, style)
					family = font_tuple[0]
					size = font_tuple[1]
					family_str = f"{{{family}}}" if " " in family else family
					modifier = font_tuple[2] if len(font_tuple) > 2 else ""
					if modifier:
						key = f"{family_str} {size} {modifier}"
					else:
						key = f"{family_str} {size}"
					font_map[key] = f"Font.{f.name}.{style}"
				except (AttributeError, IndexError):
					continue

		return font_map

	def _toggle_debugger(self, event=None):
		self.active = not self.active
		if not self.active:
			self.overlay.withdraw()
			self.hud.withdraw()
			self.last_widget = None

	def _copy_to_clipboard(self, event=None):
		if not self.active or not self.last_widget:
			return
		info_text = self.info_label.cget("text")
		if info_text:
			self.root.clipboard_clear()
			self.root.clipboard_append(info_text)

	def _is_debugger_window(self, widget):
		if not widget:
			return False
		try:
			w_path = widget.winfo_pathname(widget.winfo_id())
			overlay_path = self.overlay.winfo_pathname(self.overlay.winfo_id())
			hud_path = self.hud.winfo_pathname(self.hud.winfo_id())
			return w_path.startswith(overlay_path) or w_path.startswith(hud_path)
		except tk.TclError:
			return False

	def _find_deepest_widget(self, parent, x, y):
		smallest_child = None
		smallest_area = float('inf')

		for child in parent.winfo_children():
			if not child.winfo_viewable() or self._is_debugger_window(child):
				continue

			cx = child.winfo_rootx()
			cy = child.winfo_rooty()
			cw = child.winfo_width()
			ch = child.winfo_height()

			if cx <= x <= cx + cw and cy <= y <= cy + ch:
				area = cw * ch
				if area < smallest_area:
					smallest_area = area
					smallest_child = child

		if smallest_child:
			deeper_child = self._find_deepest_widget(smallest_child, x, y)  # type: ignore
			return deeper_child if deeper_child else smallest_child

		return None

	# noinspection PyUnresolvedReferences
	def _inspect_element(self, event):
		if not self.active:
			return

		x, y = self.root.winfo_pointerxy()
		widget = self._find_deepest_widget(self.root, x, y)

		if not widget:
			try:
				target = self.root.winfo_containing(x, y)
				if target and not self._is_debugger_window(target):
					widget = target
				else:
					widget = self.root
			except tk.TclError:
				widget = self.root

		if widget == self.last_widget:
			self._position_hud(x, y)
			return

		self.last_widget = widget

		wx = widget.winfo_rootx()
		wy = widget.winfo_rooty()
		ww = widget.winfo_width()
		wh = widget.winfo_height()

		self.overlay.geometry(f"{ww}x{wh}+{wx}+{wy}")
		self.overlay.deiconify()

		self._update_hud_text(widget, ww, wh)  # type: ignore
		self._position_hud(x, y)

	def _position_hud(self, x, y):
		screen_w = self.root.winfo_screenwidth()
		screen_h = self.root.winfo_screenheight()

		hud_w = self.hud.winfo_reqwidth()
		hud_h = self.hud.winfo_reqheight()

		pos_x = x + 20 if x + 20 + hud_w < screen_w else x - hud_w - 20
		pos_y = y + 20 if y + 20 + hud_h < screen_h else y - hud_h - 20

		self.hud.geometry(f"+{pos_x}+{pos_y}")
		self.hud.deiconify()

	def _update_hud_text(self, widget, w, h):
		w_class = widget.winfo_class()
		try:
			full_path = widget.winfo_pathname(widget.winfo_id())
		except tk.TclError:
			full_path = widget.winfo_name()

		details = [
			f"CLASS: {w_class}",
			f"PATH:  {full_path}",
			f"SIZE:  {w}x{h}",
			"-" * 30,
		]

		opt_keys = [
			"font",
			"background",
			"foreground",
			"selectbackground",
			"selectforeground",
			"borderwidth",
			"relief",
			"cursor"
		]

		is_ttk = full_path.startswith(".") and w_class.startswith("T") and w_class != "Text"
		ttk_style_obj = ttk.Style() if is_ttk else None

		assigned_style = ""
		if is_ttk:
			try:
				assigned_style = widget.cget("style") or w_class
				details.insert(1, f"STYLE: {assigned_style}")
			except tk.TclError:
				assigned_style = w_class

		found_opts = False
		color_map = self._get_color_map()
		font_map = self._get_font_map()

		for opt in opt_keys:
			val = None
			try:
				if is_ttk:
					# noinspection PyUnresolvedReferences
					val = ttk_style_obj.lookup(assigned_style, opt)

				if not val:
					val = widget.cget(opt)
			except tk.TclError:
				pass

			if val is not None and val != "":
				found_opts = True
				display_val = str(val)

				if opt == "font":
					clean_val = " ".join(display_val.split())
					if clean_val in font_map:
						display_val = font_map[clean_val]
				elif opt in ["background", "foreground", "selectbackground", "selectforeground"]:
					clean_val = display_val.lower()
					if clean_val in color_map:
						display_val = color_map[clean_val]

				details.append(f"{opt.ljust(18)} {display_val}")

		if not found_opts:
			details.append("NA")

		self.info_label.config(text="\n".join(details))
