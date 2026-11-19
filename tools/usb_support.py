"""Detect installed Apple USB drivers without requiring an attached iPhone."""
import os
import winreg
from pathlib import Path


def has_apple_usb_driver():
    for service in ("USBAAPL64", "USBAAPL"):
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                rf"SYSTEM\CurrentControlSet\Services\{service}",
            ):
                return True
        except FileNotFoundError:
            continue
        except OSError:
            return None
    store = Path(os.environ["SystemRoot"]) / "System32/DriverStore/FileRepository"
    try:
        return any(
            path.name.lower().startswith(("usbaapl", "appleusb.inf_"))
            for path in store.iterdir()
        )
    except OSError:
        return None
