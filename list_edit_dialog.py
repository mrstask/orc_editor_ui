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
        self.geometry("800x600")  # Increased size for better JSON editing

        # Create main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add type indicator label
        type_label = ttk.Label(main_frame, text=f"Type: {element_type}")
        type_label.pack(fill=tk.X, pady=(0, 10))

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

        # Special handling for list of dictionaries
        if self.is_complex_type and self.list_value and isinstance(self.list_value[0], dict):
            # Create a single text widget for the entire JSON array
            self.json_text = tk.Text(self.entries_frame, height=20, width=80)
            self.json_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            json_str = json.dumps(self.list_value, indent=2)
            self.json_text.insert("1.0", json_str)
            self.entries = [self.json_text]  # Keep track of the widget
        else:
            # Add entries for existing values
            self.entries = []
            for value in self.list_value:
                if isinstance(value, (dict, str)) and self.is_complex_type:
                    if isinstance(value, dict):
                        value = json.dumps(value, indent=2)
                    elif self.is_json(value):
                        try:
                            parsed = json.loads(value)
                            value = json.dumps(parsed, indent=2)
                        except json.JSONDecodeError:
                            pass
                self.add_entry(value)

            # Create control buttons (only for non-JSON array cases)
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

    def is_json(self, value):
        """Check if a string is valid JSON"""
        if not isinstance(value, str):
            return False
        try:
            json.loads(value)
            return True
        except (ValueError, TypeError):
            return False

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
            entry = tk.Text(frame, height=4, width=80)
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
        # Special handling for the meta column with list of dictionaries
        if self.is_complex_type and len(self.entries) == 1 and isinstance(self.entries[0], tk.Text):
            try:
                json_str = self.get_entry_value(self.entries[0])
                # First verify it's valid JSON
                values = json.loads(json_str)
                if not isinstance(values, list):
                    values = [values]

                # Now reconstruct the string but maintaining the exact format
                result = []
                for item in values:
                    if isinstance(item, dict):
                        # Handle the value field specially to maintain its format
                        if 'value' in item:
                            value = item['value']
                            if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                                # Keep complex values as is
                                value_str = value
                            else:
                                # Wrap simple values in quotes
                                value_str = f'"{value}"'
                            item['value'] = value_str
                        result.append(item)
                    else:
                        result.append(item)
                return result
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Invalid JSON format:\n{str(e)}")
                return None

        # Regular handling for individual entries
        values = []
        for entry in self.entries:
            value = self.get_entry_value(entry).strip()
            if not value:  # Skip empty entries
                continue
            try:
                if self.is_complex_type:
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict) and 'value' in parsed:
                            # Handle the special case of value field
                            value_content = parsed['value']
                            if isinstance(value_content, str) and (value_content.startswith('{') or value_content.startswith('[')):
                                parsed['value'] = value_content
                            else:
                                parsed['value'] = f'"{value_content}"'
                        values.append(parsed)
                    except json.JSONDecodeError:
                        values.append(value)
                elif self.element_type == "int":
                    clean_value = value.strip('[]"\' ')
                    values.append(int(float(clean_value)))
                elif self.element_type == "float":
                    clean_value = value.strip('[]"\' ')
                    values.append(float(clean_value))
                else:
                    clean_value = value.strip('[]"\' ')
                    values.append(clean_value)
            except ValueError as e:
                messagebox.showerror("Error",
                                    f"Invalid {self.element_type} format: {value}\nError: {str(e)}")
                return None
        return values

    def ok(self):
        self.result = self.validate_values()
        if self.result is not None:
            self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()
