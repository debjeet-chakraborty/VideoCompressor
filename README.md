# Offline Video Compressor

A local-only web app for compressing large video files without uploading them anywhere. The interface runs in your browser, but the video stays on your computer and is processed by a local Python backend with `ffmpeg`.

![Offline Video Compressor](https://img.shields.io/badge/offline-yes-67ffd2)
![Python](https://img.shields.io/badge/python-3.10%2B-6aa7ff)
![License](https://img.shields.io/badge/license-MIT-ffb35c)

## Features

- Choose a local video file from your computer.
- Choose the exact save destination.
- Compress large videos without browser upload limits.
- Live progress while encoding.
- Runs offline on `127.0.0.1`.
- One-click packaged builds for Windows, macOS, and Linux.

## Download And Run

Download the build for your operating system from the Releases page.

Then double-click:

- Windows: `VideoCompressor.exe`
- macOS: `VideoCompressor.app` if present, otherwise `VideoCompressor`
- Linux: `VideoCompressor`

No Python, ffmpeg, terminal, or internet connection is needed for the packaged app.

## Run From Source

Use this for development or local testing.

```bash
git clone https://github.com/debjeet-chakraborty/VideoCompressor.git
cd VideoCompressor
python3 app.py
```

Open `http://127.0.0.1:8765` if the browser does not open automatically.

Source mode needs `ffmpeg` installed on your system, or a local binary at:

```text
bin/ffmpeg
```

On Windows:

```text
bin/ffmpeg.exe
```

## Build A One-Click App

Build on the same operating system you want to distribute for.

Windows:

```bat
build_windows.bat
```

macOS/Linux:

```bash
chmod +x build_macos_linux.sh
./build_macos_linux.sh
```

Or directly:

```bash
python build_package.py
```

The build script automatically:

- creates a temporary build virtual environment,
- installs PyInstaller,
- downloads a portable ffmpeg binary through `imageio-ffmpeg`,
- bundles the UI, Python runtime, and ffmpeg engine,
- writes the final app into `dist/`.

## Compression Notes

- The app prefers H.265 for better compression.
- If the bundled ffmpeg does not support H.265, it falls back to H.264.
- A 75% reduction is targeted, but some already-compressed videos cannot shrink that much without visible quality loss.
- Use `Smallest file` for stronger compression.

## Privacy

The app is offline-first:

- no uploads,
- no accounts,
- no telemetry,
- no cloud API,
- local server only on `127.0.0.1`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License. See [LICENSE](LICENSE).
