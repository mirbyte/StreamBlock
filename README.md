# StreamBlock
[![License](https://gradgen.boris.sh/github/license/mirbyte/StreamBlock?gradient=000000,404040,9146FF)](https://raw.githubusercontent.com/mirbyte/StreamBlock/master/LICENSE)
![Size](https://gradgen.boris.sh/github/repo-size/mirbyte/StreamBlock?label=size&gradient=000000,404040,9146FF)
[![Download Count](https://gradgen.boris.sh/github/downloads/mirbyte/StreamBlock/total?gradient=000000,404040,9146FF)](https://github.com/mirbyte/StreamBlock/releases)
[![Latest Release](https://gradgen.boris.sh/github/release/mirbyte/StreamBlock?gradient=000000,404040,9146FF)](https://github.com/mirbyte/StreamBlock/releases/latest)
![LastCommit](https://gradgen.boris.sh/github/last-commit/mirbyte/StreamBlock?label=repo%20updated&gradient=000000,404040,9146FF)

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


