import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
import pyarrow
import pyarrow.orc as orc

from edit_dialog import EditDialog


class ORCEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ORC File Editor")
        self.current_file = None
        self.df = None

        # Configure root window to be responsive
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Create main container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # File operations buttons
        self.create_file_buttons(main_frame)

        # Create scrollable frame for the table
        self.create_table_view(main_frame)

    def create_file_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(button_frame, text="Open ORC", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save ORC", command=self.save_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Row", command=self.edit_selected).pack(side=tk.LEFT, padx=5)

    def create_table_view(self, parent):
        # Create frame for the table and scrollbars
        table_frame = ttk.Frame(parent)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Create canvas and scrollbars
        canvas = tk.Canvas(table_frame)
        vscrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        hscrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=canvas.xview)

        # Create frame inside canvas for the treeview
        self.tree_frame = ttk.Frame(canvas)

        # Create Treeview
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Configure canvas
        canvas.configure(yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)

        # Add bindings for double-click
        self.tree.bind('<Double-1>', lambda e: self.edit_selected())

        # Layout
        canvas.grid(row=0, column=0, sticky="nsew")
        vscrollbar.grid(row=0, column=1, sticky="ns")
        hscrollbar.grid(row=1, column=0, sticky="ew")

        # Create window inside canvas
        canvas.create_window((0, 0), window=self.tree_frame, anchor="nw")

        # Configure scroll region when frame changes
        self.tree_frame.bind("<Configure>",
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

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

        # Add data
        for idx, row in self.df.iterrows():
            values = []
            for col in visible_columns:
                value = row[col]
                if isinstance(value, (np.ndarray, list)):
                    if isinstance(value, np.ndarray):
                        value = f"[{','.join(map(str, value))}]" if value.size > 0 else '[]'
                    else:  # list
                        value = f"[{','.join(map(str, value))}]" if value else '[]'
                elif pd.api.types.is_integer_dtype(self.df[col].dtype):
                    try:
                        value = 0 if pd.isna(value) else int(value)
                    except (ValueError, TypeError):
                        value = 0
                values.append(value)
            self.tree.insert("", "end", values=values)

    def edit_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to edit")
            return

        idx = self.tree.index(selection[0])
        visible_columns = [col for col in self.df.columns if not self.is_empty_list_column(col)]

        dialog = EditDialog(self.root, self.df, idx, visible_columns)
        self.root.wait_window(dialog)

        if dialog.result:
            # Update DataFrame with new values
            for col, value in dialog.result.items():
                self.df.loc[idx, col] = value
            self.update_table_view()

    def open_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("ORC files", "*.orc"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.current_file = filename
                orc_file = orc.ORCFile(filename)
                self.df = orc_file.read().to_pandas()
                self.update_table_view()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")

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
                df_to_save = self.df.copy()

                # Handle special column types and ensure proper types for each column
                for column in df_to_save.columns:
                    # Get sample non-null value to determine column type
                    sample_value = df_to_save[column].dropna().iloc[0] if not df_to_save[column].isna().all() else None

                    if isinstance(sample_value, (list, np.ndarray)):
                        # Convert arrays/lists to string representation
                        df_to_save[column] = df_to_save[column].apply(
                            lambda x: ','.join(map(str, x)) if isinstance(x, (list, np.ndarray)) and len(x) > 0
                            else '' if isinstance(x, (list, np.ndarray))
                            else str(x) if pd.notna(x) else ''
                        )
                    elif pd.api.types.is_integer_dtype(df_to_save[column].dtype):
                        # Convert integer columns, replace NaN with 0
                        df_to_save[column] = df_to_save[column].fillna(0).astype('int64')
                    elif pd.api.types.is_float_dtype(df_to_save[column].dtype):
                        # Convert float columns, replace NaN with 0.0
                        df_to_save[column] = df_to_save[column].fillna(0.0).astype('float64')
                    else:
                        # Convert object/string columns, replace NaN with empty string
                        df_to_save[column] = df_to_save[column].fillna('').astype(str)

                # Convert to PyArrow table with explicit schema
                schema = []
                for column in df_to_save.columns:
                    if pd.api.types.is_integer_dtype(df_to_save[column].dtype):
                        schema.append(pyarrow.field(column, pyarrow.int64()))
                    elif pd.api.types.is_float_dtype(df_to_save[column].dtype):
                        schema.append(pyarrow.field(column, pyarrow.float64()))
                    else:
                        schema.append(pyarrow.field(column, pyarrow.string()))

                table = pyarrow.Table.from_pandas(df_to_save, schema=pyarrow.schema(schema))

                with pyarrow.orc.ORCWriter(filename) as writer:
                    writer.write(table)
                messagebox.showinfo("Success", "File saved successfully")
            except Exception as e:
                import traceback
                print("Error saving file:", traceback.format_exc())
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                detail_msg = "Details:\n" + traceback.format_exc()
                messagebox.showerror("Detailed Error", detail_msg)