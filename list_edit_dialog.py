import tkinter as tk
from tkinter import ttk, messagebox
import json


class ListEditDialog(tk.Toplevel):
    def __init__(self, parent, list_value, column_name, element_type="int"):
        super().__init__(parent)
        self.title(f"Edit List - {column_name}")
        self.list_value = list_value if list_value else []
        self.element_type = element_type
        self.result = None
        self.is_complex_type = element_type == "struct" or element_type == "str"

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Configure dialog size and position
        self.geometry("600x500")  # Increased width for complex types

        # Create main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create list editing frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)

        # Create list entries with a scrollable frame
        self.canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)

        self.entries_frame = ttk.Frame(self.canvas)
        self.entries_frame.columnconfigure(0, weight=1)

        # Configure canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.entries_frame, anchor="nw")

        # Layout scrollable area
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add entries for existing values
        self.entries = []
        for value in self.list_value:
            if isinstance(value, (dict, str)) and self.is_complex_type:
                value = json.dumps(value if isinstance(value, dict) else json.loads(value), indent=2)
            self.add_entry(value)

        # Create control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(control_frame, text="Add Item", command=self.add_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Remove Last", command=self.remove_last).pack(side=tk.LEFT, padx=5)

        # Create OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))

        # Update scroll region when entries are added/removed
        self.entries_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas_width)

    def update_scroll_region(self, event=None):
        """Update the scroll region when the frame size changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_canvas_width(self, event):
        """Update the canvas frame width when the canvas is resized"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def add_entry(self, value=None):
        """Add a new entry row"""
        idx = len(self.entries)
        frame = ttk.Frame(self.entries_frame)
        frame.grid(row=idx, column=0, sticky="ew", pady=2)
        frame.columnconfigure(1, weight=1)

        # Index label
        ttk.Label(frame, text=f"{idx}:").grid(row=0, column=0, padx=(0, 5))

        # Entry or Text widget based on type
        if self.is_complex_type:
            entry = tk.Text(frame, height=4, width=50)
            entry.grid(row=0, column=1, sticky="ew")
            if value is not None:
                entry.insert("1.0", str(value))
        else:
            entry = ttk.Entry(frame)
            entry.grid(row=0, column=1, sticky="ew")
            if value is not None:
                entry.insert(0, str(value))

        self.entries.append(entry)
        self.update_scroll_region()

    def remove_last(self):
        """Remove the last entry"""
        if self.entries:
            entry = self.entries.pop()
            entry.grid_remove()
            entry.destroy()
            self.update_scroll_region()

    def get_entry_value(self, entry):
        """Get value from either Entry or Text widget"""
        if isinstance(entry, tk.Text):
            return entry.get("1.0", "end-1c")  # Get text without trailing newline
        return entry.get()

    def validate_values(self):
        """Validate and convert all entry values"""
        values = []
        for entry in self.entries:
            value = self.get_entry_value(entry).strip()
            if not value:  # Skip empty entries
                continue
            try:
                if self.is_complex_type:
                    # Try to parse as JSON to validate, but keep as string
                    parsed = json.loads(value)
                    values.append(parsed if isinstance(parsed, dict) else value)
                elif self.element_type == "int":
                    # Remove any surrounding brackets and quotes
                    clean_value = value.strip('[]"\' ')
                    values.append(int(float(clean_value)))
                elif self.element_type == "float":
                    clean_value = value.strip('[]"\' ')
                    values.append(float(clean_value))
                else:
                    # For string types, preserve the value but remove list formatting if present
                    clean_value = value.strip('[]"\' ')
                    values.append(clean_value)
            except ValueError as e:
                messagebox.showerror("Error",
                                     f"Invalid {self.element_type} format: {value}\nError: {str(e)}")
                return None
            except json.JSONDecodeError as e:
                messagebox.showerror("Error",
                                     f"Invalid JSON format: {value}\nError: {str(e)}")
                return None
        return values

    def ok(self):
        self.result = self.validate_values()
        if self.result is not None:
            self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()
