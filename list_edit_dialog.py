import json
import platform
import tkinter as tk
from tkinter import ttk, messagebox


class ListEditDialog(tk.Toplevel):
    def __init__(self, parent, list_value, column_name, element_type="int"):
        super().__init__(parent)
        self.title(f"Edit List - {column_name}")
        self.list_value = list_value if list_value else []
        self.element_type = element_type
        self.result = None
        self.is_complex_type = element_type == "struct" or element_type == "str"

        # Determine if we're on Mac OS
        self.is_mac = platform.system() == 'Darwin'

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Configure dialog size and position
        self.geometry("800x600")

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

        # Create canvas with scrollbar
        self.create_scrollable_frame(list_frame)

        # Special handling for list of dictionaries
        if self.is_complex_type and self.list_value and isinstance(self.list_value[0], dict):
            self.setup_json_editor()
        else:
            self.setup_regular_editor()

        # Create control buttons
        self.create_control_buttons(main_frame)

        # Bind keyboard shortcuts
        self.bind_shortcuts()

    def create_control_buttons(self, main_frame):
        """Create control buttons for the dialog"""
        # Create Add/Remove buttons if not in JSON editor mode
        if not (self.is_complex_type and self.list_value and isinstance(self.list_value[0], dict)):
            control_frame = ttk.Frame(main_frame)
            control_frame.pack(fill=tk.X, pady=(0, 10))
            ttk.Button(control_frame, text="Add Item", command=self.add_entry).pack(side=tk.LEFT, padx=5)
            ttk.Button(control_frame, text="Remove Last", command=self.remove_last).pack(side=tk.LEFT, padx=5)

        # Create OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

    def create_scrollable_frame(self, parent):
        self.canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.entries_frame = ttk.Frame(self.canvas)
        self.entries_frame.columnconfigure(0, weight=1)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.entries_frame, anchor="nw")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_json_editor(self):
        self.json_text = tk.Text(self.entries_frame, height=20, width=80, undo=True)
        self.json_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        json_str = json.dumps(self.list_value, indent=2)
        self.json_text.insert("1.0", json_str)
        self.entries = [self.json_text]

        # Bind text widget shortcuts
        self.bind_text_shortcuts(self.json_text)

    def setup_regular_editor(self):
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

    def bind_shortcuts(self):
        # Global shortcuts
        if self.is_mac:
            self.bind_all('<Command-d>', self.duplicate_selection)
        else:
            self.bind_all('<Control-d>', self.duplicate_selection)

    def bind_text_shortcuts(self, widget):
        if self.is_mac:
            # Mac OS shortcuts
            widget.bind('<Command-c>', lambda e: self.copy_text(widget))
            widget.bind('<Command-v>', lambda e: self.paste_text(widget))
            widget.bind('<Command-x>', lambda e: self.cut_text(widget))
            widget.bind('<Command-z>', lambda e: self.undo_text(widget))
            widget.bind('<Command-d>', lambda e: self.duplicate_selection(widget))
        else:
            # Windows/Linux shortcuts
            widget.bind('<Control-c>', lambda e: self.copy_text(widget))
            widget.bind('<Control-v>', lambda e: self.paste_text(widget))
            widget.bind('<Control-x>', lambda e: self.cut_text(widget))
            widget.bind('<Control-z>', lambda e: self.undo_text(widget))
            widget.bind('<Control-d>', lambda e: self.duplicate_selection(widget))

    def bind_entry_shortcuts(self, entry):
        if self.is_mac:
            entry.bind('<Command-c>', lambda e: self.copy_entry(entry))
            entry.bind('<Command-v>', lambda e: self.paste_entry(entry))
            entry.bind('<Command-x>', lambda e: self.cut_entry(entry))
            entry.bind('<Command-d>', lambda e: self.duplicate_entry_selection(entry))
        else:
            entry.bind('<Control-c>', lambda e: self.copy_entry(entry))
            entry.bind('<Control-v>', lambda e: self.paste_entry(entry))
            entry.bind('<Control-x>', lambda e: self.cut_entry(entry))
            entry.bind('<Control-d>', lambda e: self.duplicate_entry_selection(entry))

    def copy_text(self, widget):
        try:
            widget.event_generate('<<Copy>>')
            return "break"
        except:
            pass

    def paste_text(self, widget):
        try:
            widget.event_generate('<<Paste>>')
            return "break"
        except:
            pass

    def cut_text(self, widget):
        try:
            widget.event_generate('<<Cut>>')
            return "break"
        except:
            pass

    def undo_text(self, widget):
        try:
            widget.edit_undo()
            return "break"
        except:
            pass

    def duplicate_selection(self, widget=None, event=None):
        if isinstance(widget, tk.Text):
            try:
                if widget.tag_ranges("sel"):
                    selected_text = widget.get("sel.first", "sel.second")
                    widget.insert("sel.second", selected_text)
                return "break"
            except:
                pass
        elif isinstance(widget, ttk.Entry):
            try:
                selected_text = widget.selection_get()
                current_text = widget.get()
                sel_start = widget.index("sel.first")
                sel_end = widget.index("sel.second")
                widget.delete(0, tk.END)
                widget.insert(0, current_text[:sel_end] + selected_text + current_text[sel_end:])
                return "break"
            except:
                pass

    def copy_entry(self, entry):
        try:
            entry.event_generate('<<Copy>>')
            return "break"
        except:
            pass

    def paste_entry(self, entry):
        try:
            entry.event_generate('<<Paste>>')
            return "break"
        except:
            pass

    def cut_entry(self, entry):
        try:
            entry.event_generate('<<Cut>>')
            return "break"
        except:
            pass

    def duplicate_entry_selection(self, entry):
        try:
            selected_text = entry.selection_get()
            current_text = entry.get()
            sel_start = entry.index("sel.first")
            sel_end = entry.index("sel.second")
            entry.delete(0, tk.END)
            entry.insert(0, current_text[:sel_end] + selected_text + current_text[sel_end:])
            return "break"
        except:
            pass

    def add_entry(self, value=None):
        idx = len(self.entries)
        frame = ttk.Frame(self.entries_frame)
        frame.grid(row=idx, column=0, sticky="ew", pady=2)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text=f"{idx}:").grid(row=0, column=0, padx=(0, 5))

        if self.is_complex_type:
            entry = tk.Text(frame, height=4, width=80, undo=True)
            if value is not None:
                entry.insert("1.0", str(value))
            self.bind_text_shortcuts(entry)
        else:
            entry = ttk.Entry(frame)
            if value is not None:
                entry.insert(0, str(value))
            self.bind_entry_shortcuts(entry)

        entry.grid(row=0, column=1, sticky="ew")
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
        """Validate and convert all entry values."""
        if self.is_complex_type and len(self.entries) == 1 and isinstance(self.entries[0], tk.Text):
            return self._validate_complex_entry_with_json_editor()

        validated_values = []
        for entry in self.entries:
            entry_value = self.get_entry_value(entry).strip()
            if not entry_value:  # Skip empty entries
                continue

            try:
                if self.is_complex_type:
                    parsed_value = self._parse_json(entry_value)
                    if parsed_value is not None:
                        validated_values.append(parsed_value)
                else:
                    validated_values.append(self._convert_value(entry_value, self.element_type))
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid {self.element_type} format: {entry_value}\nError: {str(e)}")
                return None

        return validated_values

    def _validate_complex_entry_with_json_editor(self):
        """Handles complex entry validation when editing JSON directly."""
        entry_value = self.get_entry_value(self.entries[0])
        try:
            values = self._parse_json(entry_value)
            if not isinstance(values, list):
                values = [values]

            validated_values = []
            for entry in values:
                if isinstance(entry, dict) and 'value' in entry:
                    entry['value'] = (
                        entry['value']
                        if isinstance(entry['value'], str) and (
                                entry['value'].startswith("{") or entry['value'].startswith("["))
                        else entry["value"]
                    )
                validated_values.append(entry)
            return validated_values
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON format:\n{str(e)}")
            return None

    def _parse_json(self, value):
        """Parses a JSON string into a Python object."""
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict) and 'value' in parsed:
                if isinstance(parsed['value'], str):
                    parsed['value'] = parsed['value'].strip('"')
            return parsed
        except json.JSONDecodeError:
            return value

    def _convert_value(self, value, element_type):
        """Converts a value to the desired type (int, float, or str)."""
        clean_value = value.strip('[]"\' ')
        if element_type == "int":
            return int(float(clean_value))
        elif element_type == "float":
            return float(clean_value)
        else:
            return clean_value

    def ok(self):
        self.result = self.validate_values()
        if self.result is not None:
            self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()
