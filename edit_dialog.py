import ast
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import pandas as pd

from list_edit_dialog import ListEditDialog
from utils import get_spark_type


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
        self.geometry("700x600")  # Increased width to accommodate spark type information

        # Create main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas with scrollbar for vertical scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

        # Create frame for edit widgets
        self.edit_frame = ttk.Frame(canvas)
        self.edit_frame.columnconfigure(2, weight=1)  # Make entry column expandable

        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create edit widgets - vertical layout
        self.edit_widgets = {}
        for idx, col in enumerate(visible_columns):
            # Label (Column name)
            ttk.Label(self.edit_frame, text=col, anchor="e").grid(
                row=idx, column=0, padx=(0, 10), pady=5, sticky="e"
            )

            # Type information label
            sample_value = self.df.iloc[0][col]  # Get a sample value to help determine array types
            spark_type = get_spark_type(self.df[col].dtype, sample_value)
            type_label = ttk.Label(self.edit_frame, text=f"({spark_type})", foreground="gray")
            type_label.grid(row=idx, column=1, padx=(0, 10), pady=5, sticky="w")

            # Entry widget with edit button for lists
            entry_frame = ttk.Frame(self.edit_frame)
            entry_frame.grid(row=idx, column=2, pady=5, sticky="ew", padx=(0, 10))
            entry_frame.columnconfigure(0, weight=1)

            entry = ttk.Entry(entry_frame)
            entry.grid(row=0, column=0, sticky="ew")

            # Get and format value
            value = df.iloc[row_idx][col]
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray):
                    list_value = value.tolist() if value.size > 0 else []
                    entry_value = f"[{','.join(map(str, list_value))}]"
                else:
                    list_value = value
                    entry_value = f"[{','.join(map(str, value))}]" if value else '[]'

                # Add edit button for list types
                edit_btn = ttk.Button(entry_frame, text="...", width=3)
                edit_btn.grid(row=0, column=1, padx=(5, 0))

                # Create closure to capture the current entry and list_value
                def create_edit_callback(entry_widget, current_value, col_name):
                    def edit_list():
                        # Determine element type from the first element or default to int
                        element_type = "int"
                        if current_value:
                            first_elem = current_value[0] if isinstance(current_value, list) else \
                                current_value.tolist()[0]
                            if isinstance(first_elem, dict):
                                element_type = "struct"
                            elif isinstance(first_elem, str) and (
                                    first_elem.startswith('{') or first_elem.startswith('[')):
                                element_type = "struct"
                            elif isinstance(first_elem, float):
                                element_type = "float"
                            elif isinstance(first_elem, str):
                                element_type = "str"

                        dialog = ListEditDialog(self, current_value, col_name, element_type)
                        self.wait_window(dialog)
                        if dialog.result is not None:
                            entry_widget.delete(0, tk.END)
                            entry_widget.insert(0, f"[{','.join(map(str, dialog.result))}]")

                    return edit_list

                edit_btn.config(command=create_edit_callback(entry, list_value, col))
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
            sample_value = self.df.iloc[0][col]  # Get sample value to help determine type

            try:
                if value.startswith('[') and value.endswith(']'):
                    try:
                        try:
                            value = ast.literal_eval(value)
                        except Exception as e:
                            print(e)
                            items = value[1:-1].split(',')
                            items = [item.strip().strip('"\'') for item in items if item.strip()]

                            if isinstance(sample_value, (np.ndarray, list)):
                                if len(sample_value) > 0:
                                    first_elem = sample_value[0] if isinstance(sample_value, list) else sample_value.item(0)
                                    if isinstance(first_elem, str):
                                        value = items  # Keep as strings
                                    elif isinstance(first_elem, int):
                                        value = [int(float(item)) for item in items]
                                    elif isinstance(first_elem, float):
                                        value = [float(item) for item in items]
                                    else:
                                        value = items  # Default to strings
                                else:
                                    value = items  # Empty list case
                            else:
                                try:
                                    value = [int(float(item)) for item in items]
                                except ValueError:
                                    try:
                                        value = [float(item) for item in items]
                                    except ValueError:
                                        value = items  # Keep as strings
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
