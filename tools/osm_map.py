"""Interactive OpenStreetMap tiles and Web Mercator coordinates."""
import base64
import math
import os
import queue
import re
import sqlite3
import time
import tkinter as tk
import urllib.error
import urllib.request
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from pathlib import Path
from tkinter import ttk

TILE = 256
MAX_LATITUDE = 85.05112878
TILE_URL = "https://tile.openstreetmap.org"
USER_AGENT = "TetherPin/1.0 (iPhone USB Location; Windows map picker)"
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def project(lat, lon, zoom):
    size = TILE * 2**zoom
    rad = math.radians(max(-MAX_LATITUDE, min(lat, MAX_LATITUDE)))
    return size * (lon + 180) / 360, size * (1 - math.asinh(math.tan(rad)) / math.pi) / 2


def unproject(x, y, zoom):
    size = TILE * 2**zoom
    y = max(0, min(y, size))
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / size)))), (
        x / size * 360 % 360 - 180
    )


class TileCache:
    def __init__(self):
        folder = Path(os.environ["LOCALAPPDATA"]) / "iap2-location-bridge-windows"
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / "osm-tiles.sqlite3"
        with self.connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS tiles (
                    id TEXT PRIMARY KEY, data BLOB, expires REAL, etag TEXT, modified TEXT
                )"""
            )

    def connect(self):
        return sqlite3.connect(self.path)

    def get(self, key):
        tile_id = "/".join(str(part) for part in key)
        now = time.time()
        with self.connect() as db:
            previous = db.execute(
                "SELECT data, expires, etag, modified FROM tiles WHERE id = ?", (tile_id,)
            ).fetchone()
        if previous and previous[1] > now:
            return previous[0]
        headers = {"User-Agent": USER_AGENT}
        if previous:
            if previous[2]:
                headers["If-None-Match"] = previous[2]
            if previous[3]:
                headers["If-Modified-Since"] = previous[3]
        request = urllib.request.Request(f"{TILE_URL}/{tile_id}.png", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                data = response.read(1_048_577)
                info = response.headers
            if not data.startswith(PNG_HEADER) or len(data) > 1_048_576:
                raise ValueError("Invalid map tile")
        except urllib.error.HTTPError as error:
            with error:
                if error.code != 304 or not previous:
                    raise
                data, info = previous[0], error.headers
        cache_control = info.get("Cache-Control", "")
        max_age = re.search(r"\bmax-age=(\d+)", cache_control, flags=re.IGNORECASE)
        expires = now + 7 * 24 * 60 * 60
        if max_age:
            expires = now + max(0, int(max_age[1]) - int(info.get("Age", "0")))
        elif info.get("Expires"):
            expires = parsedate_to_datetime(info["Expires"]).timestamp()
        if "no-store" not in cache_control.lower():
            etag = info.get("ETag") or (previous[2] if previous else None)
            modified = info.get("Last-Modified") or (previous[3] if previous else None)
            with self.connect() as db:
                db.execute(
                    "INSERT OR REPLACE INTO tiles VALUES (?, ?, ?, ?, ?)",
                    (tile_id, data, expires, etag, modified),
                )
        return data


class MapPicker(ttk.Frame):
    def __init__(self, parent, on_pick):
        super().__init__(parent, style="Map.TFrame")
        self.on_pick = on_pick
        self.zoom = 12
        self.center_lat, self.center_lon = 22.3193, 114.1694
        self.pin = None
        self.pick_enabled = True
        self.drag = None
        self.redraw_job = None
        self.pending = {}
        self.images = {}
        self.failed = set()
        self.results = queue.SimpleQueue()
        self.pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="osm")
        self.cache = None

        self.canvas = tk.Canvas(self, background="#dfe8e5", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        controls = ttk.Frame(self, style="Map.TFrame")
        controls.place(x=14, y=14)
        for row, (label, step) in enumerate((("+", 1), ("−", -1))):
            ttk.Button(
                controls, text=label, width=3, style="Map.TButton",
                command=lambda delta=step: self.change_zoom(delta),
            ).grid(row=row, pady=1)
        attribution = tk.Label(
            self, text="© OpenStreetMap contributors", background="#ffffff",
            foreground="#244d42", font=("Segoe UI", 9), cursor="hand2", padx=8, pady=4,
        )
        attribution.place(relx=1, rely=1, anchor="se")
        attribution.bind("<Button-1>", lambda _: webbrowser.open(
            "https://www.openstreetmap.org/copyright"
        ))
        self.canvas.bind("<Configure>", self.schedule_redraw)
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.bind("<Destroy>", self.shutdown, add="+")
        try:
            self.cache = TileCache()
        except (OSError, sqlite3.Error):
            pass
        self.after(70, self.poll)

    def shutdown(self, event):
        if event.widget is self:
            self.pool.shutdown(wait=False, cancel_futures=True)

    def viewport(self):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        x, y = project(self.center_lat, self.center_lon, self.zoom)
        return width, height, x - width / 2, y - height / 2

    def set_pin(self, lat, lon, *, recenter=False):
        self.pin = (lat, lon)
        if recenter:
            self.center_lat, self.center_lon = lat, lon
            self.failed.clear()
        self.schedule_redraw()

    def schedule_redraw(self, _event=None):
        if self.redraw_job is not None:
            self.after_cancel(self.redraw_job)
        self.redraw_job = self.after(55, self.redraw)

    def redraw(self):
        self.redraw_job = None
        width, height, left, top = self.viewport()
        self.canvas.delete("all")
        count = 2**self.zoom
        positions = [
            ((self.zoom, x % count, y), int(x * TILE - left), int(y * TILE - top))
            for y in range(max(0, math.floor(top / TILE)), min(count, math.ceil((top + height) / TILE)))
            for x in range(math.floor(left / TILE), math.ceil((left + width) / TILE))
        ]
        visible = {key for key, _, _ in positions}
        for key, future in list(self.pending.items()):
            if key not in visible and future.cancel():
                del self.pending[key]
        self.images = {key: image for key, image in self.images.items() if key in visible}
        for key, x, y in positions:
            if key in self.images:
                self.canvas.create_image(x, y, anchor="nw", image=self.images[key])
            elif self.cache and key not in self.pending and key not in self.failed:
                self.pending[key] = self.pool.submit(self.load_tile, key)
        if not self.images and (not self.cache or visible <= self.failed):
            self.canvas.create_text(
                width / 2, height / 2 - 36, text="地图暂不可用 · 可直接输入坐标",
                font=("Microsoft YaHei UI", 11), fill="#37564e",
            )
        if self.pin is not None:
            x, y = project(*self.pin, self.zoom)
            size = count * TILE
            x = (x - left - width / 2 + size / 2) % size - size / 2 + width / 2
            y -= top
            self.canvas.create_oval(x - 11, y - 11, x + 11, y + 11,
                                    fill="#136a55", outline="white", width=3)
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="white", outline="")

    def load_tile(self, key):
        try:
            data = self.cache.get(key)
        except (OSError, sqlite3.Error, ValueError):
            data = None
        self.results.put((key, data))

    def poll(self):
        changed = False
        while True:
            try:
                key, data = self.results.get_nowait()
            except queue.Empty:
                break
            self.pending.pop(key, None)
            if data is not None and key[0] == self.zoom:
                try:
                    self.images[key] = tk.PhotoImage(data=base64.b64encode(data), format="png")
                except tk.TclError:
                    self.failed.add(key)
            elif data is None:
                self.failed.add(key)
            changed = True
        if changed and self.redraw_job is None:
            self.schedule_redraw()
        self.after(70, self.poll)

    def change_zoom(self, step, point=None):
        zoom = max(2, min(19, self.zoom + step))
        if zoom == self.zoom:
            return
        width, height, left, top = self.viewport()
        x, y = point if point is not None else (width / 2, height / 2)
        anchor = unproject(left + x, top + y, self.zoom)
        self.zoom = zoom
        world_x, world_y = project(*anchor, zoom)
        self.center_lat, self.center_lon = unproject(
            world_x + width / 2 - x, world_y + height / 2 - y, zoom,
        )
        self.failed.clear()
        self.schedule_redraw()

    def wheel(self, event):
        if event.delta:
            self.change_zoom(1 if event.delta > 0 else -1, (event.x, event.y))

    def press(self, event):
        center = project(self.center_lat, self.center_lon, self.zoom)
        self.drag = event.x, event.y, center, False

    def pan(self, event):
        if self.drag is None:
            return
        start_x, start_y, center, moved = self.drag
        dx, dy = event.x - start_x, event.y - start_y
        if moved or abs(dx) + abs(dy) > 5:
            self.center_lat, self.center_lon = unproject(center[0] - dx, center[1] - dy, self.zoom)
            self.drag = start_x, start_y, center, True
            self.schedule_redraw()

    def release(self, event):
        if self.drag and not self.drag[3] and self.pick_enabled:
            _, _, left, top = self.viewport()
            self.on_pick(*unproject(left + event.x, top + event.y, self.zoom))
        self.drag = None
