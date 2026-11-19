# Third-party notices

TetherPin contains modifications of xpqball/iap2-location-bridge-windows (baseline 3d0af910ac6868df99978f593adb2fcbd2de8cc1), itself derived from aur3l14no/accessory-location. This project retains GPL-3.0-only licensing. See LICENSE, docs/sources.md and docs/protocol.md.

The packaged Windows application uses Python, Tcl/Tk, PyMobileDevice3, cryptography, Pillow, pywin32 and their dependencies. Their license files, when provided by installed distribution metadata, are bundled under third_party_licenses in the executable extraction directory. The GPL applies to TetherPin source code. Each dependency retains its own license.

OpenStreetMap map data is provided by OpenStreetMap contributors under ODbL. The application displays map attribution and retrieves standard tiles according to the OpenStreetMap tile usage policy.
https://www.openstreetmap.org/copyright
https://operations.osmfoundation.org/policies/tiles/

The release executable also contains the shared experimental accessory certificate and matching private key previously imported from the pinned DiPlay v0.2.7 APK. Those materials are third-party accessory identity data, are extractable from the executable, and are not relicensed under TetherPin's GPL source license. They are excluded from the Git source repository. See docs/authentication.md for their provenance, pinned archive hash and limitations.
https://github.com/shihabal3amri/DiPlay/blob/main/docs/THIRD_PARTY_NOTICES.md
