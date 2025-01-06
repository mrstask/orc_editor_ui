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
        self.original_schema = None

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

                # Get the table first to preserve all schema information
                table = orc_file.read()

                # Store the original schema and metadata
                self.original_schema = table.schema
                self.original_metadata = table.schema.metadata

                print("Original ORC schema:", self.original_schema)
                print("Original metadata:", self.original_metadata)

                # Convert to pandas
                self.df = table.to_pandas()
                self.update_table_view()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def compare_schemas(self, original_schema, saved_schema):
        """Compare two schemas and return differences"""

        def schema_to_dict(schema):
            result = {}
            for field in schema:
                if isinstance(field.type, pyarrow.ListType):
                    list_type = field.type
                    if isinstance(list_type.value_type, pyarrow.StructType):
                        struct_fields = {}
                        for struct_field in list_type.value_type:
                            struct_fields[struct_field.name] = str(struct_field.type)
                        result[field.name] = {
                            'type': 'list<struct>',
                            'struct_fields': struct_fields
                        }
                    else:
                        result[field.name] = f'list<{str(list_type.value_type)}>'
                else:
                    result[field.name] = str(field.type)
            return result

        original_dict = schema_to_dict(original_schema)
        saved_dict = schema_to_dict(saved_schema)

        differences = []
        for field in original_dict:
            if field not in saved_dict:
                differences.append(f"Missing field in saved schema: {field}")
            elif original_dict[field] != saved_dict[field]:
                differences.append(
                    f"Type mismatch for {field}:\n"
                    f"  Original: {original_dict[field]}\n"
                    f"  Saved: {saved_dict[field]}"
                )

        for field in saved_dict:
            if field not in original_dict:
                differences.append(f"Extra field in saved schema: {field}")

        return differences

    def save_file(self):
        if self.df is None:
            messagebox.showwarning("Warning", "No data to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".orc",
            filetypes=[("ORC files", "*.orc"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            if hasattr(self, 'original_schema'):
                print("Using original schema for saving:", self.original_schema)

                # Create table with original schema
                table = pyarrow.Table.from_pandas(
                    self.df,
                    schema=self.original_schema
                )

                # Set metadata if it exists
                if hasattr(self, 'original_metadata'):
                    table = table.replace_schema_metadata(self.original_metadata)
            else:
                print("Warning: No original schema available, inferring schema from data")
                table = pyarrow.Table.from_pandas(self.df)

            # Save the file
            with pyarrow.orc.ORCWriter(filename) as writer:
                writer.write(table)

            # Validate saved file
            orc_file = orc.ORCFile(filename)
            saved_table = orc_file.read()
            saved_schema = saved_table.schema

            # Compare schemas
            if hasattr(self, 'original_schema'):
                differences = self.compare_schemas(self.original_schema, saved_schema)
                if differences:
                    mismatch_msg = "Schema differences detected:\n" + "\n".join(differences)
                    messagebox.showwarning("Schema Mismatch Warning", mismatch_msg)

                    # Print detailed schema information for debugging
                    print("\nDetailed Schema Information:")
                    print("Original Schema:")
                    print(self.original_schema.to_string(show_field_metadata=True))
                    print("\nSaved Schema:")
                    print(saved_schema.to_string(show_field_metadata=True))
                else:
                    messagebox.showinfo("Success", "File saved successfully with schema preserved")
            else:
                messagebox.showinfo("Success", "File saved successfully")

        except Exception as e:
            import traceback
            print("Error saving file:", traceback.format_exc())
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            detail_msg = "Details:\n" + traceback.format_exc()
            messagebox.showerror("Detailed Error", detail_msg)
