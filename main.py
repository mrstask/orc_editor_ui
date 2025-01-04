import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyarrow
import pyarrow.orc as orc
import pandas as pd
import numpy as np


class EditDialog(tk.Toplevel):
    def __init__(self, parent, df, row_idx, visible_columns):
        super().__init__(parent)
        self.title("Edit Row")
        self.df = df
        self.row_idx = row_idx
        self.result = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create scrollable frame
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        self.edit_frame = ttk.Frame(canvas)

        canvas.configure(xscrollcommand=scrollbar.set)

        # Create edit widgets
        self.edit_widgets = {}
        for idx, col in enumerate(visible_columns):
            ttk.Label(self.edit_frame, text=col).grid(row=0, column=idx, padx=5)
            entry = ttk.Entry(self.edit_frame, width=20)
            entry.grid(row=1, column=idx, padx=5)
            value = df.iloc[row_idx][col]
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray):
                    entry_value = f"[{','.join(map(str, value))}]" if value.size > 0 else '[]'
                else:
                    entry_value = f"[{','.join(map(str, value))}]" if value else '[]'
            else:
                entry_value = str(value) if pd.notna(value) else ""
            entry.insert(0, entry_value)
            self.edit_widgets[col] = entry

        # Put the edit frame in the canvas
        canvas.create_window((0, 0), window=self.edit_frame, anchor="nw")

        # Layout
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Update scroll region when widgets are configured
        self.edit_frame.bind("<Configure>",
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))

    def save(self):
        self.result = {}
        for col, widget in self.edit_widgets.items():
            value = widget.get()
            original_dtype = self.df[col].dtype

            try:
                if value.startswith('[') and value.endswith(']'):
                    try:
                        items = value[1:-1].split(',')
                        items = [int(item.strip()) for item in items if item.strip()]
                        value = items
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid list format for column '{col}'")
                        return
                elif pd.api.types.is_integer_dtype(original_dtype):
                    value = 0 if not value.strip() else int(float(value))

                self.result[col] = value
            except (ValueError, TypeError):
                messagebox.showerror("Error",
                                     f"Invalid value for column '{col}'. Expected type: {original_dtype}")
                return

        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


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

                # Handle special column types
                for column in df_to_save.columns:
                    if df_to_save[column].dtype == 'object':
                        df_to_save[column] = df_to_save[column].apply(
                            lambda x: ','.join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(
                                x) if pd.notna(x) else None
                        )

                table = pyarrow.Table.from_pandas(df_to_save)
                with pyarrow.orc.ORCWriter(filename) as writer:
                    writer.write(table)
                messagebox.showinfo("Success", "File saved successfully")
            except Exception as e:
                import traceback
                print("Error saving file:", traceback.format_exc())
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                detail_msg = "Details:\n" + traceback.format_exc()
                messagebox.showerror("Detailed Error", detail_msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = ORCEditor(root)
    root.mainloop()
