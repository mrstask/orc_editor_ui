import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
import pyarrow
import pyarrow.orc as orc


class ScrolledFrame(ttk.Frame):
    """A scrollable frame widget"""

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure canvas
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        # Track changes to the canvas and frame size and sync them
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Put the frame in the canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Layout
        self.canvas.grid(row=0, column=0, sticky="ew")
        self.scrollbar.grid(row=1, column=0, sticky="ew")

        # Expand canvas to fill frame
        self.grid_columnconfigure(0, weight=1)

    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)


class ORCEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ORC File Editor")
        self.current_file = None
        self.df = None

        # Make the window responsive
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create main container
        self.main_frame = ttk.Frame(root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # File operations buttons
        self.create_file_buttons()

        # Table view
        self.create_table_view()

        # Scrollable edit controls
        self.create_edit_controls()

    def create_file_buttons(self):
        file_frame = ttk.Frame(self.main_frame)
        file_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(file_frame, text="Open ORC", command=self.open_file).grid(row=0, column=0, padx=5)
        ttk.Button(file_frame, text="Save ORC", command=self.save_file).grid(row=0, column=1, padx=5)

    def create_table_view(self):
        # Create frame for treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid scrollbars and treeview
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure tree selection
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    def create_edit_controls(self):
        # Create a frame for edit controls with scrolling
        edit_frame = ttk.LabelFrame(self.main_frame, text="Edit Row", padding="5")
        edit_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        # Create scrollable frame for edit controls
        self.edit_scroll_frame = ScrolledFrame(edit_frame)
        self.edit_scroll_frame.grid(row=0, column=0, sticky="ew")
        edit_frame.grid_columnconfigure(0, weight=1)

        self.edit_widgets = {}
        self.edit_row = ttk.Frame(self.edit_scroll_frame.scrollable_frame)
        self.edit_row.grid(row=0, column=0)

        # Buttons frame
        button_frame = ttk.Frame(edit_frame)
        button_frame.grid(row=1, column=0, pady=5)

        ttk.Button(button_frame, text="Update Row", command=self.update_row).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Delete Row", command=self.delete_row).grid(row=0, column=1, padx=5)

    def open_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("ORC files", "*.orc"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.current_file = filename
                # Read ORC file using pyarrow
                orc_file = orc.ORCFile(filename)
                self.df = orc_file.read().to_pandas()

                # Replace NaN with 0 in integer columns in a safer way
                for col in self.df.columns:
                    # Check if column is numeric and contains any NaN
                    if pd.api.types.is_numeric_dtype(self.df[col]):
                        if self.df[col].isna().any():
                            # Convert to nullable integer if it's an integer type
                            if pd.api.types.is_integer_dtype(self.df[col].dtype):
                                self.df[col] = self.df[col].fillna(0).astype('Int64')

                self.update_table_view()
            except Exception as e:
                # Log the full error for debugging
                import traceback
                print("Error opening file:", traceback.format_exc())
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
                # Show detailed error message
                detail_msg = "Details:\n" + traceback.format_exc()
                messagebox.showerror("Detailed Error", detail_msg)

    def save_file(self):
        if self.df is None:
            messagebox.showwarning("Warning", "No data to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".orc",
            filetypes=[("ORC files", "*.orc"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Create a copy of the DataFrame for conversion
                df_to_save = self.df.copy()

                # Handle special column types
                for column in df_to_save.columns:
                    # Check if column contains arrays or lists
                    if df_to_save[column].dtype == 'object':
                        # Convert arrays/lists to string representation
                        df_to_save[column] = df_to_save[column].apply(
                            lambda x: ','.join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(
                                x) if pd.notna(x) else None
                        )

                # Convert DataFrame to PyArrow Table
                table = pyarrow.Table.from_pandas(df_to_save)

                # Write to ORC file
                with pyarrow.orc.ORCWriter(filename) as writer:
                    writer.write(table)
                messagebox.showinfo("Success", "File saved successfully")
            except Exception as e:
                # Log the full error for debugging
                import traceback
                print("Error saving file:", traceback.format_exc())
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                # Show detailed error message to user
                detail_msg = "Details:\n" + traceback.format_exc()
                messagebox.showerror("Detailed Error", detail_msg)

    def is_empty_list_column(self, column):
        """Check if a column contains only empty lists/arrays."""
        for value in self.df[column]:
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray) and value.size > 0:
                    return False
                if isinstance(value, list) and len(value) > 0:
                    return False
            elif not pd.isna(value):  # If it's not an empty list/array and not NaN
                return False
        return True

    def update_table_view(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.df is None or self.df.empty:
            return

        # Filter out columns with only empty lists
        visible_columns = [col for col in self.df.columns if not self.is_empty_list_column(col)]

        # Configure columns
        self.tree["columns"] = visible_columns
        self.tree["show"] = "headings"

        for column in visible_columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=100)

        # Add data with proper handling of NaN values for integer columns
        for idx, row in self.df.iterrows():
            values = []
            for col in visible_columns:
                value = row[col]
                # Handle different types of values
                if isinstance(value, (np.ndarray, list)):
                    # Handle array/list values
                    if isinstance(value, np.ndarray):
                        value = f"[{','.join(map(str, value))}]" if value.size > 0 else '[]'
                    else:  # list
                        value = f"[{','.join(map(str, value))}]" if value else '[]'
                elif pd.api.types.is_integer_dtype(self.df[col].dtype):
                    # Handle integer columns
                    try:
                        value = 0 if pd.isna(value) else int(value)
                    except (ValueError, TypeError):
                        value = 0
                values.append(value)
            self.tree.insert("", "end", values=values)

        # Update edit controls
        self.update_edit_controls()

    def update_edit_controls(self):
        # Clear existing widgets
        for widget in self.edit_widgets.values():
            widget.destroy()
        self.edit_widgets.clear()

        if self.df is None or self.df.empty:
            return

        # Only show edit controls for visible columns
        visible_columns = [col for col in self.df.columns if not self.is_empty_list_column(col)]

        # Create entry widgets for each visible column
        for idx, col in enumerate(visible_columns):
            ttk.Label(self.edit_row, text=col).grid(row=0, column=idx, padx=5)
            entry = ttk.Entry(self.edit_row, width=15)
            entry.grid(row=1, column=idx, padx=5)
            self.edit_widgets[col] = entry

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        # Get selected item values
        item = self.tree.item(selection[0])
        values = item['values']

        # Get visible columns
        visible_columns = [col for col in self.df.columns if not self.is_empty_list_column(col)]

        # Update only the widgets for visible columns
        for col, value in zip(visible_columns, values):
            if col in self.edit_widgets:  # Check if widget exists for this column
                self.edit_widgets[col].delete(0, tk.END)
                self.edit_widgets[col].insert(0, str(value) if value is not None else "")

    def update_row(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to update")
            return

        # Get values from entry widgets and handle data types
        new_values = {}
        idx = self.tree.index(selection[0])

        for col, widget in self.edit_widgets.items():
            value = widget.get()
            original_dtype = self.df[col].dtype

            try:
                # Handle different data types
                if pd.api.types.is_integer_dtype(original_dtype):
                    # Handle integer types
                    value = int(float(value)) if value.strip() else pd.NA
                elif pd.api.types.is_float_dtype(original_dtype):
                    # Handle float types
                    value = float(value) if value.strip() else pd.NA
                elif pd.api.types.is_datetime64_dtype(original_dtype):
                    # Handle datetime
                    value = pd.to_datetime(value) if value.strip() else pd.NaT
                elif pd.api.types.is_bool_dtype(original_dtype):
                    # Handle boolean
                    value = value.lower() in ('true', '1', 't', 'y', 'yes') if value.strip() else pd.NA

                new_values[col] = value
            except (ValueError, TypeError):
                messagebox.showerror("Error", f"Invalid value for column '{col}'. Expected type: {original_dtype}")
                return

        # Update DataFrame with type-safe values
        for col, value in new_values.items():
            self.df.loc[idx, col] = value

        # Update tree view
        self.update_table_view()

    def add_row(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please open or create a new file first")
            return

        # Get values from entry widgets and handle data types
        new_row = {}
        for col, widget in self.edit_widgets.items():
            value = widget.get()
            original_dtype = self.df[col].dtype

            try:
                # Handle different data types
                if pd.api.types.is_integer_dtype(original_dtype):
                    value = int(float(value)) if value.strip() else pd.NA
                elif pd.api.types.is_float_dtype(original_dtype):
                    value = float(value) if value.strip() else pd.NA
                elif pd.api.types.is_datetime64_dtype(original_dtype):
                    value = pd.to_datetime(value) if value.strip() else pd.NaT
                elif pd.api.types.is_bool_dtype(original_dtype):
                    value = value.lower() in ('true', '1', 't', 'y', 'yes') if value.strip() else pd.NA

                new_row[col] = value
            except (ValueError, TypeError):
                messagebox.showerror("Error", f"Invalid value for column '{col}'. Expected type: {original_dtype}")
                return

        # Add to DataFrame using concat instead of deprecated append
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)

        # Update tree view
        self.update_table_view()

    def delete_row(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to delete")
            return

        # Delete from DataFrame
        idx = self.tree.index(selection[0])
        self.df = self.df.drop(idx).reset_index(drop=True)

        # Update tree view
        self.update_table_view()


if __name__ == "__main__":
    root = tk.Tk()
    app = ORCEditor(root)
    root.mainloop()
