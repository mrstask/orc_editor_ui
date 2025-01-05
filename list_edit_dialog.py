import tkinter as tk
from tkinter import ttk, messagebox

class ListEditDialog(tk.Toplevel):
    def __init__(self, parent, list_value, column_name, element_type="int"):
        super().__init__(parent)
        self.title(f"Edit List - {column_name}")
        self.list_value = list_value if list_value else []
        self.element_type = element_type
        self.result = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Configure dialog size and position
        self.geometry("400x500")

        # Create main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate listbox
        for item in self.list_value:
            self.listbox.insert(tk.END, str(item))

        # Create control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(control_frame, text="Add", command=self.add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Edit", command=self.edit_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Remove", command=self.remove_item).pack(side=tk.LEFT, padx=5)

        # Create OK/Cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                 parent.winfo_rooty() + 50))

    def add_item(self):
        dialog = ItemEditDialog(self, "", "Add Item", self.element_type)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.listbox.insert(tk.END, str(dialog.result))

    def edit_item(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to edit")
            return

        idx = selection[0]
        current_value = self.listbox.get(idx)
        dialog = ItemEditDialog(self, current_value, "Edit Item", self.element_type)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.listbox.delete(idx)
            self.listbox.insert(idx, str(dialog.result))

    def remove_item(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to remove")
            return

        self.listbox.delete(selection[0])

    def get_list_values(self):
        values = []
        for i in range(self.listbox.size()):
            value = self.listbox.get(i)
            try:
                if self.element_type == "int":
                    values.append(int(float(value)))
                elif self.element_type == "float":
                    values.append(float(value))
                else:
                    values.append(str(value))
            except ValueError:
                messagebox.showerror("Error", f"Invalid value format: {value}")
                return None
        return values

    def ok(self):
        self.result = self.get_list_values()
        if self.result is not None:
            self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class ItemEditDialog(tk.Toplevel):
    def __init__(self, parent, value, title, element_type="int"):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.element_type = element_type

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create and pack widgets
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Value:").pack(pady=(0, 5))
        self.entry = ttk.Entry(main_frame)
        self.entry.pack(fill=tk.X, pady=(0, 10))
        self.entry.insert(0, str(value))

        ttk.Button(main_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(main_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 100,
                                 parent.winfo_rooty() + 100))

    def validate_value(self, value):
        try:
            if self.element_type == "int":
                return int(float(value))
            elif self.element_type == "float":
                return float(value)
            else:
                return str(value)
        except ValueError:
            messagebox.showerror("Error", f"Invalid {self.element_type} format")
            return None

    def ok(self):
        value = self.entry.get()
        validated_value = self.validate_value(value)
        if validated_value is not None:
            self.result = validated_value
            self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()
