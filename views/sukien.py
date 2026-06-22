import tkinter as tk
from tkinter import ttk

class SuKienTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Label(self, text="QUẢN LÝ HỌC PHÍ", font=("Arial", 14, "bold")).pack(pady=10)