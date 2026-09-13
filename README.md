# MacSucks

Screen region OCR for Windows. Select any area of your screen with a global shortcut, extract text via [LlamaCloud/LlamaParse](https://cloud.llamaindex.ai), and copy it to your clipboard.

Repo: [purple86a/MacSucks](https://github.com/purple86a/MacSucks)

## Features

- Global hotkey screen region capture with snipping-tool-style dim overlay
- LlamaCloud OCR (API key verified before saving, stored encrypted via Windows DPAPI)
- System tray app with settings UI, debug logs, and CPU/RAM usageC
- Run at Windows login (registry startup)
- Auto-update checks on launch, every 2 hours, and manually (with cooldown)
- MSI releases via GitHub Actions

## Requirements

- Windows 10/11
- Python 3.11+ (development)
- [uv](https://docs.astral.sh/uv/)
- LlamaCloud API key (`llx-...`)

## Setup / try before committing

```powershell
cd "c:\Users\Sara\Desktop\per-pro\screenshot app\MacSucks"
uv sync --all-groups
uv run macsucks
```

The app lives in the **system tray** (hidden icons). Right-click the MacSucks icon → **Open Settings**, paste your API key, then use **Capture Region** or the hotkey (`Alt+C` by default).

Quit from the tray menu when you're done testing.

## Configuration

Settings are stored in `%APPDATA%\MacSucks\config.json`. Your API key is stored in the Windows credential vault (not in plain text).

Auto-updates use:

```toml
[tool.macsucks]
update_repo_owner = "purple86a"
update_repo_name = "MacSucks"
```

## Development

```powershell
uv run pytest
uv run bump2version patch
uv run pyinstaller macsucks.spec --noconfirm
```

## Release

Releases build an MSI and publish a GitHub Release.

**From a push (flag in commit message):**

```text
[release]          → patch bump + release
[release:minor]    → minor bump + release
[release:major]    → major bump + release
```

Example:

```powershell
git commit -m "Polish toasts and installer [release]"
git push
```

**Manual:** GitHub Actions → **Release** → Run workflow (`release=true`, choose bump).

Ordinary pushes without `[release]` do **not** publish a release.

## Usage

1. Launch MacSucks (system tray)
2. Open Settings and save your LlamaCloud API key
3. Press `Alt+C` (default) or use **Capture Region** from the tray
4. Drag to select a region; text is OCR'd and copied to clipboard

## License

[PolyForm Noncommercial License 1.0.0](LICENSE) — personal / noncommercial use only. Commercial use is not permitted.
