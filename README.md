# TetherPin

TetherPin 是一个 Windows 桌面工具，可以在 OpenStreetMap 上选点，并通过 USB 向 iPhone 提供 iAP2 配件定位。也可以使用地点预设或直接输入经纬度。

## 使用

1. 从 GitHub Releases 下载 Windows x64 版 `TetherPin.exe`，双击运行。电脑需要 Apple 设备或 iTunes 提供的 USB 驱动和服务。
2. 用数据线连接 iPhone，解锁并在手机上信任这台电脑。如果连接失败，先点「打开 Apple 设备」确认电脑能识别手机。缺少 USB 支持时，点「安装 Apple USB 支持」可通过 WinGet 安装微软商店的 Apple 设备。WinGet 不可用或安装失败时会打开官方商店页面。
3. 在地图上点击目标位置，或在右侧选择预设、输入十进制度经纬度。点「开始模拟」。
4. 打开苹果地图，点「我的位置」确认蓝点是否移动。地图版需要联网加载 OpenStreetMap，预设和手输坐标可在地图加载失败时使用。
5. 点「停止」并拔线，再在苹果地图确认真实定位已恢复。

首次运行模拟时，若本机缺少认证材料，程序会从 DiPlay 的 GitHub Release 下载固定版本的 APK，验证 SHA-256 后在本机导入配件证书和私钥。APK 只在电脑端读取。公开版 `TetherPin.exe` 和 Git 源码均不包含认证材料。来源与格式见[认证说明](docs/authentication.md)。

## 重插或定位不更新

- 拔线会结束当前会话。重插、解锁后，重新点「开始模拟」。
- 「坐标已发送」表示 iAP2 链路已确认数据。以苹果地图的当前定位蓝点为准。
- 确认「设置 → 隐私与安全性 → 定位服务 → 系统服务 → 系统自定义」已开启。保持插线、保持发送，关闭定位服务约 10 秒再打开，回苹果地图重新请求位置。
- 如果 USB 和认证正常、蓝点仍停在实际位置，可拔线重启 iPhone，解锁后再试。此步骤已在项目的一次重插复测中恢复定位，其他设备和 iOS 版本的结果可能不同。

## 从源码运行与打包

在 Windows x64 上准备 [Python 3.12](https://www.python.org/)（含 Tcl/Tk）和 [uv](https://docs.astral.sh/uv/)。

```powershell
uv sync --locked --python 3.12
uv run --no-sync python tools/portable_gui.py
uv run --no-sync pytest -p no:xonsh -q
```

构建单文件 EXE：

```powershell
uv pip install --python .venv\Scripts\python.exe pyinstaller==6.16.0
.venv\Scripts\python.exe -m PyInstaller --noconfirm TetherPin.spec
```

产物在 `dist/TetherPin.exe`。打包保留 PyMobileDevice3 的 USB 依赖，省去界面无须使用的 Jedi 补全文件和 Pillow。地图的 PNG 由 Tk 直接渲染。

### 自用版内置认证材料

如果你已有配件证书和匹配私钥，可以用同一份源码构建 `TetherPin-Offline.exe`。它会直接从可执行文件携带的数据中读取认证材料，首次模拟也无需下载 APK。

```powershell
$env:TETHERPIN_IDENTITY_DIR = Join-Path $env:LOCALAPPDATA 'iap2-location-bridge-windows\identity'
.venv\Scripts\python.exe -m PyInstaller --noconfirm TetherPin.spec
Remove-Item Env:TETHERPIN_IDENTITY_DIR
```

该目录须有 `certificate.p7b` 和 `identity.pk8`。内置数据可从 EXE 提取。Apple USB 支持单独由官方商店安装，OpenStreetMap 加载仍需要网络。

## 来源与许可

- 本项目基于 [iap2-location-bridge-windows](https://github.com/xpqball/iap2-location-bridge-windows) 的提交 `3d0af910ac6868df99978f593adb2fcbd2de8cc1)，后者源自 [accessory-location](https://github.com/aur3l14no/accessory-location)。详见[协议说明](docs/protocol.md)和[来源](docs/sources.md)。
- 地图数据来自 [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright)。
- 源码按 [GPL-3.0-only](LICENSE) 发布。
