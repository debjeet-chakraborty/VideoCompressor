from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_VENV = ROOT / ".packager-venv"
BIN_DIR = ROOT / "bin"
APP_NAME = "VideoCompressor"


def venv_python() -> Path:
    if sys.platform.startswith("win"):
        return BUILD_VENV / "Scripts" / "python.exe"
    return BUILD_VENV / "bin" / "python"


def run(args: list[str], **kwargs) -> None:
    subprocess.check_call(args, cwd=ROOT, **kwargs)


def ensure_build_environment() -> Path:
    if not venv_python().exists():
        venv.EnvBuilder(with_pip=True).create(BUILD_VENV)
    python = venv_python()
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--index-url",
            "https://pypi.org/simple",
            "--upgrade",
            "pyinstaller",
            "imageio-ffmpeg",
        ]
    )
    return python


def bundled_ffmpeg_name() -> str:
    return "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"


def ensure_ffmpeg(python: Path) -> None:
    BIN_DIR.mkdir(exist_ok=True)
    destination = BIN_DIR / bundled_ffmpeg_name()
    if destination.exists():
        return

    snippet = "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
    source = subprocess.check_output([str(python), "-c", snippet], text=True).strip()
    shutil.copy2(source, destination)
    if not sys.platform.startswith("win"):
        destination.chmod(destination.stat().st_mode | 0o755)


def pyinstaller_data_arg(source: str, target: str) -> str:
    separator = ";" if sys.platform.startswith("win") else ":"
    return f"{source}{separator}{target}"


def build_app(python: Path) -> None:
    args = [
        str(python),
        "-m",
        "PyInstaller",
        "--name",
        APP_NAME,
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--hidden-import",
        "tkinter",
        "--hidden-import",
        "tkinter.filedialog",
        "--add-data",
        pyinstaller_data_arg("templates", "templates"),
        "--add-data",
        pyinstaller_data_arg("static", "static"),
        "--add-data",
        pyinstaller_data_arg("bin", "bin"),
        "app.py",
    ]
    run(args)


def write_launcher_notes() -> None:
    if sys.platform == "darwin":
        launcher = f"{APP_NAME}.app"
    elif sys.platform.startswith("win"):
        launcher = f"{APP_NAME}.exe"
    else:
        launcher = APP_NAME
    dist_dir = ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    (dist_dir / "START_HERE.txt").write_text(
        "Offline Video Compressor\n"
        "========================\n\n"
        f"Double-click {launcher} to start the app.\n"
        "A browser window will open automatically.\n\n"
        "No Python, ffmpeg, or internet connection is needed on this computer.\n",
        encoding="utf-8",
    )


def main() -> None:
    if os.environ.get("PYINSTALLER_RESET_ENVIRONMENT"):
        os.environ.pop("PYINSTALLER_RESET_ENVIRONMENT", None)
    python = ensure_build_environment()
    ensure_ffmpeg(python)
    build_app(python)
    write_launcher_notes()
    print(f"\nBuilt one-click app in: {ROOT / 'dist'}")


if __name__ == "__main__":
    main()
