# How A Non-Technical Friend Should Run This

Give your friend a packaged app, not this source folder.

## What You Give Them

After packaging, send the app from:

```text
dist/
```

The app contains the browser UI, Python runtime, and ffmpeg engine.

## What They Do

### Windows

1. Double-click `VideoCompressor.exe`.
2. The browser opens automatically.
3. Choose the source video, choose where to save, then click `Compress`.

### macOS

1. Double-click `VideoCompressor.app` if present.
2. If macOS blocks the app, right-click it once and choose `Open`.
3. The browser opens automatically.

### Linux

1. Double-click `VideoCompressor`, or run it from Terminal:

```bash
./VideoCompressor
```

## Important

- Build the package on the same operating system your friend uses.
- The packaged app does not need Python, ffmpeg, internet, or command line on your friend's machine.
- Do not send only the Python source folder to a non-technical user.
