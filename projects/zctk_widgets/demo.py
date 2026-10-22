"""
A small render-queue window that exercises every ZCTk widget.

Run with Python 3.14+ and `pip install customtkinter numpy`.
"""
import sys

import customtkinter as ctk

import zctk

FONT = "Segoe UI"
FORMATS = ["PNG sequence", "MP4 (H.264)", "GIF", "WebP", "TIFF"]


class DemoApp(ctk.CTk):
	def __init__(self):
		super().__init__()
		self.title("ZCTk demo")
		self.geometry("980x600")
		self.resizable(False, False)

		self.delta_timer = zctk.ZCTkDeltaTimer(self, show_fps=True)
		self.notifications = zctk.ZCTkNotificationManager(self, self.delta_timer)

		self.menu = zctk.ZCTkMenuBar(self)
		self.menu.pack(fill="x", padx=10, pady=(6, 0))
		self.menu.add_cascade("View", ["Dark mode", "Light mode", "Toggle FPS"], command=self.on_view)

		body = ctk.CTkFrame(self, fg_color="transparent")
		body.pack(fill="both", expand=True, padx=10, pady=10)
		body.grid_columnconfigure((0, 1), weight=1, uniform="cols")
		body.grid_rowconfigure(0, weight=1)

		self.job = zctk.ZCTkLabeledContainer(body, text="New render", label_font=(FONT, 16, "bold"))
		self.job.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

		self.scene = zctk.ZCTkLabeledInput(self.job, label_text="Scene", orientation="horizontal",
										   entry_placeholder_text="e.g. Garden at dusk", label_font=(FONT, 14, "bold"))
		self.frames = zctk.ZCTkLabeledInput(self.job, label_text="Frames", orientation="horizontal",
											entry_placeholder_text="Whole number", label_font=(FONT, 14, "bold"))
		self.fps = zctk.ZCTkLabeledInput(self.job, label_text="FPS", orientation="horizontal",
										 entry_placeholder_text="e.g. 30", label_font=(FONT, 14, "bold"))
		for row in (self.scene, self.frames, self.fps):
			row.label.configure(width=90, anchor="w")
			row.pack(fill="x", padx=10, pady=4)

		self.formats = zctk.ZCTkScrollableSelectionGroup(
			self.job, items=FORMATS, scroll_label_text="Output format", scroll_label_font=(FONT, 14, "bold"),
			height=170, command=lambda checked: print(f"Formats: {', '.join(checked) or 'none'}")
		)
		self.formats.pack(fill="both", expand=True, padx=10, pady=(8, 4))

		self.submit = zctk.ZCTkConditionalButton(
			self.job, error_message="Could not queue the render:", delta_timer=self.delta_timer,
			notification_manager=self.notifications, text="Queue render", font=(FONT, 14, "bold"),
			command=self.on_submit
		)
		self.submit.pack(fill="x", padx=10, pady=(6, 12), ipady=4)
		self.submit.add_condition(lambda: not self.scene.get().strip(), "No scene entered", self.scene)
		self.submit.add_condition(lambda: not self.frames.get().strip().isdigit(), "Frames must be a whole number", self.frames)
		self.submit.add_condition(lambda: not self.fps.get().strip().isdigit(), "FPS must be a whole number", self.fps)
		self.submit.add_condition(lambda: len(self.formats.get_checked_items()) != 1, "Pick exactly one output format", self.formats)

		log = zctk.ZCTkLabeledContainer(body, text="Console", label_font=(FONT, 16, "bold"))
		log.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
		self.console = ctk.CTkTextbox(log, font=("Cascadia Code", 12))
		self.console.pack(fill="both", expand=True, padx=10, pady=(4, 10))
		sys.stdout = zctk.ZCTkTerminalRedirector(self.console)
		print("print() output lands here.")

	def on_submit(self):
		frames, fps = int(self.frames.get()), int(self.fps.get())
		output = self.formats.get_checked_items()[0]
		print(f"Queued: {self.scene.get()}, {frames:,} frames ({frames / fps:.1f} s at {fps} fps) as {output}")
		self.notifications.show_notification(zctk.ZCTkFloatingTextBox(None, "Render queued", label_font=(FONT, 14, "bold")))

	def on_view(self, choice):
		if choice == "Toggle FPS":
			self.delta_timer.toggle_fps(not self.delta_timer._show_fps)
		else:
			ctk.set_appearance_mode("Dark" if choice == "Dark mode" else "Light")
		self.menu.get_menu("View").set("View")


if __name__ == "__main__":
	ctk.set_appearance_mode("Dark")
	DemoApp().mainloop()
