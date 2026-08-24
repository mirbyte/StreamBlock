![StreamBlock_logo_smaller](https://github.com/user-attachments/assets/9ea5b879-a986-4ae7-8f61-460851b8bb62)

# StreamBlock
[![License](https://img.shields.io/github/license/mirbyte/StreamBlock?color=black)](https://raw.githubusercontent.com/mirbyte/StreamBlock/master/LICENSE)
![Size](https://img.shields.io/github/repo-size/mirbyte/StreamBlock?label=size&color=black)
[![Download Count](https://img.shields.io/github/downloads/mirbyte/StreamBlock/total?color=black)](https://github.com/mirbyte/StreamBlock/releases)
[![Latest Release](https://img.shields.io/github/release/mirbyte/StreamBlock.svg?color=black)](https://github.com/mirbyte/StreamBlock/releases/latest)
![LastCommit](https://img.shields.io/github/last-commit/mirbyte/StreamBlock?color=black&label=repo+updated)

A Python application that creates draggable colored overlay blocks on your screen.

## Download
- **Windows**: Download the package from the **[releases page](https://github.com/mirbyte/StreamBlock/releases/latest)**
- **Others**: Clone this project and run `python streamblock.py` *(non-Windows support is not tested)*

## Features
- **Draggable & Resizable Blocks**: Create movable colored rectangles anywhere on your screen
- **Always on Top**: Blocks stay visible over all other applications
- **Color Customization**: Pick any static color per block
- **Dynamic Color Mode**: Blocks sample 8 surrounding screen points and adapt their color or gradient every 2 seconds
- **Gradient Support**: When surrounding colors differ enough, the block renders a smooth multi-point gradient instead of a flat color
- **Save/Load Layouts**: Preserve your block arrangements for future sessions
- **DPI Aware**: Correct sizing and positioning on 4K and high-DPI displays

## Usage

### Creating blocks
1. Choose a color with the **Pick Color** button, or enable **Dynamic** mode to have the block match its surroundings automatically
2. Click **+ Add Block** to place a new overlay

### Controlling blocks
| Action | Input |
|---|---|
| Move | Left-click drag |
| Resize | Right-click drag (from bottom-right) |
| Delete | Double-click |
| Change color | Middle-click *(static blocks only)* |

### Dynamic block indicators
A small tag in the top-left corner of each dynamic block shows its current state:

| Tag | Meaning |
|---|---|
| `D` | Dynamic mode, solid color |
| `D+` | Dynamic mode, gradient active |
| `D>` | Dynamic mode, transitioning to a gradient |

## Dependencies

| Package | Purpose |
|---|---|
| `tkinter` | GUI framework (Python standard library) |
| `Pillow` | Image processing and gradient rendering |
| `pywin32` *(optional)* | Windows screen metrics; `ctypes` fallback is built in |
| `numpy` *(optional)* | Accelerated gradient computation, strongly recommended for dynamic mode |

Install with:
```
pip install -r requirements.txt
```

## Technical Details
- **Thread model**: Color detection and animation run on background threads; background workers never call Tkinter, and animation redraws are handled by the main-thread `_ui_tick` loop
- **Gradient rendering**: Piecewise 8-point interpolation, vectorized with NumPy when available and falling back to pure Python otherwise
- **Screen sampling**: 12×12px grabs at 8 points around each block's edges every 2 seconds, with 1-second eased transitions between states
- **Layout storage**: JSON

## Use Cases
- **Live Streams**: Hide burned-in ads or watermarks during live stream viewing
- **Live Streaming**: Cover personal information, notifications, or sensitive content
- **Screen Recording**: Block out areas you don't want recorded
- **Presentations**: Cover content until ready to reveal
- **Privacy**: Hide desktop elements during screen sharing

<br>

<img width="453" height="908" alt="gui" src="https://github.com/user-attachments/assets/f75a8bd1-b659-4547-ad78-39eaafebee1b" />

<br>

![example_twitch](https://github.com/user-attachments/assets/73c708f9-6a21-488b-9972-8ae77bd7d7b9)

![before2](https://github.com/user-attachments/assets/7fa04ad4-20ba-4066-ac16-6b5ef5820f4c)

![after2](https://github.com/user-attachments/assets/68c265d7-6bd6-4538-a8e9-4b51ce0aa386)
