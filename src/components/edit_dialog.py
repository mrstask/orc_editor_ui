import ast
import json
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
        self.visible_columns = visible_columns
        self.result = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Configure dialog size and position
        self.geometry("700x600")

        # Create main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas with scrollbar for vertical scrolling
        self.canvas = tk.Canvas(main_frame)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)

        # Create frame for edit widgets
        self.edit_frame = ttk.Frame(self.canvas)
        self.edit_frame.columnconfigure(2, weight=1)  # Make entry column expandable

        # Configure canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self._create_edit_widgets(visible_columns)
        self._layout_widgets()
        self._setup_bindings()

    def _create_edit_widgets(self, visible_columns):
        """Create the edit widgets for each column."""
        self.edit_widgets = {}
        for idx, col in enumerate(visible_columns):
            # Label (Column name)
            ttk.Label(self.edit_frame, text=col, anchor="e").grid(
                row=idx, column=0, padx=(0, 10), pady=5, sticky="e"
            )

            # Entry widget
            entry = ttk.Entry(self.edit_frame)
            entry.grid(row=idx, column=1, padx=(0, 10), pady=5, sticky="ew")

            # Get and format value
            value = self.df.iloc[self.row_idx][col]

            # Handle arrays and lists
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray):
                    entry_value = f"[{','.join(map(str, value.tolist()))}]" if value.size > 0 else "[]"
                else:  # list
                    entry_value = f"[{','.join(map(str, value))}]" if value else "[]"
            else:
                # Handle scalar values
                entry_value = str(value) if pd.notna(value) else ""

            entry.insert(0, entry_value)
            self.edit_widgets[col] = entry

            # Bind double-click event for complex fields
            if isinstance(value, (np.ndarray, list, dict)):
                entry.bind("<Double-1>", lambda e, col=col: self.open_larger_editor(col))

    def open_larger_editor(self, column):
        """Open a larger editor for complex fields."""
        # Get the current value from the entry widget
        current_value = self.edit_widgets[column].get()

        # Pretty-print the value for easier editing
        try:
            # Try to parse the value as JSON (for dictionaries)
            parsed_value = json.loads(current_value)
            formatted_value = json.dumps(parsed_value, indent=4)
        except json.JSONDecodeError:
            # If not JSON, assume it's a list or other complex type
            try:
                # Try to evaluate the value as a Python object (e.g., list)
                parsed_value = ast.literal_eval(current_value)
                formatted_value = json.dumps(parsed_value, indent=4)
            except (ValueError, SyntaxError):
                # Fallback to the original value if parsing fails
                formatted_value = current_value

        # Create a new window for the larger editor
        editor_window = tk.Toplevel(self)  # Make it a child of the EditDialog
        editor_window.title(f"Edit {column}")
        editor_window.geometry("500x400")

        # Make the new window modal
        editor_window.transient(self)  # Set as child of the EditDialog
        editor_window.grab_set()  # Make it modal

        # Create a Text widget for editing
        editor_text = tk.Text(editor_window, wrap=tk.WORD, width=60, height=20)
        editor_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Insert the formatted value into the Text widget
        editor_text.insert("1.0", formatted_value)

        # Add Save and Cancel buttons
        button_frame = ttk.Frame(editor_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Save",
            command=lambda: self.save_larger_editor(column, editor_text, editor_window)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=editor_window.destroy
        ).pack(side=tk.LEFT, padx=5)

    def save_larger_editor(self, column, editor_text, editor_window):
        """Save the changes from the larger editor."""
        # Get the edited value from the Text widget
        edited_value = editor_text.get("1.0", tk.END).strip()

        # Update the corresponding entry widget in the EditDialog
        self.edit_widgets[column].delete(0, tk.END)
        self.edit_widgets[column].insert(0, edited_value)

        # Close the larger editor window
        editor_window.destroy()

    def _layout_widgets(self):
        """Layout all widgets in the dialog."""
        # Put the edit frame in the canvas
        self.canvas.create_window((0, 0), window=self.edit_frame, anchor="nw")

        # Layout scrollable area
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons at the bottom
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        # Center the dialog
        self.center_dialog()

    def _setup_bindings(self):
        """Setup event bindings."""
        self.edit_frame.bind("<Configure>",
                             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def center_dialog(self):
        """Center the dialog on the parent window."""
        self.geometry("+%d+%d" % (
            self.master.winfo_rootx() + 50,
            self.master.winfo_rooty() + 50
        ))

    def save(self):
        """Save the changes made in the dialog"""
        self.result = {}
        for col, widget in self.edit_widgets.items():
            value = widget.get()
            original_dtype = self.df[col].dtype
            sample_value = self.df.iloc[0][col]  # Get sample value to help determine type

            try:
                if value.strip().startswith('[') and value.strip().endswith(']'):
                    try:
                        # First try ast.literal_eval
                        try:
                            value = ast.literal_eval(value.strip())
                        except Exception:
                            # If that fails, parse manually
                            items = value.strip()[1:-1].split(',')
                            items = [item.strip().strip('"\'') for item in items if item.strip()]

                            if isinstance(sample_value, (np.ndarray, list)):
                                if len(sample_value) > 0:
                                    first_elem = (sample_value[0] if isinstance(sample_value, list)
                                                  else sample_value.item(0))
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
                    except ValueError as e:
                        messagebox.showerror("Error", f"Invalid list format for column '{col}': {str(e)}")
                        return
                elif pd.api.types.is_integer_dtype(original_dtype):
                    value = 0 if not value.strip() else int(float(value))
                elif pd.api.types.is_float_dtype(original_dtype):
                    value = 0.0 if not value.strip() else float(value)
                elif pd.api.types.is_bool_dtype(original_dtype):
                    value = value.strip().lower() in ('true', '1', 't', 'y', 'yes')

                self.result[col] = value
            except (ValueError, TypeError) as e:
                messagebox.showerror(
                    "Error",
                    f"Invalid value for column '{col}'. Expected type: {original_dtype}\nError: {str(e)}"
                )
                return

        self.destroy()
