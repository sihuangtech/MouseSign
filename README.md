# MouseSign

[简体中文](README.zh-CN.md)

MouseSign is a local desktop application that turns a Chinese and/or English name into a pen trajectory, then replays it using real mouse down, move, and up events in a user-selected screen region.

It is designed for testing signing workflows in local applications, PDF viewers, drawing canvases, and web signature controls. It does not upload screen content, keystrokes, or signatures.

## Features

- Chinese, English, and mixed-name input.
- Signature preview before mouse automation begins.
- Multi-display region picker: select a drawing region on the monitor that
  contains the signature field, with coordinate clamping at replay time.
- Adjustable size, speed, jitter, and slant.
- Per-point timing based on local curvature.
- Three-second countdown before replay.
- Global Escape cancellation on Windows, plus PyAutoGUI corner fail-safe on all
  supported systems.
- macOS Quartz, Windows Win32, and PyAutoGUI fallback mouse backends.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- macOS or Windows for actual mouse replay

## Install and run

```bash
cd MouseSign
uv sync
./run.sh
```

Alternatively, run `uv run python main.py`.

## Usage

1. Enter a name.
2. Adjust size, speed, jitter, and slant.
3. Select **Preview**.
4. Select **Choose region** and drag the exact rectangle that may receive mouse events.
5. Select **Start signing**, then switch to the target application during the countdown.
6. On Windows, press **Esc** to stop at any time. On macOS, cancel during the
   countdown with **Esc**, or move the cursor to a primary-monitor corner while
   replaying to invoke the PyAutoGUI fail-safe.

## Data sources and current scope

- English is rendered from the bundled Hershey single-line font data in `fonts/hersheytext.json`.
- Chinese uses [animCJK](https://github.com/parsimonhi/animCJK) stroke-order centre lines. Cached SVG files are read from `fonts/svgsZhHans`; an uncached character is downloaded and cached on first use.
- animCJK provides standard stroke order, not genuine online handwriting samples. It yields legible Chinese writing but not a consistent human signature style.
- CASIA-style online handwriting samples are not bundled. A legally obtained handwriting dataset is required before this application can provide authentic Chinese writer styles.

Always test in a disposable drawing surface before using a real signature workflow.

## macOS permissions

Grant the terminal or Python application both of the following permissions in **System Settings → Privacy & Security**:

- **Accessibility**, to emit mouse events.

> macOS global Escape monitoring is intentionally disabled because the current
> `pynput` listener can cause a native macOS crash. The corner fail-safe remains
> available during replay.

## Development

```bash
uv run python -m unittest discover -s tests -v
```

## Project layout

```text
core/       trajectory generation, text conversion, mouse replay, emergency stop
fonts/      bundled Hershey data and cached Chinese SVG paths
gui/        Tkinter application window and region-selection overlay
tests/      deterministic core regression tests
```
