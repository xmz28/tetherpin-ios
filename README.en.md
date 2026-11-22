# TetherPin

[简体中文](README.md) · **English**

TetherPin is a Windows tool for sending accessory location updates to an iPhone over USB. Pick a point on OpenStreetMap, choose a preset, or enter latitude and longitude. The coordinates are sent over iAP2. The default location is Kowloon, Hong Kong.

## Features

- Click to select a map location, drag to pan, and zoom smoothly. Previously viewed tiles remain visible while new ones load.
- Presets for Kowloon, Tokyo, Singapore and San Francisco, plus manual decimal latitude and longitude.
- Find the computer's location using Windows location services first, with approximate public-IP geolocation as a fallback.
- Start and stop USB location updates and view connection, accessory authentication and coordinate delivery status.
- Links to install and open Apple's device software. Hover over the Douyin and support buttons to show QR codes, or click them to open their pages.

## Download and run

Download [TetherPin.exe](https://github.com/xmz28/tetherpin-ios/releases/latest/download/TetherPin.exe) from the [latest release](https://github.com/xmz28/tetherpin-ios/releases/latest) and run it on Windows x64.

The single-file executable includes Python, an accessory certificate and its matching private key. The source repository excludes these credentials. The executable is not Authenticode-signed.

On startup, TetherPin checks for Apple USB support in the background, even if no phone is connected. If the driver is missing, the status bar offers an installation entry. If permissions prevent detection, check manually using Apple Devices.

Apple Devices or iTunes must provide the Windows USB driver and services. The **Install USB support** action asks for confirmation, then uses WinGet to install Apple Devices from the Microsoft Store. If that fails, it opens the official store page. Internet access is required for map tiles, IP-based location and driver installation.

The right panel contains **My location**, **Install USB support**, **Open Apple Devices**, **Douyin**, and **Buy me a coffee · Alipay**. The author buttons show their QR codes on hover.

## Use

1. Connect an iPhone with a data-capable USB cable, unlock it, and trust the computer. Confirm Apple Devices can see the phone.
2. On the iPhone, enable **Settings → Privacy & Security → Location Services → System Services → System Customization**. Allow Apple Maps to use precise location.
3. Choose a preset, click the map, or enter coordinates, then click **Start simulation**.
4. Open Apple Maps and tap **My Location** to check the blue dot. If needed, keep the cable and program running, turn Location Services off for about 10 seconds, then turn it back on and request the location again.
5. Click **Stop**, unplug USB, and request the real location again in Apple Maps to confirm it has recovered.

**My location** only selects coordinates and moves the map. Start simulation separately after checking them. Windows location depends on system services and permission; IP fallback may point to a VPN, proxy or broadband exit, so adjust the point on the map if needed.

## Window and display scaling

The right panel scrolls when content exceeds the available height, such as at 125% display scaling or in a small window. The mouse wheel still zooms the map when the pointer is over it.

## Troubleshooting

**Coordinates sent, but the map did not move** — This means the iAP2 link acknowledged the location packet. Check the iPhone's blue dot, Maps permission and System Customization, then try the Location Services toggle above.

**Location no longer works after reconnecting** — Unplugging ends the session. Reconnect, unlock and start the simulation again. If authentication succeeds but toggling Location Services does not help, restart the iPhone and reconnect. A restart restored one tested device.

**Map unavailable** — Wait for connectivity or choose a preset or manual coordinates. Viewed tiles are cached according to the cache policy; the app does not download entire cities for offline use.

**Can it enable Apple Watch regional features?** — The program supplies accessory location. Availability also depends on the device, OS and service. Hypertension notification setup succeeded on one user's device; other combinations require testing.

**The old location remains after quitting** — Quitting does not confirm real location has returned. Unplug the cable and request location again; if necessary, toggle Location Services, reopen Maps and wait for a new fix.

## Authentication and local data

The released EXE embeds a shared accessory certificate and matching private key, which can be extracted from the binary. The source repository excludes them. When running from source without local credentials, the app can download a pinned DiPlay APK, verify its SHA-256 and extract the authentication material on the computer; the APK is not installed on the iPhone.

The shared identity comes from Carlinkit firmware referenced by DiPlay. These third-party credentials are not relicensed under this project's GPL license. See [authentication provenance](docs/authentication.md).

Authentication and map caches are stored in `%LOCALAPPDATA%\iap2-location-bridge-windows`. Computer location is queried only when requested; IP fallback calls ipwho.is over HTTPS. QR images are bundled and require no network to display.

## Run from source

Install Python 3.12 with Tcl/Tk and uv on Windows x64:

```powershell
uv sync --locked --python 3.12
uv run --no-sync python tools/portable_gui.py
```

Run checks:

```powershell
uv run --no-sync ruff check src tests tools
uv run --no-sync pytest -p no:xonsh -q
```

## Build the Windows executable

```powershell
uv pip install --python .venv\Scripts\python.exe pyinstaller==6.16.0
.venv\Scripts\python.exe -m PyInstaller --noconfirm TetherPin.spec
```

The output is `dist/TetherPin.exe`. Prepare the accessory certificate and matching private key locally before packaging. The default directory is `%LOCALAPPDATA%\iap2-location-bridge-windows\identity`; alternatively:

```powershell
$env:TETHERPIN_IDENTITY_DIR = 'C:\path\to\your\local\identity'
.venv\Scripts\python.exe -m PyInstaller --noconfirm TetherPin.spec
Remove-Item Env:TETHERPIN_IDENTITY_DIR
```

The directory must contain `certificate.p7b` and `identity.pk8`. Packaging checks for both files and embeds them in the EXE; it stops if they are missing. Credentials and the EXE are ignored by Git.

## Follow and support

| Douyin | Buy me a coffee · Alipay |
| --- | --- |
| [Open Douyin](https://v.douyin.com/x64M2NbYj0A/) | [Open Alipay support link](https://qr.alipay.com/fkx16608y1puemmltuocze0) |
| ![Douyin QR code](assets/douyin.png) | ![Alipay QR code](assets/coffee.png) |

Copyright © 2026 xmz28

## Sources and license

- Based on [iap2-location-bridge-windows](https://github.com/xpqball/iap2-location-bridge-windows) commit `3d0af910ac6868df99978f593adb2fcbd2de8cc1`, originally based on [accessory-location](https://github.com/aur3l14no/accessory-location).
- See the [protocol](docs/protocol.md) and [sources](docs/sources.md) documents.
- Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).
- Source code is [GPL-3.0-only](LICENSE). Dependencies retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).
