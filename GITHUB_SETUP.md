# GitHub Upload Guide

Use these steps from inside this project folder.

## First Upload

```bash
git init
git add .
git commit -m "Initial open-source release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/VideoCompressor.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Create A Release Build

Push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will build Windows, macOS, and Linux artifacts.

After the workflow finishes:

1. Open your GitHub repo.
2. Go to `Actions`.
3. Open the completed `Build Desktop Apps` run.
4. Download the artifacts.
5. Create a GitHub Release and attach those files.

## What Users Should Download

Tell users to download the release for their operating system:

- Windows users: `VideoCompressor-Windows`
- macOS users: `VideoCompressor-macOS`
- Linux users: `VideoCompressor-Linux`

They should extract the downloaded zip and double-click the app.
