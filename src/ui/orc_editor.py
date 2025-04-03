import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
import pyarrow
import pyarrow.orc as orc

from src.components.add_column_dialog import AddColumnDialog
from src.components.edit_dialog import EditDialog


class ORCEditor:
    # Update the __init__ method in ORCEditor to use ToolbarFrame
    # Update the __init__ method in the ORCEditor class to initialize show_empty_columns
    def __init__(self, root):
        self.root = root
        self.root.title("ORC File Editor")
        self.current_file = None
        self.df = None
        self.original_schema = None
        self.original_metadata = None

        # Initialize the show_empty_columns attribute with default value
        self.show_empty_columns = False  # Default: hide empty columns

        # Configure root window to be responsive
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Create main container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Create toolbar with callbacks
        callbacks = {
            "Open ORC": self.open_file,
            "Save ORC": self.save_file,
            "Edit Row": self.edit_selected,
            "Add Column": self.add_column,
            "toggle_empty_columns": self.toggle_empty_columns
        }

        from src.components.toolbar_frame import ToolbarFrame
        toolbar = ToolbarFrame(main_frame, callbacks)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.toolbar = toolbar

        # Create scrollable frame for the table
        self.create_table_view(main_frame)

    # Make sure toggle_empty_columns method is correct
    def toggle_empty_columns(self):
        """Toggle the visibility of empty columns."""
        self.show_empty_columns = not self.show_empty_columns  # Toggle the state
        self.update_table_view()  # Refresh the table view

    # Replace the create_file_buttons method in ORCEditor class
    def create_file_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Add standard buttons
        ttk.Button(button_frame, text="Open ORC", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save ORC", command=self.save_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Row", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Column", command=self.add_column).pack(side=tk.LEFT, padx=5)

        # Add a toggle button for empty columns
        self.show_empty_columns = False  # Default: hide empty columns
        ttk.Button(
            button_frame,
            text="Toggle Empty Columns",
            command=self.toggle_empty_columns
        ).pack(side=tk.LEFT, padx=5)

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
        """Check if a column contains only empty lists/arrays or NaN values."""
        if column not in self.df.columns:
            return True

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

        # Determine visible columns based on the toggle state
        if self.show_empty_columns:
            # Show all columns
            visible_columns = list(self.df.columns)
        else:
            # Hide empty columns
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
                values.append(str(value))
            self.tree.insert("", "end", values=values)

    def edit_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to edit")
            return

        idx = self.tree.index(selection[0])  # Get the index of the selected row
        visible_columns = [col for col in self.df.columns if not self.is_empty_list_column(col)]

        # Open the EditDialog
        dialog = EditDialog(self.root, self.df, idx, visible_columns)
        self.root.wait_window(dialog)  # Wait for the dialog to close

        # If changes were made and confirmed
        if dialog.result:
            try:
                # Update the DataFrame with the new values
                for col, value in dialog.result.items():
                    if isinstance(value, list):
                        print("List value:", value)
                        if isinstance(self.df.loc[idx, col], np.ndarray):
                            print("Existing value in DataFrame (numpy array):", self.df.loc[idx, col])
                            if self.df.loc[idx, col].size and isinstance(self.df.loc[idx, col][0], dict):
                                # Handle list of dictionaries in a numpy array
                                value = np.array(value)
                                # Update the entire array at once
                                self.df.at[idx, col] = value
                            else:
                                # Handle regular numpy arrays
                                self.df.at[idx, col] = value
                        else:
                            # Handle regular Python lists
                            self.df.at[idx, col] = value
                    else:
                        # Handle scalar values (e.g., strings, integers, dictionaries)
                        self.df.at[idx, col] = value

                # Refresh the table view to reflect the changes
                self.update_table_view()

                # Debugging: Print the updated row
                print("Updated row:", self.df.iloc[idx])

            except Exception as e:
                messagebox.showerror("Error", f"Failed to update row: {str(e)}")
                print("Error updating row:", e)
                print(f"Column: {col}, Value: {value}, Type: {type(value)}")
                print(f"Existing value in DataFrame: {self.df.loc[idx, col]}, Type: {type(self.df.loc[idx, col])}")

    def get_pandas_type(self, pa_type):
        """Map PyArrow types to pandas dtypes"""
        import pyarrow as pa

        # Define type mappings
        type_mapping = {
            pa.timestamp('ms'): 'datetime64[ms]',
            pa.int64(): 'int64',
            pa.int32(): 'int32',
            pa.float64(): 'float64',
            pa.float32(): 'float32',
            pa.string(): 'object',
            pa.bool_(): 'bool',
        }

        return type_mapping.get(pa_type, None)

    def open_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("ORC files", "*.orc"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.current_file = filename
                orc_file = orc.ORCFile(filename)
                table = orc_file.read()

                # Store the original schema and metadata
                self.original_schema = table.schema
                self.original_metadata = table.schema.metadata

                # First convert to pandas without type mapping
                self.df = table.to_pandas()

                # Then apply type conversions after the fact
                for field in table.schema:
                    if str(field.type) == 'timestamp[ms]' or str(field.type) == 'int64':
                        if field.name in self.df.columns:
                            # Fill NaN values with -1 before converting to int64
                            self.df[field.name] = self.df[field.name].fillna(-1).astype('int64')

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
            # Debug: Print the DataFrame before saving
            print("DataFrame before saving:")
            print(self.df.head())

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

            # Debug: Print the saved file's schema and data
            print("Saved file schema:")
            orc_file = orc.ORCFile(filename)
            saved_table = orc_file.read()
            saved_schema = saved_table.schema
            print(saved_schema.to_string(show_field_metadata=True))

            print("Saved file data:")
            print(saved_table.to_pandas().head())

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

    def add_column(self):
        """Open dialog to add a new column to the dataset."""
        if self.df is None:
            messagebox.showwarning("Warning", "Please open an ORC file first")
            return

        # Create dialog
        dialog = AddColumnDialog(self.root)
        self.root.wait_window(dialog)

        # Process result if user confirmed
        if dialog.result:
            try:
                column_name = dialog.result['column_name']
                data_type = dialog.result['data_type']
                default_value = dialog.result['default_value']

                # Check if column already exists
                if column_name in self.df.columns:
                    messagebox.showerror("Error", f"Column '{column_name}' already exists")
                    return

                # Add the column to the DataFrame
                self.df[column_name] = default_value

                # Update schema
                if hasattr(self, 'original_schema'):
                    # Import pyarrow and type utils
                    import pyarrow as pa
                    from src.utils.type_utils import get_pyarrow_type

                    # Get PyArrow type for the new column
                    pa_type = get_pyarrow_type(data_type)

                    # Create new field
                    new_field = pa.field(column_name, pa_type)

                    # Create new schema with the additional field
                    fields = list(self.original_schema)
                    fields.append(new_field)

                    # Update original schema
                    self.original_schema = pa.schema(fields)

                    # Update metadata if it exists
                    if hasattr(self, 'original_metadata') and self.original_metadata:
                        self.original_schema = self.original_schema.with_metadata(self.original_metadata)

                # Update table view
                self.update_table_view()

                messagebox.showinfo("Success", f"Added new column: {column_name}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add column: {str(e)}")
