"""Bundle the PNG decoder used by map tiles and QR assets."""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ["PIL.PngImagePlugin"]
excludedimports = collect_submodules(
    "PIL", lambda name: "ImagePlugin" in name and name != "PIL.PngImagePlugin"
)
