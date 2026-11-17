"""Portable Windows frontend for the USB iAP2 location client."""
import asyncio
import os
import queue
import tempfile
import threading
import tkinter as tk
import urllib.request
from tkinter import ttk
from types import SimpleNamespace

from osm_map import MapPicker

from iap2_location_bridge_windows.auth import AuthenticationProvider
from iap2_location_bridge_windows.profile import coordinate

PRESETS = {
    "香港 · 九龙": (22.3193, 114.1694),
    "东京 · 东京站": (35.6812, 139.7671),
    "新加坡 · 滨海湾": (1.2834, 103.8607),
    "旧金山 · 市中心": (37.7749, -122.4194),
}
CUSTOM = "自定义坐标"
RESTORE = "已停止。请拔下 USB，在苹果地图点「我的位置」确认已恢复。"
IDENTITY_VARS = (
    "IAP2_LOCATION_BRIDGE_WINDOWS_CERT_FILE",
    "IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE",
)


class LocalAuthentication(AuthenticationProvider):
    def __init__(self):
        from local_mfi_v3_helper import LocalMfiV3

        self.helper = LocalMfiV3()

    async def request(self, operation, **fields):
        return self.helper.handle({"op": operation, **fields})

    async def close(self):
        pass


def prepare_identity(stopped, update):
    from import_diplay_identity import (
        APK_URL,
        ASSETS,
        MAX_APK_BYTES,
        IdentityImportError,
        default_identity_dir,
        read_identity,
        write_identity,
    )

    directory = default_identity_dir()
    if not directory.exists():
        update("首次使用，正在下载配件认证材料…")
        with tempfile.TemporaryFile() as stream:
            request = urllib.request.Request(APK_URL, headers={"User-Agent": "iAP2-Location"})
            with urllib.request.urlopen(request, timeout=15) as response:
                if not response.geturl().startswith("https://"):
                    raise IdentityImportError("Insecure redirect")
                total = 0
                next_update = 1024 * 1024
                while not stopped.is_set():
                    chunk = response.read1(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_APK_BYTES:
                        raise IdentityImportError("Download exceeds size limit")
                    stream.write(chunk)
                    if total >= next_update:
                        update(f"正在下载配件认证材料… {total // (1024 * 1024)} MB")
                        next_update += 1024 * 1024
            if stopped.is_set():
                return None
            identity = read_identity(stream)
            try:
                write_identity(identity, directory)
            except (OSError, IdentityImportError):
                if not all((directory / name).is_file() for name in ASSETS):
                    raise
    for variable, name in zip(IDENTITY_VARS, ASSETS):
        os.environ[variable] = str(directory / name)
    provider = LocalAuthentication()
    provider.helper.load()
    return provider


def open_apple_devices():
    os.startfile(r"shell:AppsFolder\AppleInc.AppleDevices_nzyj5cx40ttqa!App")


class LocationApp:
    def __init__(self, root):
        self.root = root
        self.messages = queue.SimpleQueue()
        self.stopped = threading.Event()
        self.worker = None
        self.closing = False
        self.place = tk.StringVar(value=next(iter(PRESETS)))
        self.latitude = tk.StringVar()
        self.longitude = tk.StringVar()
        self.status = tk.StringVar(value="请用 USB 连接 iPhone，解锁并信任这台电脑。")

        root.title("TetherPin · iPhone USB 定位")
        root.geometry("1080x650")
        root.minsize(820, 560)
        root.configure(bg="#edf1ee")
        style = ttk.Style(root)
        style.theme_use("clam")
        font = ("Microsoft YaHei UI", 10)
        style.configure(".", font=font)
        style.configure("Shell.TFrame", background="#edf1ee")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("Map.TFrame", background="#dfe8e5")
        style.configure("TLabel", foreground="#183329", background="#ffffff")
        style.configure("Header.TLabel", foreground="#17352b", background="#edf1ee",
                        font=("Microsoft YaHei UI", 22, "bold"))
        style.configure("Subtitle.TLabel", foreground="#4f665e", background="#edf1ee")
        style.configure("Section.TLabel", font=("Microsoft YaHei UI", 14, "bold"))
        style.configure("Quiet.TLabel", foreground="#50665d")
        style.configure("Status.TLabel", foreground="#244b3d", background="#e8f2ed", padding=12)
        style.configure("TButton", padding=(9, 8), background="#edf2ef", foreground="#204638",
                        borderwidth=0, focusthickness=1)
        style.configure("Map.TButton", padding=(4, 2), background="#ffffff",
                        font=("Segoe UI", 13, "bold"))
        style.configure("Primary.TButton", background="#146550", foreground="#ffffff",
                        font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Primary.TButton", background=[("disabled", "#dce7e0"), ("active", "#0f503f")],
                  foreground=[("disabled", "#48645a"), ("!disabled", "#ffffff")])
        style.configure("TCombobox", padding=6, arrowsize=16)
        style.configure("TEntry", padding=6, fieldbackground="#f6f8f7")

        shell = ttk.Frame(root, padding=(22, 17, 22, 22), style="Shell.TFrame")
        shell.pack(fill="both", expand=True)
        header = ttk.Frame(shell, style="Shell.TFrame")
        header.pack(fill="x", pady=(0, 15))
        ttk.Label(header, text="TetherPin", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="点击地图选点 · 拖动平移 · 滚轮缩放",
                  style="Subtitle.TLabel").pack(side="right", pady=(11, 0))

        content = ttk.Frame(shell, style="Shell.TFrame")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        self.map = MapPicker(content, self.pick_location)
        self.map.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        side = ttk.Frame(content, style="Panel.TFrame", padding=(18, 18))
        side.grid(row=0, column=1, sticky="ns")
        side.columnconfigure(0, weight=1)
        side.rowconfigure(6, weight=1)

        ttk.Label(side, text="目标位置", style="Section.TLabel").grid(sticky="w")
        ttk.Label(side, text="地点预设", style="Quiet.TLabel").grid(sticky="w", pady=(17, 5))
        self.selector = ttk.Combobox(
            side, textvariable=self.place, values=(*PRESETS, CUSTOM), state="readonly", width=25,
        )
        self.selector.grid(sticky="ew", pady=(0, 13))
        self.selector.bind("<<ComboboxSelected>>", self.select_place)

        fields = ttk.Frame(side, style="Panel.TFrame")
        fields.grid(sticky="ew")
        for column, label, value in ((0, "纬度", self.latitude), (1, "经度", self.longitude)):
            fields.columnconfigure(column, weight=1)
            ttk.Label(fields, text=label, style="Quiet.TLabel").grid(row=0, column=column, sticky="w")
            entry = ttk.Entry(fields, textvariable=value, width=11)
            entry.grid(row=1, column=column, sticky="ew",
                       padx=(0, 6) if column == 0 else (6, 0), pady=(5, 0))
            entry.bind("<Return>", self.sync_pin)
            entry.bind("<FocusOut>", self.sync_pin)
            if column == 0:
                self.lat_entry = entry
            else:
                self.lon_entry = entry

        actions = ttk.Frame(side, style="Panel.TFrame")
        actions.grid(sticky="ew", pady=(17, 12))
        self.start_button = ttk.Button(
            actions, text="开始模拟", style="Primary.TButton", command=self.start
        )
        self.start_button.pack(side="left", fill="x", expand=True)
        self.stop_button = ttk.Button(actions, text="停止", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=(7, 0))
        ttk.Label(side, textvariable=self.status, style="Status.TLabel", wraplength=206,
                  justify="left").grid(sticky="ew")
        ttk.Button(side, text="打开 Apple 设备", command=self.launch_apple_devices).grid(
            row=7, sticky="ew", pady=(14, 0),
        )

        root.protocol("WM_DELETE_WINDOW", self.close)
        self.select_place()
        root.after(75, self.poll)

    def pick_location(self, latitude, longitude):
        self.place.set(CUSTOM)
        self.latitude.set(f"{latitude:.6f}")
        self.longitude.set(f"{longitude:.6f}")
        self.map.set_pin(latitude, longitude)
        self.select_place()

    def coordinates(self):
        latitude, longitude = float(self.latitude.get()), float(self.longitude.get())
        coordinate(latitude, True)
        coordinate(longitude, False)
        return latitude, longitude

    def sync_pin(self, _event=None):
        if self.worker or self.place.get() != CUSTOM:
            return
        try:
            point = self.coordinates()
        except ValueError:
            return
        if self.map.pin and all(abs(a - b) < 0.000001 for a, b in zip(self.map.pin, point)):
            return
        self.map.set_pin(*point, recenter=True)

    def select_place(self, _event=None, *, recenter=True):
        preset = PRESETS.get(self.place.get())
        if preset:
            self.latitude.set(str(preset[0]))
            self.longitude.set(str(preset[1]))
            if recenter:
                self.map.set_pin(*preset, recenter=True)
        state = "readonly" if preset or self.worker else "normal"
        self.lat_entry.configure(state=state)
        self.lon_entry.configure(state=state)

    def launch_apple_devices(self):
        try:
            open_apple_devices()
        except OSError:
            self.status.set("请从 Microsoft Store 安装 Apple 设备，并完成 iPhone 信任配对。")

    def start(self):
        if self.worker is not None:
            return
        try:
            latitude, longitude = self.coordinates()
        except ValueError:
            self.status.set("请输入十进制度坐标。纬度 −90 至 90，经度 −180 至 180。")
            return
        self.sync_pin()
        self.map.pick_enabled = False
        self.stopped.clear()
        self.status.set("正在准备 USB 定位…")
        self.worker = threading.Thread(target=self.run, args=(latitude, longitude), daemon=True)
        self.selector.configure(state="disabled")
        self.lat_entry.configure(state="readonly")
        self.lon_entry.configure(state="readonly")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.worker.start()

    def stop(self):
        self.stopped.set()
        self.stop_button.configure(state="disabled")
        self.status.set("正在停止…")

    def close(self):
        if self.worker is None:
            self.root.destroy()
        else:
            self.closing = True
            self.stop()

    def poll(self):
        while True:
            try:
                kind, message = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "done":
                if self.closing:
                    self.root.destroy()
                    return
                self.worker = None
                self.selector.configure(state="readonly")
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.map.pick_enabled = True
                self.select_place(recenter=False)
                self.status.set(message)
            elif not self.stopped.is_set():
                self.status.set(message)
        self.root.after(75, self.poll)

    def update(self, message):
        self.messages.put(("status", message))

    def run(self, latitude, longitude):
        try:
            from import_diplay_identity import IdentityImportError
            from local_mfi_v3_helper import ProviderError

            from iap2_location_bridge_windows import cli
        except ImportError as error:
            self.messages.put(("done", f"无法加载定位组件（{error.name}）。"))
            return

        sent = False
        connected = False
        result = "已停止。"

        def report(**event):
            nonlocal sent, connected
            kind = event["event"]
            if kind == "device_connected":
                connected = True
                self.update("iPhone 已连接，正在认证定位配件…")
            elif kind == "authentication_succeeded" and not sent:
                self.update("认证已通过。请打开苹果地图并点击「我的位置」。")
            elif kind == "location_requested":
                if not sent:
                    self.update("iPhone 已请求定位，正在发送坐标…")
            elif kind == "location_link_acknowledged":
                sent = True
                self.update("坐标已发送。请用苹果地图确认蓝点。必要时关闭定位服务约 10 秒再打开。")

        async def send(provider):
            args = SimpleNamespace(
                transport="usb", command="send", auth_helper=None, duration=900, interval=1,
                latitude=latitude, longitude=longitude,
            )
            task = asyncio.create_task(cli.run(args, provider=provider, report=report))
            try:
                while not task.done() and not self.stopped.is_set():
                    await asyncio.sleep(0.1)
                if not task.done():
                    task.cancel()
                await task
            except asyncio.CancelledError:
                if not self.stopped.is_set():
                    raise

        try:
            provider = prepare_identity(self.stopped, self.update)
            if provider is not None and not self.stopped.is_set():
                self.update("正在连接 iPhone…")
                asyncio.run(send(provider))
                if sent:
                    result = RESTORE
                elif not self.stopped.is_set():
                    result = "本次未发送坐标。请检查定位服务和「系统自定义」，再打开苹果地图重试。"
        except (IdentityImportError, ProviderError, urllib.error.URLError) as error:
            result = f"认证材料准备失败（{type(error).__name__}）。请检查 GitHub 网络连接后重试。"
        except Exception as error:
            if sent:
                result = RESTORE
            elif self.stopped.is_set():
                result = "已停止。"
            elif connected:
                result = f"连接中断（{type(error).__name__}）。请保持 iPhone 解锁、插线后重试。"
            else:
                result = "未连接到 iPhone。请打开 Apple 设备，解锁手机并完成信任，再试一次。"
        if self.stopped.is_set() and not sent:
            result = "已停止。"
        self.messages.put(("done", result))


def main():
    root = tk.Tk()
    LocationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
