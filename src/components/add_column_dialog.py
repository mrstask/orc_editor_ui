import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np


class AddColumnDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add New Column")
        self.result = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Configure dialog size and position
        self.geometry("400x300")

        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Column name
        ttk.Label(main_frame, text="Column Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.column_name = ttk.Entry(main_frame, width=30)
        self.column_name.grid(row=0, column=1, sticky="ew", pady=5)
        self.column_name.focus_set()  # Set focus to column name field

        # Data type
        ttk.Label(main_frame, text="Data Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.data_type = ttk.Combobox(main_frame, values=[
            "String", "Integer", "Float", "Boolean", "List<String>",
            "List<Integer>", "List<Float>", "List<Boolean>"
        ])
        self.data_type.grid(row=1, column=1, sticky="ew", pady=5)
        self.data_type.current(0)  # Default to String

        # Default value
        ttk.Label(main_frame, text="Default Value:").grid(row=2, column=0, sticky="w", pady=5)
        self.default_value = ttk.Entry(main_frame, width=30)
        self.default_value.grid(row=2, column=1, sticky="ew", pady=5)
        self.default_value.insert(0, "")  # Empty string as default

        # Help text
        help_text = "For lists, use comma-separated values like: 1,2,3 or a,b,c"
        ttk.Label(main_frame, text=help_text, font=("", 8), foreground="gray").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Add Column", command=self.add_column).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

        # Add bindings
        self.bind("<Return>", lambda e: self.add_column())
        self.bind("<Escape>", lambda e: self.cancel())

        # Center the dialog
        self.center_dialog()

    def center_dialog(self):
        """Center the dialog on the parent window."""
        self.geometry("+%d+%d" % (
            self.master.winfo_rootx() + 50,
            self.master.winfo_rooty() + 50
        ))

    # Remove the get_pyarrow_type static method from AddColumnDialog class
    # and keep only these methods:

    def add_column(self):
        """Validate input and add the column."""
        col_name = self.column_name.get().strip()
        data_type = self.data_type.get()
        default_val = self.default_value.get().strip()

        # Validate column name
        if not col_name:
            messagebox.showerror("Error", "Column name cannot be empty")
            return

        # Process default value based on data type
        try:
            if data_type == "String":
                value = default_val
            elif data_type == "Integer":
                value = int(default_val) if default_val else 0
            elif data_type == "Float":
                value = float(default_val) if default_val else 0.0
            elif data_type == "Boolean":
                value = default_val.lower() in ('true', '1', 't', 'y', 'yes') if default_val else False
            elif data_type.startswith("List<"):
                # Handle list types
                if not default_val:
                    value = []
                else:
                    items = [item.strip() for item in default_val.split(',')]
                    if data_type == "List<String>":
                        value = items
                    elif data_type == "List<Integer>":
                        value = [int(item) for item in items]
                    elif data_type == "List<Float>":
                        value = [float(item) for item in items]
                    elif data_type == "List<Boolean>":
                        value = [item.lower() in ('true', '1', 't', 'y', 'yes') for item in items]
                    else:
                        value = items

                # For numpy arrays
                value = np.array(value)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid default value for {data_type}: {str(e)}")
            return

        # Store result
        self.result = {
            'column_name': col_name,
            'data_type': data_type,
            'default_value': value
        }

        self.destroy()

    def cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.destroy()
