"""Author links with locally bundled hover QR cards."""
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk

LINKS = (
    ("抖音主页", "https://v.douyin.com/x64M2NbYj0A/", "douyin.png", "扫码关注作者"),
    ("请我喝杯咖啡 · 支付宝", "https://qr.alipay.com/fkx16608y1puemmltuocze0",
     "coffee.png", "扫码请我喝杯咖啡"),
)


class AuthorLink:
    def __init__(self, parent, text, url, image, caption):
        self.url = url
        self.image_name = image
        self.caption = caption
        self.popup = None
        self.job = None
        self.photo = None
        self.button = ttk.Button(parent, text=text, command=self.open)
        self.button.pack(fill="x", pady=(7, 0))
        self.button.bind("<Enter>", self.enter)
        self.button.bind("<Leave>", self.leave)
        self.button.bind("<FocusIn>", self.enter)
        self.button.bind("<FocusOut>", self.leave)
        self.button.bind("<Destroy>", self.destroy)

    def open(self, _event=None):
        webbrowser.open(self.url)

    def cancel(self):
        if self.job is not None:
            self.button.after_cancel(self.job)
            self.job = None

    def enter(self, _event=None):
        self.cancel()
        if self.popup is None:
            self.job = self.button.after(250, self.show)

    def show(self):
        self.job = None
        if self.popup is not None:
            return
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        self.photo = tk.PhotoImage(file=str(root / "assets" / self.image_name))
        popup = self.popup = tk.Toplevel(self.button)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.configure(background="#d4dfd8", padx=1, pady=1)
        card = tk.Frame(popup, background="white", padx=12, pady=10)
        card.pack()
        tk.Label(card, image=self.photo, background="white").pack()
        tk.Label(card, text=self.caption, background="white", foreground="#244b3d",
                 font=("Microsoft YaHei UI", 10)).pack(pady=(6, 0))
        popup.update_idletasks()
        width, height = popup.winfo_reqwidth(), popup.winfo_reqheight()
        x = min(self.button.winfo_rootx(), popup.winfo_screenwidth() - width - 8)
        y = self.button.winfo_rooty() - height - 4
        if y < 0:
            y = self.button.winfo_rooty() + self.button.winfo_height() + 4
        popup.geometry(f"+{max(0, x)}+{max(0, y)}")
        for widget in (popup, card, *card.winfo_children()):
            widget.bind("<Enter>", self.enter)
            widget.bind("<Leave>", self.leave)
            widget.bind("<Button-1>", self.open)
            widget.configure(cursor="hand2")
        popup.deiconify()
        popup.lift()

    def leave(self, _event=None):
        self.cancel()
        self.job = self.button.after(180, self.hide_if_outside)

    def hide_if_outside(self):
        self.job = None
        x, y = self.button.winfo_pointerxy()
        for widget in (self.button, self.popup):
            if widget is not None and (
                widget.winfo_rootx() <= x < widget.winfo_rootx() + widget.winfo_width()
                and widget.winfo_rooty() <= y < widget.winfo_rooty() + widget.winfo_height()
            ):
                return
        self.hide()

    def hide(self):
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None

    def destroy(self, event):
        if event.widget is self.button:
            self.cancel()
            self.hide()
