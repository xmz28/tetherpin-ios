# TetherPin

Windows 上的 iPhone USB 配件定位工具。通过 OpenStreetMap 点击选点，或选择地点预设、输入经纬度，将目标坐标通过 iAP2 发送给已连接的 iPhone。默认位置为香港九龙。

## 功能

- 地图点击选点、拖动平移、平滑缩放，加载新瓦片时保留已浏览地图作缓冲。
- 香港九龙、东京、新加坡、旧金山预设，以及手动输入十进制度经纬度。
- 本机位置优先查询 Windows 定位服务，可利用 Wi-Fi 等系统定位来源，失败后查询出口 IP 的大致位置。
- 开始和停止 USB 定位，显示连接、配件认证和坐标发送状态。
- 提供官方 Apple 设备的安装入口。
- 右侧「抖音主页」「请我喝杯咖啡」悬停显示二维码，点击打开对应网页。二维码在入口左侧显示，鼠标离开入口即关闭。

## 下载与运行

从 [Latest Release](https://github.com/xmz28/tetherpin-ios/releases/latest) 下载 [TetherPin.exe](https://github.com/xmz28/tetherpin-ios/releases/latest/download/TetherPin.exe)，双击运行。

发布提供一个 Windows x64 单文件程序 **TetherPin.exe**，内置配件证书和匹配私钥，首次使用也无需下载认证材料。源码仓库不包含证书和私钥。

启动时会在后台检查本机已安装的 Apple USB 驱动，无需先连接手机。检测到驱动后正常使用，缺少驱动时在状态栏提示安装。权限导致检测无法完成时，可通过安装入口和 Apple 设备手动确认。

右侧入口从上至下为「本机位置」「安装 USB 支持」「打开 Apple 设备」「抖音主页」「请我喝杯咖啡 · 支付宝」。作者入口悬停显示二维码，点击打开网页。

EXE 自带 Python 运行环境。Windows 仍需 Apple 设备或 iTunes 提供的 USB 驱动和服务。缺少时可点「安装 USB 支持」，程序确认后通过 WinGet 从 Microsoft Store 安装 Apple 设备，失败时打开官方商店页面。

地图加载、IP 定位和驱动安装需要网络。EXE 当前未做 Authenticode 签名。

## 使用步骤

1. 用支持数据传输的 USB 线连接 iPhone，解锁并信任电脑。先在 Apple 设备中确认电脑能识别手机。
2. 开启 iPhone「设置 → 隐私与安全性 → 定位服务」，在「系统服务」中开启「系统自定义」。允许苹果地图使用精确位置。
3. 在 TetherPin 选择预设、点击地图或输入坐标，点「开始模拟」。
4. 打开苹果地图，点「我的位置」，观察当前定位蓝点。必要时保持插线和程序发送，关闭定位服务约 10 秒后重新打开，再回地图请求位置。
5. 使用结束点「停止」，拔下 USB，并在苹果地图重新请求真实位置，确认恢复。

点击「本机位置」只会选取坐标并移动地图，确认后再点「开始模拟」。Windows 定位依赖系统服务和权限，IP 估算可能显示 VPN、代理或宽带出口所在地，可在地图上继续微调。

## 窗口与显示缩放

右侧操作面板使用紧凑布局，在 125% 等显示缩放或较小窗口下，超出的内容可通过面板滚动条或鼠标滚轮访问。鼠标位于地图上时，滚轮仍用于地图缩放。

## 常见问题

**坐标已发送，但地图没移动**

此状态表示定位包获得 iAP2 链路确认，最终位置以 iPhone 蓝点为准。检查地图权限和「系统自定义」，尝试上述开关定位流程。

**重插后定位无效**

拔线会结束当前会话，重插并解锁后需要重新开始模拟。如果认证正常且开关定位仍无效，可拔线重启 iPhone，再连接重试。本项目曾在一次实测中通过重启恢复。

**地图暂时不可用**

等待网络恢复，或先用预设、手动经纬度选点。已浏览瓦片按缓存策略保存在电脑上。程序不会下载整座城市的离线地图。

**可以开启 Apple Watch 的地区功能吗**

程序提供配件定位。地区功能还取决于设备、系统和服务可用性。项目曾在用户设备上完成高血压通知设置，其他设备组合需要自行验证。

**退出后还显示旧位置**

退出程序不等于真实定位已恢复。拔线后重新请求位置，必要时开关定位服务、重开地图，并等待重新定位。

## 认证材料与本地数据

发布的 TetherPin.exe 内置共享配件证书和匹配私钥，内置数据可被提取。源码仓库排除这些文件。源码运行时，本机缺少身份材料则按需下载固定版本 DiPlay APK，校验 SHA-256 后在电脑端提取认证材料，APK 不会安装到 iPhone。

该共享身份来自 DiPlay 所引用的 Carlinkit 固件，第三方认证材料没有按本项目 GPL 许可证重新授权，详见[认证材料来源与边界](docs/authentication.md)。

认证缓存和地图缓存保存在 `%LOCALAPPDATA%\iap2-location-bridge-windows`。本机位置仅在点击按钮时查询，IP 回退通过 HTTPS 访问 ipwho.is。二维码图片随程序打包，显示二维码无需联网。

## 从源码运行

在 Windows x64 上安装 Python 3.12（含 Tcl/Tk）和 uv，然后执行：

```powershell
uv sync --locked --python 3.12
uv run --no-sync python tools/portable_gui.py
```

检查代码：

```powershell
uv run --no-sync ruff check src tests tools
uv run --no-sync pytest -p no:xonsh -q
```

## 打包 Windows 单文件版

```powershell
uv pip install --python .venv\Scripts\python.exe pyinstaller==6.16.0
.venv\Scripts\python.exe -m PyInstaller --noconfirm TetherPin.spec
```

输出为 `dist/TetherPin.exe`。

打包前在本机准备配件证书和匹配私钥。默认读取 `%LOCALAPPDATA%\iap2-location-bridge-windows\identity`，也可以使用环境变量指定：

```powershell
$env:TETHERPIN_IDENTITY_DIR = 'C:\你的本机认证目录'
.venv\Scripts\python.exe -m PyInstaller --noconfirm TetherPin.spec
Remove-Item Env:TETHERPIN_IDENTITY_DIR
```

目录须包含 `certificate.p7b` 和 `identity.pk8`。构建会检查文件存在，再将其加入 EXE，缺少材料时会停止。产物统一为 `dist/TetherPin.exe`。这些材料与 EXE 都已在 Git 忽略规则中，公开源码只保留读取和打包逻辑。

## 关注与支持

| 抖音主页 | 请我喝杯咖啡 · 支付宝 |
| --- | --- |
| [打开抖音主页](https://v.douyin.com/x64M2NbYj0A/) | [打开支付宝支持链接](https://qr.alipay.com/fkx16608y1puemmltuocze0) |
| ![抖音主页二维码](assets/douyin.png) | ![支付宝支持二维码](assets/coffee.png) |

Copyright © 2026 xmz28

## 来源与许可

- 本项目基于 [iap2-location-bridge-windows](https://github.com/xpqball/iap2-location-bridge-windows) 的提交 `3d0af910ac6868df99978f593adb2fcbd2de8cc1`，上游源自 [accessory-location](https://github.com/aur3l14no/accessory-location)。
- 协议与研究来源见[协议说明](docs/protocol.md)和[来源记录](docs/sources.md)。
- 地图数据来自 [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright)。
- 源码按 [GPL-3.0-only](LICENSE) 发布，依赖遵循各自许可证，见[第三方声明](THIRD_PARTY_NOTICES.md)。
