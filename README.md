![StreamBlock_logo_smaller](https://github.com/user-attachments/assets/9ea5b879-a986-4ae7-8f61-460851b8bb62)

# StreamBlock
[![License](https://img.shields.io/github/license/mirbyte/StreamBlock?color=black)](https://raw.githubusercontent.com/mirbyte/StreamBlock/master/LICENSE)
![Size](https://img.shields.io/github/repo-size/mirbyte/StreamBlock?label=size&color=black)
[![Download Count](https://img.shields.io/github/downloads/mirbyte/StreamBlock/total?color=black)](https://github.com/mirbyte/StreamBlock/releases)
[![Latest Release](https://img.shields.io/github/release/mirbyte/StreamBlock.svg?color=black)](https://github.com/mirbyte/StreamBlock/releases/latest)
![LastCommit](https://img.shields.io/github/last-commit/mirbyte/StreamBlock?color=black&label=repo+updated)

A lightweight Python application that creates draggable colored overlay blocks on your screen.

## Download
- **Windows**: Download the package from the **[releases page](https://github.com/mirbyte/StreamBlock/releases/latest)**
- **Others**: Clone this project and run the .py (*you might have to remove the `win32gui` and `win32api` imports, not tested*)

## Features
- **Draggable Blocks**: Create movable colored rectangles anywhere on your screen
- **Resizable**: Easily adjust block dimensions with right-click drag
- **Color Customization**: Choose any color for your blocks
- **Always on Top**: Blocks stay visible over all other applications
- **Save/Load Layouts**: Preserve your block arrangements for future use
- **Real-time Controls**: Modify, move, and delete blocks on the fly

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

![example_twitch](https://github.com/user-attachments/assets/73c708f9-6a21-488b-9972-8ae77bd7d7b9)



![before2](https://github.com/user-attachments/assets/7fa04ad4-20ba-4066-ac16-6b5ef5820f4c)

![after2](https://github.com/user-attachments/assets/68c265d7-6bd6-4538-a8e9-4b51ce0aa386)

