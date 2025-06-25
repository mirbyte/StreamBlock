import tkinter as tk
from tkinter import colorchooser, messagebox
import json
import os
from PIL import Image, ImageTk, ImageFilter
import ctypes
import win32gui, win32api


# first release version
# github.com/mirbyte


# --- DPI Awareness ---
try:
    ctypes.windll.shcore.SetProcessDpiAwarenessContext(-2)
except (AttributeError, OSError):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass

def get_screen_size():
    """Get screen dimensions with fallback"""
    try:
        return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    except:
        # Fallback if win32api fails
        return 1920, 1080

class BlackBlock(tk.Toplevel):
    def __init__(self, master, x, y, w, h, color="#000000"):
        super().__init__(master)
        
        # Validate inputs
        self.color = color if color and color.startswith('#') else "#000000"
        
        # Ensure reasonable dimensions
        w = max(20, min(w, 4000))
        h = max(20, min(h, 3000))
        
        # Ensure position is on screen
        sw, sh = get_screen_size()
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h))
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg=self.color)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.canvas = tk.Canvas(self, width=w, height=h, highlightthickness=0, bg=self.color)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_block(w, h)

        # Drag & resize state
        self._drag_data = {"x": 0, "y": 0, "action": None}
        self._is_destroyed = False

        # Mouse bindings
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Button-3>", self.start_resize)
        self.canvas.bind("<B3-Motion>", self.do_resize)
        self.canvas.bind("<ButtonRelease-3>", self.stop_resize)
        self.canvas.bind("<Double-Button-1>", self.delete_block)
        self.canvas.bind("<Button-2>", self.change_color)

    def draw_block(self, w, h):
        """Draw the block with error handling"""
        try:
            self.canvas.delete("all")
            self.canvas.create_rectangle(0, 0, w, h, fill=self.color, outline=self.color)
        except tk.TclError:
            pass

    def change_color(self, event):
        """Change block color with validation"""
        try:
            color = colorchooser.askcolor(initialcolor=self.color)[1]
            if color and color.startswith('#'):
                self.color = color
                self.config(bg=self.color)
                self.canvas.config(bg=self.color)
                self.draw_block(self.winfo_width(), self.winfo_height())
        except (tk.TclError, AttributeError):
            pass

    def get_block_data(self):
        """Return block data for saving with validation"""
        try:
            if self._is_destroyed or not self.winfo_exists():
                return None
            
            return {
                'x': max(0, self.winfo_x()),
                'y': max(0, self.winfo_y()),
                'width': max(20, self.winfo_width()),
                'height': max(15, self.winfo_height()),
                'color': self.color
            }
        except tk.TclError:
            return None

    def start_drag(self, event):
        if not self._is_destroyed:
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
            self._drag_data["action"] = "move"
            try:
                self.canvas.config(cursor="fleur")
            except tk.TclError:
                pass

    def do_drag(self, event):
        if self._drag_data["action"] == "move" and not self._is_destroyed:
            try:
                dx = event.x - self._drag_data["x"]
                dy = event.y - self._drag_data["y"]
                
                # Get screen bounds
                sw, sh = get_screen_size()
                new_x = max(0, min(self.winfo_x() + dx, sw - self.winfo_width()))
                new_y = max(0, min(self.winfo_y() + dy, sh - self.winfo_height()))
                
                self.geometry(f"+{new_x}+{new_y}")
            except tk.TclError:
                pass

    def stop_drag(self, event):
        self._drag_data["action"] = None
        try:
            self.canvas.config(cursor="")
        except tk.TclError:
            pass

    def start_resize(self, event):
        if not self._is_destroyed:
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
            self._drag_data["action"] = "resize"
            try:
                self.canvas.config(cursor="bottom_right_corner")
            except tk.TclError:
                pass

    def do_resize(self, event):
        if self._drag_data["action"] == "resize" and not self._is_destroyed:
            try:
                w = max(30, min(event.x, 4000))
                h = max(30, min(event.y, 3000))
                
                # Ensure doesn't go off screen
                sw, sh = get_screen_size()
                if self.winfo_x() + w > sw:
                    w = sw - self.winfo_x()
                if self.winfo_y() + h > sh:
                    h = sh - self.winfo_y()
                
                self.geometry(f"{w}x{h}+{self.winfo_x()}+{self.winfo_y()}")
                self.canvas.config(width=w, height=h)
                self.draw_block(w, h)
            except tk.TclError:
                pass

    def stop_resize(self, event):
        self._drag_data["action"] = None
        try:
            self.canvas.config(cursor="")
        except tk.TclError:
            pass

    def delete_block(self, event):
        """Safely delete block"""
        try:
            if self in self.master.blocks:
                self.master.blocks.remove(self)
            self._is_destroyed = True
            self.destroy()
        except (tk.TclError, AttributeError):
            pass

class OverlayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("StreamBlock v0.1    (github.com/mirbyte)") # ############################################## TITLE
        self.geometry("700x580")
        self.resizable(True, True)
        self.configure(bg="#2c3e50")

        # Current color for new blocks
        self.current_color = "#000000"
        
        # Config file in working directory
        self.config_file = "streamblock_layout.json"

        # Make main window draggable
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)

        self.setup_ui()
        self.blocks = []
        
        # Periodic cleanup of destroyed blocks
        self.after(5000, self.cleanup_blocks) # Every 5 seconds

    def setup_ui(self):
        # Title
        title = tk.Label(self, text="StreamBlock",
                        font=("Arial", 16, "bold"),
                        bg="#2c3e50", fg="white")
        title.pack(pady=15)

        # Instructions
        instructions = tk.Label(self,
                               text="Create draggable colored blocks to hide content",
                               font=("Arial", 10),
                               bg="#2c3e50", fg="#ecf0f1")
        instructions.pack(pady=5)

        # Color selection frame
        color_frame = tk.Frame(self, bg="#2c3e50")
        color_frame.pack(pady=15)

        tk.Label(color_frame, text="Block Color:",
                font=("Arial", 10), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)

        # Color preview
        self.color_preview = tk.Label(color_frame, text="   ",
                                    bg=self.current_color, width=4, relief=tk.RAISED)
        self.color_preview.pack(side=tk.LEFT, padx=5)

        # Color picker button
        color_btn = tk.Button(color_frame, text="Choose Color",
                            command=self.choose_color,
                            bg="#34495e", fg="white", font=("Arial", 9))
        color_btn.pack(side=tk.LEFT, padx=5)

        # Add block button
        add_btn = tk.Button(self, text="➕ Add New Block",
                           command=self.add_black_block,
                           bg="#000000", fg="white",
                           font=("Arial", 12, "bold"),
                           relief=tk.RAISED, bd=3,
                           padx=20, pady=10)
        add_btn.pack(pady=20)

        # Save/Load buttons
        file_frame = tk.Frame(self, bg="#2c3e50")
        file_frame.pack(pady=15)

        save_btn = tk.Button(file_frame, text="💾 Save Layout",
                           command=self.save_layout,
                           bg="#27ae60", fg="white", font=("Arial", 10))
        save_btn.pack(side=tk.LEFT, padx=10)

        load_btn = tk.Button(file_frame, text="📁 Load Layout",
                           command=self.load_layout,
                           bg="#3498db", fg="white", font=("Arial", 10))
        load_btn.pack(side=tk.LEFT, padx=10)

        # Config file info
        config_info = tk.Label(self, text=f"Config: {self.config_file}",
                              font=("Arial", 8),
                              bg="#2c3e50", fg="#95a5a6")
        config_info.pack(pady=2)

        # Controls info
        controls_text = """Controls:
• Left-drag: Move block  • Right-drag: Resize block
• Double-click: Delete block  • Middle-click: Change color"""

        tk.Label(self, text=controls_text,
                font=("Arial", 9),
                bg="#2c3e50", fg="#bdc3c7",
                justify=tk.LEFT).pack(pady=10)

        # Clear all button
        clear_btn = tk.Button(self, text="🗑️ Clear All Blocks",
                            command=self.clear_all_blocks,
                            bg="#95a5a6", fg="white",
                            font=("Arial", 10))
        clear_btn.pack(pady=5)

    def cleanup_blocks(self):
        """Periodically remove destroyed blocks from list"""
        try:
            self.blocks = [block for block in self.blocks 
                          if not getattr(block, '_is_destroyed', False) and block.winfo_exists()]
        except tk.TclError:
            pass
        
        # Schedule next cleanup
        self.after(5000, self.cleanup_blocks)

    def choose_color(self):
        try:
            color = colorchooser.askcolor(initialcolor=self.current_color)[1]
            if color and color.startswith('#'):
                self.set_color(color)
        except Exception as e:
            print(f"Color selection error: {e}")

    def set_color(self, color):
        if color and color.startswith('#'):
            self.current_color = color
            try:
                self.color_preview.config(bg=color)
            except tk.TclError:
                pass

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        try:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    def add_black_block(self):
        try:
            sw, sh = get_screen_size()
            w, h = sw // 8, sh // 15  # Starting size
            x, y = sw // 3, sh // 3   # Center-ish position

            block = BlackBlock(self, x, y, w, h, self.current_color)
            self.blocks.append(block)
            print(f"⬛ Added {self.current_color} block at ({x}, {y}) size {w}x{h}")
        except Exception as e:
            print(f"Failed to create block: {e}")
            messagebox.showerror("Error", f"Failed to create block: {str(e)}")

    def save_layout(self):
        if not self.blocks:
            messagebox.showwarning("Warning", "No blocks to save!")
            return

        try:
            layout_data = []
            for block in self.blocks:
                block_data = block.get_block_data()
                if block_data: # Only add valid data
                    layout_data.append(block_data)

            if not layout_data:
                messagebox.showwarning("Warning", "No valid blocks to save!")
                return

            with open(self.config_file, 'w') as f:
                json.dump(layout_data, f, indent=2)

            messagebox.showinfo("Success", f"Layout saved!\n{len(layout_data)} blocks saved to {self.config_file}")
            print(f"💾 Saved {len(layout_data)} blocks to {self.config_file}")

        except Exception as e:
            error_msg = f"Failed to save: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)

    def load_layout(self):
        if not os.path.exists(self.config_file):
            messagebox.showwarning("Warning", f"No saved layout found!\n{self.config_file} doesn't exist.")
            return

        try:
            with open(self.config_file, 'r') as f:
                layout_data = json.load(f)

            if not isinstance(layout_data, list):
                raise ValueError("Invalid layout file format")

            # Clear existing blocks
            self.clear_all_blocks()

            # Create blocks from saved data
            valid_blocks = 0
            for block_data in layout_data:
                try:
                    # Validate block data
                    if not all(key in block_data for key in ['x', 'y', 'width', 'height']):
                        print(f"Skipping invalid block data: {block_data}")
                        continue

                    block = BlackBlock(
                        self,
                        int(block_data['x']),
                        int(block_data['y']),
                        int(block_data['width']),
                        int(block_data['height']),
                        block_data.get('color', '#000000')
                    )
                    self.blocks.append(block)
                    valid_blocks += 1
                    
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Skipping invalid block: {e}")
                    continue

            if valid_blocks > 0:
                messagebox.showinfo("Success", f"Layout loaded!\n{valid_blocks} blocks loaded from {self.config_file}")
                print(f"📁 Loaded {valid_blocks} blocks from {self.config_file}")
            else:
                messagebox.showwarning("Warning", "No valid blocks found in layout file!")

        except Exception as e:
            error_msg = f"Failed to load: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)

    def clear_all_blocks(self):
        for block in self.blocks[:]: # Copy list to avoid modification during iteration
            try:
                block._is_destroyed = True
                block.destroy()
            except tk.TclError:
                pass
        self.blocks.clear()
        print("🗑️ Cleared all blocks")




if __name__ == "__main__":
    app = OverlayApp()
    app.mainloop()

