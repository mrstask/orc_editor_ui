import tkinter as tk
from tkinter import ttk


class ToolbarFrame(ttk.Frame):
    def __init__(self, parent, callbacks):
        super().__init__(parent)
        self._callbacks = callbacks
        self._create_buttons()

    def _create_buttons(self):
        """Create toolbar buttons including the toggle for empty columns"""
        # Standard buttons
        for btn_text, callback in self._callbacks.items():
            ttk.Button(self, text=btn_text, command=callback).pack(side=tk.LEFT, padx=5)

        # Add separator
        ttk.Separator(self, orient='vertical').pack(side=tk.LEFT, padx=10, fill='y')

        # Create toggle button for empty columns
        self.toggle_btn = ttk.Checkbutton(
            self,
            text="Hide Empty Columns",
            command=self._callbacks.get("toggle_empty_columns", lambda: None),
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        # Set default state to checked
        self.toggle_btn.state(['selected'])
