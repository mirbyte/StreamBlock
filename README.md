# StreamBlock

[![License](https://img.shields.io/github/license/mirbyte/StreamBlock?color=purple)](https://raw.githubusercontent.com/mirbyte/StreamBlock/master/LICENSE)
![Size](https://img.shields.io/github/repo-size/mirbyte/StreamBlock?label=size&color=purple)
[![Download Count](https://img.shields.io/github/downloads/mirbyte/StreamBlock/total?color=purple)](https://github.com/mirbyte/StreamBlock/releases)
[![Latest Release](https://img.shields.io/github/release/mirbyte/StreamBlock.svg?color=purple)](https://github.com/mirbyte/StreamBlock/releases/latest)
![LastCommit](https://img.shields.io/github/last-commit/mirbyte/StreamBlock?color=purple&label=repo+updated)

A lightweight Python application that creates draggable colored overlay blocks on your screen.

## Features
- **Draggable Blocks**: Create movable colored rectangles anywhere on your screen
- **Resizable**: Easily adjust block dimensions with right-click drag
- **Color Customization**: Choose any color for your blocks
- **Always on Top**: Blocks stay visible over all other applications
- **Save/Load Layouts**: Preserve your block arrangements for future use
- **Real-time Controls**: Modify, move, and delete blocks on the fly

## Download
- **Windows**: Download the package from the **[releases page](https://github.com/mirbyte/StreamBlock/releases/latest)**
- **Others**: Clone the project folder and run the .py (*you might have to remove the `win32gui` and `win32api` imports, not tested*)

## Usage
1. **Create blocks**:
    - Choose a color using the "Choose Color" button
    - Click "➕ Add New Block" to create a new overlay

2. **Control blocks**:
    - **Move**: Left-click and drag
    - **Resize**: Right-click and drag from bottom-right
    - **Delete**: Double-click on the block
    - **Change Color**: Middle-click on the block

## Technical Details
- **Framework**: tkinter (Python's standard GUI library)
- **Image Processing**: Pillow (PIL)
- **Windows Integration**: pywin32 for DPI awareness and screen metrics
- **Data Storage**: JSON for layout persistence


## Use Cases
- **Live Streams**: Hide burned-in ads or watermarks during live stream viewing
- **Live Streaming**: Hide personal information, notifications, or sensitive content
- **Screen Recording**: Block out areas you don't want recorded
- **Presentations**: Cover content until ready to reveal
- **Privacy**: Temporarily hide desktop elements during screen sharing

<br>

![StreamBlock_logo_small](https://github.com/user-attachments/assets/817db0da-9c06-4d42-b9cc-019d15fc2542)


