import tkinter as tk
from tkinter import colorchooser, messagebox
import json
import os
from PIL import Image, ImageTk, ImageFilter, ImageGrab, ImageDraw
import ctypes
import win32gui, win32api
import threading
import time
import colorsys
import random
import math
from threading import Lock, Event


# github.com/mirbyte


# --- Configuration Management ---
class Config:
    # Performance settings
    DETECTION_INTERVAL = 2.0  # seconds
    ANIMATION_FPS = 30
    TRANSITION_DURATION = 1.0
    
    # Color detection settings
    COLOR_CHANGE_THRESHOLD = 30
    GRADIENT_THRESHOLD = 60
    SAMPLE_SIZE = 12
    SAMPLE_MARGIN = 12
    
    # UI settings
    MIN_BLOCK_SIZE = 20
    MAX_BLOCK_WIDTH = 4000
    MAX_BLOCK_HEIGHT = 3000
    
    # File settings
    CONFIG_FILE = "streamblock_layout.json"

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
        return 1920, 1080

def get_contrasting_color(bg_color):
    """Get contrasting color for text visibility"""
    if not bg_color or not bg_color.startswith('#'):
        return "#FFFFFF"
    
    bg_color = bg_color[1:]
    try:
        if len(bg_color) != 6:
            return "#FFFFFF"
        
        r, g, b = int(bg_color[0:2], 16), int(bg_color[2:4], 16), int(bg_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#000000" if luminance > 0.5 else "#FFFFFF"
    except (ValueError, IndexError):
        return "#FFFFFF"

def analyze_single_pixel_area(image):
    """Fast single pixel color analysis with validation"""
    try:
        if not image or image.size[0] == 0 or image.size[1] == 0:
            return "#808080"
        
        w, h = image.size
        center_pixel = image.getpixel((w//2, h//2))
        r, g, b = center_pixel[:3]
        
        # Light quantization for stability
        r = max(0, min(255, (r // 16) * 16))
        g = max(0, min(255, (g // 16) * 16))
        b = max(0, min(255, (b // 16) * 16))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#808080"

def color_distance_fast(color1, color2):
    """Fast color distance with validation"""
    try:
        if not color1 or not color2 or len(color1) < 7 or len(color2) < 7:
            return 0
        
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        return abs(r1-r2) + abs(g1-g2) + abs(b1-b2)
    except (ValueError, IndexError):
        return 0

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple with validation"""
    try:
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        if len(hex_color) != 6:
            return (128, 128, 128)
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    except (ValueError, IndexError):
        return (128, 128, 128)

def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color with validation"""
    try:
        r, g, b = max(0, min(255, int(rgb[0]))), max(0, min(255, int(rgb[1]))), max(0, min(255, int(rgb[2])))
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, TypeError, IndexError):
        return "#808080"

def interpolate_color(color1, color2, factor):
    """Smoothly interpolate between two colors (factor 0.0 to 1.0)"""
    try:
        factor = max(0.0, min(1.0, factor))
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        r = int(rgb1[0] * (1 - factor) + rgb2[0] * factor)
        g = int(rgb1[1] * (1 - factor) + rgb2[1] * factor)
        b = int(rgb1[2] * (1 - factor) + rgb2[2] * factor)
        
        return rgb_to_hex((r, g, b))
    except Exception:
        return color1 if color1 else "#808080"

def should_use_gradient(colors):
    """Determine if gradient should be used based on 8-point analysis"""
    try:
        directions = ['top_left', 'top', 'top_right', 'left', 'right', 'bottom_left', 'bottom', 'bottom_right']
        max_diff = 0
        
        for i, dir1 in enumerate(directions):
            for dir2 in directions[i+1:]:
                diff = color_distance_fast(colors.get(dir1, '#808080'), colors.get(dir2, '#808080'))
                max_diff = max(max_diff, diff)
        
        return max_diff > Config.GRADIENT_THRESHOLD
    except Exception:
        return False

def create_advanced_gradient(width, height, colors):
    """Create sophisticated multi-point gradient with error handling"""
    try:
        if width <= 0 or height <= 0:
            return Image.new('RGB', (1, 1), hex_to_rgb('#808080'))
        
        img = Image.new('RGB', (width, height))
        pixels = []
        
        # Convert all colors to RGB with validation
        color_points = {}
        for direction in ['top_left', 'top', 'top_right', 'left', 'right', 'bottom_left', 'bottom', 'bottom_right']:
            color_points[direction] = hex_to_rgb(colors.get(direction, '#808080'))
        
        # Fixed division by zero issue
        w_1 = max(1, width - 1) if width > 1 else 1
        h_1 = max(1, height - 1) if height > 1 else 1
        
        for y in range(height):
            for x in range(width):
                # Handle single pixel case
                if width == 1:
                    x_norm = 0.0
                else:
                    x_norm = x / w_1
                
                if height == 1:
                    y_norm = 0.0
                else:
                    y_norm = y / h_1
                
                # Ensure normalization is within bounds
                x_norm = max(0.0, min(1.0, x_norm))
                y_norm = max(0.0, min(1.0, y_norm))
                
                # Simplified bilinear interpolation
                top_color = interpolate_3_points(
                    color_points['top_left'], color_points['top'], color_points['top_right'], x_norm
                )
                
                bottom_color = interpolate_3_points(
                    color_points['bottom_left'], color_points['bottom'], color_points['bottom_right'], x_norm
                )
                
                final_color = interpolate_rgb_tuple(top_color, bottom_color, y_norm)
                pixels.append(final_color)
        
        img.putdata(pixels)
        return img
    except Exception as e:
        print(f"Gradient creation error: {e}")
        return Image.new('RGB', (max(1, width), max(1, height)), hex_to_rgb('#808080'))

def interpolate_3_points(color1, color2, color3, factor):
    """Interpolate between 3 colors using factor 0.0 to 1.0"""
    try:
        factor = max(0.0, min(1.0, factor))
        if factor <= 0.5:
            local_factor = factor * 2
            return interpolate_rgb_tuple(color1, color2, local_factor)
        else:
            local_factor = (factor - 0.5) * 2
            return interpolate_rgb_tuple(color2, color3, local_factor)
    except Exception:
        return color1

def interpolate_rgb_tuple(rgb1, rgb2, factor):
    """Interpolate between two RGB tuples with validation"""
    try:
        factor = max(0.0, min(1.0, factor))
        r = int(rgb1[0] * (1 - factor) + rgb2[0] * factor)
        g = int(rgb1[1] * (1 - factor) + rgb2[1] * factor)
        b = int(rgb1[2] * (1 - factor) + rgb2[2] * factor)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    except Exception:
        return rgb1 if rgb1 else (128, 128, 128)

class BlackBlock(tk.Toplevel):
    def __init__(self, master, x, y, w, h, color="#000000", is_dynamic=False):
        super().__init__(master)
        
        # Initialize critical attributes FIRST
        self._is_destroyed = False
        self._detection_thread = None
        self._animation_thread = None
        
        # Thread safety
        self._lock = Lock()
        self._stop_event = Event()
        
        # Validate and set initial properties
        self.base_color = color if color and color.startswith('#') else "#000000"
        self.current_color = self.base_color
        self.is_dynamic = is_dynamic
        
        # 8-point color detection system
        self.current_colors = {
            'top_left': '#808080', 'top': '#808080', 'top_right': '#808080',
            'left': '#808080', 'right': '#808080',
            'bottom_left': '#808080', 'bottom': '#808080', 'bottom_right': '#808080'
        }
        self.target_colors = self.current_colors.copy()
        self.should_gradient = False
        self.target_gradient = False
        self.last_printed_color = ""
        self.gradient_photo = None
        
        # Animation state
        self.transition_start_time = 0
        self.transition_duration = Config.TRANSITION_DURATION
        self.is_transitioning = False
        
        # Validate dimensions and position
        w = max(Config.MIN_BLOCK_SIZE, min(w, Config.MAX_BLOCK_WIDTH))
        h = max(Config.MIN_BLOCK_SIZE, min(h, Config.MAX_BLOCK_HEIGHT))
        sw, sh = get_screen_size()
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h))
        
        # Drag & resize state
        self._drag_data = {"x": 0, "y": 0, "action": None}
        
        try:
            # Setup window
            self.overrideredirect(True)
            self.attributes("-topmost", True)
            self.config(bg=self.current_color)
            self.geometry(f"{w}x{h}+{x}+{y}")
            
            self.canvas = tk.Canvas(self, width=w, height=h, highlightthickness=0, bg=self.current_color)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            self.draw_block(w, h)
            
            # Mouse bindings
            self.canvas.bind("<Button-1>", self.start_drag)
            self.canvas.bind("<B1-Motion>", self.do_drag)
            self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
            self.canvas.bind("<Button-3>", self.start_resize)
            self.canvas.bind("<B3-Motion>", self.do_resize)
            self.canvas.bind("<ButtonRelease-3>", self.stop_resize)
            self.canvas.bind("<Double-Button-1>", self.delete_block)
            self.canvas.bind("<Button-2>", self.change_color)
            
            # Start dynamic color if enabled
            if self.is_dynamic:
                self.start_dynamic_color()
                
        except Exception as e:
            print(f"Block initialization error: {e}")
            self._is_destroyed = True
            raise

    def start_dynamic_color(self):
        """Start both detection and animation threads with improved safety"""
        with self._lock:
            if self._detection_thread and self._detection_thread.is_alive():
                return
            
            self._stop_event.clear()
            
            # Detection thread
            self._detection_thread = threading.Thread(target=self._color_detection_loop, daemon=True)
            self._detection_thread.start()
            
            # Animation thread
            self._animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self._animation_thread.start()

    def stop_dynamic_color(self):
        """Stop both threads safely"""
        self._stop_event.set()
        
        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=1.0)
        
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)

    def _color_detection_loop(self):
        """Background thread for optimized 8-point color detection"""
        last_detection_time = 0
        
        while not self._stop_event.is_set() and not self._is_destroyed:
            try:
                current_time = time.time()
                
                # Only detect if enough time has passed
                if current_time - last_detection_time < Config.DETECTION_INTERVAL:
                    time.sleep(0.1)
                    continue
                
                if not self.winfo_exists():
                    break
                
                # Get block position and size with error handling
                try:
                    x, y = self.winfo_x(), self.winfo_y()
                    w, h = self.winfo_width(), self.winfo_height()
                except tk.TclError:
                    break
                
                # Enhanced 8-point sampling system
                margin = Config.SAMPLE_MARGIN
                sample_size = Config.SAMPLE_SIZE
                sw, sh = get_screen_size()
                
                # Define 8 sampling points around the block
                sample_areas = {
                    'top_left': (max(0, x - margin), max(0, y - margin),
                                max(0, x - margin + sample_size), max(0, y - margin + sample_size)),
                    'top_right': (min(sw - sample_size, x + w + margin - sample_size), max(0, y - margin),
                                 min(sw, x + w + margin), max(0, y - margin + sample_size)),
                    'bottom_left': (max(0, x - margin), min(sh - sample_size, y + h + margin - sample_size),
                                   max(0, x - margin + sample_size), min(sh, y + h + margin)),
                    'bottom_right': (min(sw - sample_size, x + w + margin - sample_size),
                                    min(sh - sample_size, y + h + margin - sample_size),
                                    min(sw, x + w + margin), min(sh, y + h + margin)),
                    'top': (max(0, x + w//2 - 6), max(0, y - margin),
                           max(0, x + w//2 + 6), max(0, y - margin + sample_size)),
                    'bottom': (max(0, x + w//2 - 6), min(sh - sample_size, y + h + margin - sample_size),
                              max(0, x + w//2 + 6), min(sh, y + h + margin)),
                    'left': (max(0, x - margin), max(0, y + h//2 - 6),
                            max(0, x - margin + sample_size), max(0, y + h//2 + 6)),
                    'right': (min(sw - sample_size, x + w + margin - sample_size), max(0, y + h//2 - 6),
                             min(sw, x + w + margin), max(0, y + h//2 + 6))
                }
                
                new_colors = {}
                
                # Take screenshots for all 8 points
                for direction, area in sample_areas.items():
                    x1, y1, x2, y2 = area
                    
                    # Skip tiny areas
                    if x2 - x1 < 8 or y2 - y1 < 8:
                        with self._lock:
                            new_colors[direction] = self.target_colors.get(direction, '#808080')
                        continue
                    
                    try:
                        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                        detected_color = analyze_single_pixel_area(screenshot)
                        new_colors[direction] = detected_color
                    except Exception:
                        with self._lock:
                            new_colors[direction] = self.target_colors.get(direction, '#808080')
                
                # Check if colors have changed significantly (thread safety fixed)
                colors_changed = False
                with self._lock:
                    for direction in self.target_colors.keys():
                        old_color = self.target_colors.get(direction, '#808080')
                        new_color = new_colors.get(direction, '#808080')
                        if color_distance_fast(old_color, new_color) > Config.COLOR_CHANGE_THRESHOLD:
                            colors_changed = True
                            break
                
                if colors_changed:
                    self.target_gradient = should_use_gradient(new_colors)
                    mode = "gradient" if self.target_gradient else "solid"
                    
                    # Only print when dominant color changes
                    dominant_color = new_colors.get('top', '#808080')
                    if dominant_color != self.last_printed_color:
                        print(f"🎨 Block adapting: {mode.upper()} mode → {dominant_color}")
                        self.last_printed_color = dominant_color
                    
                    # Start smooth transition to new colors
                    self.start_transition(new_colors)
                
                last_detection_time = current_time
                
            except Exception as e:
                print(f"Detection error: {e}")
                time.sleep(1.0)

    def _animation_loop(self):
        """Background thread for smooth color transitions"""
        while not self._stop_event.is_set() and not self._is_destroyed:
            try:
                if self.is_transitioning:
                    current_time = time.time()
                    elapsed = current_time - self.transition_start_time
                    
                    if elapsed >= self.transition_duration:
                        # Transition complete
                        with self._lock:
                            self.current_colors = self.target_colors.copy()
                            self.should_gradient = self.target_gradient
                            self.is_transitioning = False
                    else:
                        # Calculate transition factor
                        factor = elapsed / self.transition_duration
                        factor = self.ease_in_out(factor)
                        
                        # Interpolate all 8 colors
                        with self._lock:
                            for direction in self.current_colors.keys():
                                current = self.current_colors[direction]
                                target = self.target_colors[direction]
                                self.current_colors[direction] = interpolate_color(current, target, factor)
                    
                    # Update UI
                    if not self._stop_event.is_set():
                        self.after_idle(self._update_animation_ui)
                
                # 30 FPS animation
                time.sleep(1/Config.ANIMATION_FPS)
                
            except Exception as e:
                print(f"Animation error: {e}")
                time.sleep(0.1)

    def ease_in_out(self, t):
        """Smooth easing function for natural transitions"""
        try:
            t = max(0.0, min(1.0, t))
            if t < 0.5:
                return 4 * t * t * t
            else:
                return 1 - pow(-2 * t + 2, 3) / 2
        except Exception:
            return t

    def start_transition(self, new_target_colors):
        """Start a smooth transition to new colors"""
        with self._lock:
            self.target_colors = new_target_colors.copy()
            self.transition_start_time = time.time()
            self.is_transitioning = True

    def _update_animation_ui(self):
        """Update UI during animation (called from main thread)"""
        try:
            if self._is_destroyed:
                return
            
            if not self.winfo_exists():
                return
            
            # Get dimensions safely
            try:
                w, h = self.winfo_width(), self.winfo_height()
            except tk.TclError:
                return
            
            # Ensure minimum size
            if w <= 0 or h <= 0:
                return
            
            with self._lock:
                if self.should_gradient or self.target_gradient:
                    # Create advanced multi-point gradient
                    gradient_img = create_advanced_gradient(w, h, self.current_colors)
                    self.gradient_photo = ImageTk.PhotoImage(gradient_img)
                else:
                    # Only overwrite current_color if dynamic
                    if self.is_dynamic:
                        self.current_color = self.current_colors.get('top', '#808080')
            
            self.draw_block_smooth(w, h)
            
        except tk.TclError:
            pass
        except Exception as e:
            print(f"Animation UI error: {e}")

    def draw_block_smooth(self, w, h):
        """Draw block with smooth transitions"""
        try:
            if self._is_destroyed:
                return
            
            self.canvas.delete("all")
            
            if (self.should_gradient or self.target_gradient) and self.gradient_photo:
                # Draw advanced gradient
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.gradient_photo)
            else:
                # Draw solid color
                self.canvas.create_rectangle(0, 0, w, h, fill=self.current_color, outline=self.current_color)
            
            # Minimal indicator
            if self.is_dynamic and w > 20 and h > 20:
                indicator_text = "D"
                if self.should_gradient or self.target_gradient:
                    if self.is_transitioning:
                        indicator_text += "→"
                
                self.canvas.create_text(5, 5, text=indicator_text,
                                      fill=get_contrasting_color(self.current_color),
                                      font=("Arial", 8, "bold"), anchor="nw")
        except tk.TclError:
            pass

    def draw_block(self, w, h):
        """Regular drawing method"""
        self.draw_block_smooth(w, h)

    def change_color(self, event):
        """Change block color - simplified behavior"""
        try:
            if self.is_dynamic:
                # Dynamic block - do nothing on middle click
                return
            else:
                # Static block - directly open color chooser
                color = colorchooser.askcolor(initialcolor=self.base_color)[1]
                if color and color.startswith('#'):
                    self.base_color = color
                    self.current_color = color
                    self.should_gradient = False
                    self.is_transitioning = False
                    self._update_animation_ui()
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
                'width': max(Config.MIN_BLOCK_SIZE, self.winfo_width()),
                'height': max(Config.MIN_BLOCK_SIZE, self.winfo_height()),
                'color': self.base_color,
                'is_dynamic': self.is_dynamic
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
                w = max(30, min(event.x, Config.MAX_BLOCK_WIDTH))
                h = max(30, min(event.y, Config.MAX_BLOCK_HEIGHT))
                sw, sh = get_screen_size()
                
                # Get current position safely
                try:
                    curr_x, curr_y = self.winfo_x(), self.winfo_y()
                except tk.TclError:
                    return
                
                if curr_x + w > sw:
                    w = sw - curr_x
                if curr_y + h > sh:
                    h = sh - curr_y
                
                # Update geometry first
                self.geometry(f"{w}x{h}+{curr_x}+{curr_y}")
                
                # Then update canvas size
                self.canvas.config(width=w, height=h)
                
                # Update visual after size change
                if self.is_dynamic:
                    self.after_idle(self._update_animation_ui)
                else:
                    self.after_idle(lambda: self.draw_block_smooth(w, h))
                    
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
            self.stop_dynamic_color()
            if self in self.master.blocks:
                self.master.blocks.remove(self)
            self._is_destroyed = True
            self.destroy()
        except (tk.TclError, AttributeError):
            pass

class OverlayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("StreamBlock v0.3 (github.com/mirbyte)")
        self.geometry("700x620")
        self.resizable(True, True)
        self.configure(bg="#FFFFFF")
        
        # Current settings for new blocks
        self.current_color = "#000000"
        self.use_dynamic_color = False
        
        # Config file in working directory
        self.config_file = Config.CONFIG_FILE
        
        # Make main window draggable
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        
        self.setup_ui()
        self.blocks = []
        
        # Periodic cleanup of destroyed blocks
        self.after(5000, self.cleanup_blocks)

    def setup_ui(self):
        # Title
        title = tk.Label(self, text="StreamBlock",
                        font=("Arial", 16, "bold"),
                        bg="#FFFFFF", fg="#000000")
        title.pack(pady=15)
        
        # Instructions
        instructions = tk.Label(self,
                               text="Create draggable colored overlay blocks",
                               font=("Arial", 10),
                               bg="#FFFFFF", fg="#808080")
        instructions.pack(pady=5)
        
        # Color selection frame
        color_frame = tk.Frame(self, bg="#FFFFFF")
        color_frame.pack(pady=15)
        
        tk.Label(color_frame, text="Block Color:",
                font=("Arial", 10), bg="#FFFFFF", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Color preview
        self.color_preview = tk.Label(color_frame, text="   ",
                                     bg=self.current_color, width=4, relief=tk.RAISED)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        
        # Color picker button
        color_btn = tk.Button(color_frame, text="Choose Color",
                             command=self.choose_color,
                             bg="#34495e", fg="white", font=("Arial", 9))
        color_btn.pack(side=tk.LEFT, padx=5)
        
        # Dynamic color mode frame
        dynamic_frame = tk.Frame(self, bg="#FFFFFF")
        dynamic_frame.pack(pady=10)
        
        self.dynamic_var = tk.BooleanVar(value=self.use_dynamic_color)
        dynamic_check = tk.Checkbutton(dynamic_frame, text="Use Dynamic Color",
                                      variable=self.dynamic_var,
                                      command=self.toggle_dynamic_mode,
                                      bg="#FFFFFF", fg="#000000",
                                      font=("Arial", 10))
        dynamic_check.pack(side=tk.LEFT, padx=5)
        
        # Info button for dynamic mode
        info_btn = tk.Button(dynamic_frame, text="?",
                            command=self.show_dynamic_info,
                            bg="#17a2b8", fg="white", font=("Arial", 8, "bold"),
                            width=2, height=1)
        info_btn.pack(side=tk.LEFT, padx=5)
        
        # Add block button
        add_btn = tk.Button(self, text="➕ Add New Block",
                           command=self.add_black_block,
                           bg="#000000", fg="white",
                           font=("Arial", 12, "bold"),
                           relief=tk.RAISED, bd=3,
                           padx=20, pady=10)
        add_btn.pack(pady=20)
        
        # Save/Load buttons
        file_frame = tk.Frame(self, bg="#FFFFFF")
        file_frame.pack(pady=15)
        
        save_btn = tk.Button(file_frame, text="💾 Save Layout",
                            command=self.save_layout,
                            bg="#27ae60", fg="white", font=("Arial", 10))
        save_btn.pack(side=tk.LEFT, padx=10)
        
        load_btn = tk.Button(file_frame, text="📁 Load Layout",
                            command=self.load_layout,
                            bg="#3498db", fg="white", font=("Arial", 10))
        load_btn.pack(side=tk.LEFT, padx=10)
        
        # Controls info
        controls_text = """Controls:
• Left-drag: Move block • Right-drag: Resize block
• Double-click: Delete block • Scrollwheel-click: Change color"""
        
        tk.Label(self, text=controls_text,
                font=("Arial", 9),
                bg="#FFFFFF", fg="#808080",
                justify=tk.LEFT).pack(pady=10)
        
        # Clear all button
        clear_btn = tk.Button(self, text="🗑️ Clear All Blocks",
                             command=self.clear_all_blocks,
                             bg="#95a5a6", fg="white",
                             font=("Arial", 10))
        clear_btn.pack(pady=5)

    def show_dynamic_info(self):
        """Show information about dynamic mode"""
        info_text = """Dynamic Color Mode

• 8 detection points: 4 corners + 4 edges
• Intelligent detection: Only updates when colors actually change
• 2-second detection intervals with 1-second transitions"""
        
        messagebox.showinfo("Dynamic Color Info", info_text)

    def toggle_dynamic_mode(self):
        """Toggle dynamic color mode for new blocks"""
        self.use_dynamic_color = self.dynamic_var.get()
        
        if self.use_dynamic_color:
            # Show CPU warning when enabling dynamic mode
            warning_result = messagebox.askyesno("CPU Usage Warning",
                                               "⚠️ Dynamic color mode uses background processing. "
                                               "v0.3 has optimized performance significantly.\n\n"
                                               "Continue with dynamic mode?")
            if warning_result:
                self.color_preview.config(text="8PT", bg="#4ECDC4")
            else:
                # User chose not to continue, revert the checkbox
                self.dynamic_var.set(False)
                self.use_dynamic_color = False
                self.color_preview.config(text="   ", bg=self.current_color)
        else:
            self.color_preview.config(text="   ", bg=self.current_color)

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
                if not self.use_dynamic_color:
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
            w, h = sw // 8, sh // 15
            x, y = sw // 3, sh // 3
            
            block = BlackBlock(self, x, y, w, h, self.current_color, self.use_dynamic_color)
            self.blocks.append(block)
            
            mode = "8-point dynamic" if self.use_dynamic_color else "static"
            print(f"⬛ Added {mode} block ({self.current_color}) at ({x}, {y}) size {w}x{h}")
            
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
                if block_data:
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
                    if not all(key in block_data for key in ['x', 'y', 'width', 'height']):
                        print(f"Skipping invalid block data: {block_data}")
                        continue
                    
                    block = BlackBlock(
                        self,
                        int(block_data['x']),
                        int(block_data['y']),
                        int(block_data['width']),
                        int(block_data['height']),
                        block_data.get('color', '#000000'),
                        block_data.get('is_dynamic', False)
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
        for block in self.blocks[:]:
            try:
                block.stop_dynamic_color()
                block._is_destroyed = True
                block.destroy()
            except tk.TclError:
                pass
        
        self.blocks.clear()
        print("🗑️ Cleared all blocks")



if __name__ == "__main__":
    app = OverlayApp()
    app.mainloop()


