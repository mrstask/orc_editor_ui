import tkinter as tk
from src.ui.orc_editor import ORCEditor

if __name__ == "__main__":
    root = tk.Tk()
    app = ORCEditor(root)
    root.mainloop()
