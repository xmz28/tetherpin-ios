"""On-demand Windows location with an IP estimate fallback."""
import json
import math
import os
import subprocess
import urllib.request
from pathlib import Path

WINDOWS_QUERY = r"""
Add-Type -AssemblyName System.Device
$watcher = New-Object System.Device.Location.GeoCoordinateWatcher
try {
    $null = $watcher.TryStart($false, [TimeSpan]::FromSeconds(8))
    $position = $watcher.Position.Location
    if (!$position.IsUnknown) {
        @{latitude=$position.Latitude; longitude=$position.Longitude} | ConvertTo-Json -Compress
    }
} finally { $watcher.Dispose() }
"""


def validate_position(data):
    lat, lon = float(data["latitude"]), float(data["longitude"])
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("Invalid coordinates")
    return lat, lon


def locate_computer(update):
    executable = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    try:
        result = subprocess.run(
            [str(executable), "-NoProfile", "-NonInteractive", "-Command", WINDOWS_QUERY],
            capture_output=True, text=True, timeout=12,
            creationflags=subprocess.CREATE_NO_WINDOW, check=True,
        )
        lat, lon = validate_position(json.loads(result.stdout))
        return lat, lon, "Windows 定位"
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        update("Windows 定位不可用，正在查询本机出口 IP 的大致位置…")
    request = urllib.request.Request(
        "https://ipwho.is/", headers={"User-Agent": "TetherPin/1.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read(65537))
    except OSError:
        # Windows curl uses the system TLS stack, including local proxy certificates.
        curl = Path(os.environ["SystemRoot"]) / "System32/curl.exe"
        result = subprocess.run(
            [str(curl), "--fail", "--silent", "--show-error", "--max-time", "8",
             "--max-filesize", "65536", request.full_url],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW, check=True,
        )
        data = json.loads(result.stdout)
    lat, lon = validate_position(data)
    return lat, lon, "IP 估算位置（可能是网络出口或 VPN 所在地）"
