"""Scrollable sidebar that keeps controls accessible on high-DPI displays."""
import tkinter as tk
from tkinter import ttk


class ScrollPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.canvas = tk.Canvas(self, background="white", highlightthickness=0, width=300)
        self.bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.canvas, style="Panel.TFrame", padding=(14, 12))
        self.window = self.canvas.create_window(0, 0, anchor="nw", window=self.body)
        self.body.bind("<Configure>", self.update_layout)
        self.canvas.bind("<Configure>", self.update_layout)
        self.bind_all("<MouseWheel>", self.wheel, add="+")

    def update_layout(self, _event=None):
        self.canvas.configure(width=self.body.winfo_reqwidth())
        self.canvas.itemconfigure(self.window, width=self.canvas.winfo_width())
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if self.body.winfo_reqheight() > self.canvas.winfo_height():
            self.bar.pack(side="right", fill="y")
        else:
            self.bar.pack_forget()
            self.canvas.yview_moveto(0)

    def wheel(self, event):
        target = self.winfo_containing(event.x_root, event.y_root)
        while target is not None:
            if target is self:
                if self.body.winfo_reqheight() > self.canvas.winfo_height():
                    self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
                return "break"
            target = target.master
