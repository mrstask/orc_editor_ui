import ast
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd

from src.components.table_view import TableView
from src.components.toolbar_frame import ToolbarFrame
from src.data.data_manager import ORCDataManager
from src.exceptions.orc_exceptions import ORCLoadError, ORCSaveError
from src.utils.config import Config
from src.utils.schema_validator import SchemaValidator


class ORCEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ORC File Editor")
        self._setup_window()

        self.data_manager = ORCDataManager()
        self.schema_validator = SchemaValidator()

        self._create_ui()
        self._setup_bindings()

    def _setup_window(self):
        """Configure the main window grid system"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Configure main frame to expand
        self.main_frame = ttk.Frame(self.root, padding=Config.DEFAULT_PADDING)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure main frame grid weights
        self.main_frame.grid_rowconfigure(1, weight=1)  # Row with table should expand
        self.main_frame.grid_columnconfigure(0, weight=1)  # Column should expand

    def _create_ui(self):
        """Create and layout UI components with empty column toggle"""
        # Create toolbar with callbacks including toggle
        toolbar_callbacks = {
            "Open ORC": self.open_file,
            "Save ORC": self.save_file,
            "Edit Row": self.edit_selected}
        self.toolbar = ToolbarFrame(self.main_frame, toolbar_callbacks)
        self.toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Create table view
        self.table_view = TableView(self.main_frame)
        self.table_view.grid(row=1, column=0, sticky="nsew")

    def toggle_empty_columns(self):
        """Toggle visibility of empty columns"""
        if self.data_manager.df is not None:
            self.table_view.toggle_empty_columns(self.data_manager.df)

    def open_file(self):
        try:
            filename = filedialog.askopenfilename(filetypes=Config.FILE_TYPES)
            if filename:
                self.data_manager.load_file(filename)
                self.table_view.update_data(self.data_manager.df)
        except ORCLoadError as e:
            messagebox.showerror("Error", str(e))

    def save_file(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".orc",
                filetypes=Config.FILE_TYPES
            )
            if filename:
                validation_result = self.data_manager.save_file(filename)
                if validation_result.has_differences:
                    self._show_schema_differences(validation_result.differences)
                else:
                    messagebox.showinfo("Success", "File saved successfully")
        except ORCSaveError as e:
            messagebox.showerror("Error", str(e))

    def _setup_bindings(self):
        """Setup keyboard and mouse bindings for the editor"""
        # Bind double-click on table row to edit
        self.table_view.tree.bind('<Double-1>', lambda e: self.edit_selected())

        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-e>', lambda e: self.edit_selected())

    def _show_schema_differences(self, differences):
        """Display schema differences in a dialog

        Args:
            differences: List of string descriptions of schema differences
        """
        detail_message = "\n".join(differences)
        dialog = tk.Toplevel(self.root)
        dialog.title("Schema Differences")
        dialog.geometry("600x400")

        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()

        # Create scrollable text area
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Add warning message
        warning_label = ttk.Label(
            frame,
            text="Warning: The following schema differences were detected:",
            foreground="red"
        )
        warning_label.pack(fill=tk.X, pady=(0, 10))

        # Create text widget with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(text_frame, wrap=tk.WORD, width=60, height=15)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Insert differences
        text.insert("1.0", detail_message)
        text.configure(state="disabled")  # Make read-only

        # Add close button
        ttk.Button(frame, text="Close", command=dialog.destroy).pack(pady=(10, 0))

        # Center the dialog on the screen
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2,
            self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        ))

    def edit_selected(self):
        """Handle editing of the selected row in the table"""
        selection = self.table_view.get_selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to edit")
            return

        row_idx = selection[0]  # Get the first selected row index

        # Get visible columns (excluding empty columns)
        visible_columns = [
            col for col in self.data_manager.df.columns
            if not self.data_manager.is_empty_column(col)
        ]

        # Create edit dialog
        dialog = EditDialog(
            self.root,
            self.data_manager.df,
            row_idx,
            visible_columns
        )

        self.root.wait_window(dialog)  # Wait for dialog to close

        # If changes were made and confirmed
        if dialog.result:
            try:
                # Update the data in the data manager
                self.data_manager.update_row(row_idx, dialog.result)
                # Refresh the table view
                self.table_view.update_data(self.data_manager.df)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update row: {str(e)}")

    def _update_row_display(self, row_idx):
        """Update the display of a specific row in the table

        Args:
            row_idx: Index of the row to update
        """
        row_data = self.data_manager.get_row_display_values(row_idx)
        self.table_view.update_row(row_idx, row_data)


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
