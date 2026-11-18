"""Build dist/Taktpause.exe on Windows.

Used by the GitHub Actions workflow and for local builds. From the project
folder, in a Python 3.12 environment:

    python -m pip install -r requirements.txt -r requirements-build.txt
    python packaging/windows/build.py

The Windows version information is created from APP_VERSION in taktpause.py,
so a new release only needs a new APP_VERSION.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "taktpause.py"
ICON = ROOT / "assets" / "taktpause.ico"
BUILD_DIR = ROOT / "build"
VERSION_FILE = BUILD_DIR / "version_info.txt"

HIDDEN_IMPORTS = [
    "infi.systray",
    "infi.systray.traybar",
    "infi.systray.win32_adapter",
    "win32api",
    "win32con",
    "win32gui",
    "pywintypes",
    "win32timezone",
    "arabic_reshaper",
    "bidi.algorithm",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.PngImagePlugin",
]


def read_constant(name: str, text: str) -> str:
    match = re.search(rf'^{name} = "(.*)"$', text, re.MULTILINE)
    if not match:
        sys.exit(f"Could not find {name} in {SOURCE.name}")
    return match.group(1)


def version_tuple(version: str) -> tuple[int, int, int, int]:
    numbers = [int(part) for part in re.findall(r"\d+", version.split("-")[0])]
    numbers = (numbers + [0, 0, 0, 0])[:4]
    return tuple(numbers)  # type: ignore[return-value]


def write_version_file(version: str, author: str) -> None:
    numbers = version_tuple(version)
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(
        f"""VSVersionInfo(
    ffi=FixedFileInfo(
        filevers={numbers},
        prodvers={numbers},
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable(
                u'040904B0',
                [
                    StringStruct(u'CompanyName', u'{author}'),
                    StringStruct(u'FileDescription', u'Taktpause - Work and Break Timer'),
                    StringStruct(u'FileVersion', u'{version}'),
                    StringStruct(u'InternalName', u'Taktpause'),
                    StringStruct(u'LegalCopyright', u'Copyright \\u00a9 2026 {author}. GPL-3.0.'),
                    StringStruct(u'OriginalFilename', u'Taktpause.exe'),
                    StringStruct(u'ProductName', u'Taktpause'),
                    StringStruct(u'ProductVersion', u'{version}'),
                ],
            )
        ]),
        VarFileInfo([
            VarStruct(u'Translation', [1033, 1200])
        ]),
    ],
)
""",
        encoding="utf-8",
    )


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    version = read_constant("APP_VERSION", text)
    author = read_constant("AUTHOR_NAME", text)
    write_version_file(version, author)
    print(f"Building Taktpause {version} with Python {sys.version.split()[0]}")

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed", "--onefile", "--noupx",
        "--collect-data", "sv_ttk",
        "--collect-submodules", "infi.systray",
        "--version-file", str(VERSION_FILE),
        "--icon", str(ICON),
        "--name", "Taktpause",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(BUILD_DIR / "pyinstaller"),
        "--specpath", str(BUILD_DIR),
    ]
    for module in HIDDEN_IMPORTS:
        command += ["--hidden-import", module]
    command.append(str(SOURCE))

    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        return result.returncode
    exe = ROOT / "dist" / "Taktpause.exe"
    if not exe.exists():
        print("PyInstaller finished without producing dist/Taktpause.exe")
        return 1
    print(f"Built {exe} ({exe.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
