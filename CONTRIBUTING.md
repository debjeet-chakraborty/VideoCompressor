# Contributing

Thanks for improving Offline Video Compressor.

## Local Development

```bash
python3 app.py
```

Open `http://127.0.0.1:8765`.

For compression tests, install `ffmpeg` locally or put the binary in `bin/`.

## Before Opening A Pull Request

Run:

```bash
python3 -m py_compile app.py build_package.py
```

If you change packaging behavior, also test:

```bash
python3 build_package.py
```

## Scope

- Keep the app fully offline.
- Do not add a cloud upload path.
- Keep large video files out of the repository.
- Prefer standard-library Python unless a dependency is clearly necessary.
