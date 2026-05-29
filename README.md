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

For non-technical users, download a ready build from the GitHub release or workflow artifacts.

Then double-click:

- Windows: `VideoCompressor.exe`
- macOS: `VideoCompressor.app` if present, otherwise `VideoCompressor`
- Linux: `VideoCompressor`

No Python, ffmpeg, terminal, or internet connection is needed for the packaged app.

## Run From Source

Use this if you are a developer or want to test the code directly.

```bash
git clone https://github.com/YOUR_USERNAME/VideoCompressor.git
cd VideoCompressor
python3 app.py
```

Replace `YOUR_USERNAME` with the GitHub account or organization that hosts the repo.

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

## GitHub Releases

This repo includes a GitHub Actions workflow at `.github/workflows/build.yml`.

When you push a tag like:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions builds artifacts for:

- Windows
- macOS
- Linux

You can attach those artifacts to a GitHub Release so users can download without building anything.

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

## Publishing This Repo

See [GITHUB_SETUP.md](GITHUB_SETUP.md).

## License

MIT License. See [LICENSE](LICENSE).
