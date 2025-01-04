import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import pandas as pd


class EditDialog(tk.Toplevel):
    def __init__(self, parent, df, row_idx, visible_columns):
        super().__init__(parent)
        self.title("Edit Row")
        self.df = df
        self.row_idx = row_idx
        self.result = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Configure dialog size and position
        self.geometry("500x600")  # Set initial size

        # Create main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas with scrollbar for vertical scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

        # Create frame for edit widgets
        self.edit_frame = ttk.Frame(canvas)
        self.edit_frame.columnconfigure(1, weight=1)  # Make entry column expandable

        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create edit widgets - vertical layout
        self.edit_widgets = {}
        for idx, col in enumerate(visible_columns):
            # Label (Column name)
            ttk.Label(self.edit_frame, text=col, anchor="e").grid(
                row=idx, column=0, padx=(0, 10), pady=5, sticky="e"
            )

            # Entry widget
            entry = ttk.Entry(self.edit_frame)
            entry.grid(row=idx, column=1, pady=5, sticky="ew", padx=(0, 10))

            # Get and format value
            value = df.iloc[row_idx][col]
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray):
                    entry_value = f"[{','.join(map(str, value))}]" if value.size > 0 else '[]'
                else:
                    entry_value = f"[{','.join(map(str, value))}]" if value else '[]'
            else:
                entry_value = str(value) if pd.notna(value) else ""
            entry.insert(0, entry_value)
            self.edit_widgets[col] = entry

        # Put the edit frame in the canvas
        canvas.create_window((0, 0), window=self.edit_frame, anchor="nw")

        # Layout scrollable area
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Update scroll region when widgets are configured
        self.edit_frame.bind("<Configure>",
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Buttons at the bottom
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))

        # Make sure edit frame uses full width
        self.edit_frame.bind("<Configure>", self._on_frame_configure)
        canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.edit_frame.master.configure(scrollregion=self.edit_frame.master.bbox("all"))

    def _on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        self.edit_frame.master.itemconfig(
            self.edit_frame.master.find_withtag("all")[0],
            width=event.width
        )

    def save(self):
        self.result = {}
        for col, widget in self.edit_widgets.items():
            value = widget.get()
            original_dtype = self.df[col].dtype

            try:
                if value.startswith('[') and value.endswith(']'):
                    try:
                        items = value[1:-1].split(',')
                        items = [int(item.strip()) for item in items if item.strip()]
                        value = items
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid list format for column '{col}'")
                        return
                elif pd.api.types.is_integer_dtype(original_dtype):
                    value = 0 if not value.strip() else int(float(value))

                self.result[col] = value
            except (ValueError, TypeError):
                messagebox.showerror("Error",
                                     f"Invalid value for column '{col}'. Expected type: {original_dtype}")
                return

        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()
