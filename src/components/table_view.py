import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any

import pandas as pd


class TableView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
        self._setup_bindings()

        # Configure frame to expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.hide_empty_columns = True  # Default to hiding empty columns
        self.all_columns = []  # Store all columns
        self.visible_columns = []  # Store currently visible columns

    def update_data(self, df: pd.DataFrame) -> None:
        """Update the table with new DataFrame data.

        Args:
            df: pandas DataFrame containing the new data
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if df is None or df.empty:
            return

        # Store all columns
        self.all_columns = list(df.columns)

        # Determine visible columns based on hide_empty_columns flag
        self.visible_columns = self._get_visible_columns(df)

        # Configure columns
        self.tree["columns"] = self.visible_columns
        self.tree["show"] = "headings"

        # Setup column headings
        for col in self.visible_columns:
            self.tree.heading(col, text=col)
            max_width = max(
                len(str(col)),
                df[col].astype(str).str.len().max() if len(df) > 0 else 0
            )
            width = min(max(max_width * 10, 100), 300)
            self.tree.column(col, width=width)

        # Add data rows
        for idx, row in df.iterrows():
            values = []
            for col in self.visible_columns:
                value = row[col]
                if isinstance(value, (list, tuple)):
                    value = f"[{','.join(map(str, value))}]"
                elif pd.isna(value):
                    value = ""
                values.append(str(value))
            self.tree.insert("", "end", values=values)

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _get_visible_columns(self, df: pd.DataFrame) -> List[str]:
        """Determine which columns should be visible based on settings and content.

        Args:
            df: pandas DataFrame to analyze

        Returns:
            List of column names that should be visible
        """
        if not self.hide_empty_columns:
            return list(df.columns)

        visible = []
        for col in df.columns:
            # Check if column contains any non-empty values
            has_data = False
            for value in df[col]:
                if isinstance(value, (list, tuple)):
                    if len(value) > 0:
                        has_data = True
                        break
                elif pd.notna(value) and value != "":
                    has_data = True
                    break
            if has_data:
                visible.append(col)
        return visible

    def toggle_empty_columns(self, df: pd.DataFrame) -> None:
        """Toggle visibility of empty columns.

        Args:
            df: Current DataFrame to analyze
        """
        self.hide_empty_columns = not self.hide_empty_columns
        self.update_data(df)

    def _create_widgets(self):
        """Create the widgets for the table view"""
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(self)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        # Create frame for treeview
        self.tree_frame = ttk.Frame(self.canvas)
        self.tree = ttk.Treeview(self.tree_frame)

        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # Configure tree frame to expand
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self._layout_widgets()

    def _layout_widgets(self):
        """Layout the widgets in the frame"""
        # Layout canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        # Create window inside canvas
        self.canvas.create_window((0, 0), window=self.tree_frame, anchor="nw",
                                  width=self.canvas.winfo_width(),  # Make frame fill canvas
                                  height=self.canvas.winfo_height())

        # Pack tree inside tree_frame with expansion
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Update scroll region when frame changes
        self.tree_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        # Update the inner frame to match the canvas size
        width = event.width
        height = event.height
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0],
                               width=width,
                               height=height)

    def _setup_bindings(self):
        """Setup keyboard and mouse bindings"""
        # Bind mousewheel for vertical scrolling
        self.tree.bind("<MouseWheel>", self._on_mousewheel)
        self.tree.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)

        # Bind column resize to update canvas scroll region
        self.tree.bind("<Button-1>", self._on_click)

        # Update scroll region when tree changes
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_mousewheel(self, event):
        """Handle vertical mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        """Handle horizontal mousewheel scrolling"""
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_click(self, event):
        """Handle click events and update scroll region"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_select(self, event):
        """Handle tree selection events"""
        self.event_generate("<<TableViewSelect>>")

    def get_selection(self) -> List[int]:
        """Get the currently selected row indices.

        Returns:
            List of selected row indices
        """
        selection = self.tree.selection()
        return [self.tree.index(item) for item in selection] if selection else []

    def update_row(self, row_idx: int, values: Dict[str, Any]) -> None:
        """Update a specific row in the table.

        Args:
            row_idx: Index of the row to update
            values: Dictionary mapping column names to new values
        """
        # Get the item ID for the row
        item = self.tree.get_children()[row_idx]

        # Get current columns
        columns = self.tree["columns"]

        # Prepare new values in the correct order
        row_values = []
        for col in columns:
            value = values.get(col, "")
            if isinstance(value, (list, tuple)):
                value = f"[{','.join(map(str, value))}]"
            elif pd.isna(value):
                value = ""
            row_values.append(str(value))

        # Update the row
        self.tree.item(item, values=row_values)

    def get_column_widths(self) -> Dict[str, int]:
        """Get the current width of all columns.

        Returns:
            Dictionary mapping column names to their widths
        """
        return {col: self.tree.column(col, "width") for col in self.tree["columns"]}

    def set_column_widths(self, widths: Dict[str, int]) -> None:
        """Set the width of columns.

        Args:
            widths: Dictionary mapping column names to desired widths
        """
        for col, width in widths.items():
            if col in self.tree["columns"]:
                self.tree.column(col, width=width)

    def sort_by_column(self, column: str, reverse: bool = False) -> None:
        """Sort the table by a specific column.

        Args:
            column: Name of the column to sort by
            reverse: If True, sort in descending order
        """
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        items.sort(reverse=reverse)

        # Rearrange items in sorted positions
        for idx, (_, item) in enumerate(items):
            self.tree.move(item, "", idx)
