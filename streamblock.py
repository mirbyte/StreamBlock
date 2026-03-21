# github.com/mirbyte

import tkinter as tk
from tkinter import colorchooser, messagebox
import json
import os
from PIL import Image, ImageTk, ImageGrab
import ctypes
# win32api is used for accurate DPI-aware screen metrics on Windows.
# On macOS/Linux it is not available; we fall back to tkinter's measurements.
try:
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
import threading
import time
from threading import Lock, Event

# numpy is used for fast gradient generation; falls back to pure Python if unavailable
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

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

    # Screen size cache duration in seconds
    SCREEN_CACHE_DURATION = 5.0

# --- Theme ---
# Background is intentionally darker than OBS (~#1a1a1a vs OBS ~#282828).
# All other hues are matched to OBS Dark: neutral greys with no blue/purple
# tint, muted desaturated accent blue, pure white primary text.
class Theme:
    BG          = "#1a1a1a"   # main window background (darker than OBS)
    BG_INPUT    = "#2d2d2d"   # input / control background (OBS control bg)
    BORDER      = "#3d3d3d"   # subtle dividers (OBS separator tone)
    ACCENT      = "#4c75c9"   # primary accent (OBS muted blue)
    SUCCESS     = "#2a4a38"   # save button
    SUCCESS_FG  = "#6dbf8e"
    LOAD        = "#243152"   # load button
    LOAD_FG     = "#7aaaf0"
    DANGER      = "#3d2020"   # clear button
    DANGER_FG   = "#d96060"
    FG          = "#ffffff"   # primary text — pure white
    FG_DIM      = "#707070"   # secondary / muted text (OBS disabled tone)
    FG_LABEL    = "#aaaaaa"   # section labels
    DYNAMIC_ON  = "#1e3d2c"
    DYNAMIC_FG  = "#5ab87a"
    BTN_ADD_BG  = "#4c75c9"
    BTN_ADD_FG  = "#ffffff"
    BTN_NEUTRAL = "#2d2d2d"
    BTN_NEUTRAL_FG = "#ffffff"
    FONT_TITLE  = ("Segoe UI", 13, "bold")
    FONT_BTN    = ("Segoe UI", 9)
    FONT_BTN_PRIMARY = ("Segoe UI", 10, "bold")
    FONT_MONO   = ("Consolas", 8)

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

# --- Screen size cache (thread-safe) ---
_screen_size_cache = None
_screen_size_cache_time = 0.0
_screen_size_lock = threading.Lock()

def get_screen_size():
    """Get screen dimensions with thread-safe caching.
    Uses win32api on Windows for DPI-aware metrics; falls back to tkinter on other platforms."""
    global _screen_size_cache, _screen_size_cache_time
    now = time.time()
    with _screen_size_lock:
        if _screen_size_cache and now - _screen_size_cache_time < Config.SCREEN_CACHE_DURATION:
            return _screen_size_cache
        try:
            if HAS_WIN32:
                result = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
            else:
                # tkinter fallback for macOS / Linux
                _tmp = tk.Tk()
                _tmp.withdraw()
                result = _tmp.winfo_screenwidth(), _tmp.winfo_screenheight()
                _tmp.destroy()
        except Exception:
            result = 1920, 1080
        _screen_size_cache = result
        _screen_size_cache_time = now
        return result

def safe_widget_exists(widget):
    """Check if a Tkinter widget still exists without raising TclError"""
    try:
        return widget.winfo_exists()
    except tk.TclError:
        return False

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
    """Create sophisticated multi-point gradient."""
    try:
        if width <= 0 or height <= 0:
            return Image.new('RGB', (1, 1), hex_to_rgb('#808080'))

        directions = ['top_left', 'top', 'top_right', 'bottom_left', 'bottom', 'bottom_right']
        color_points = {d: hex_to_rgb(colors.get(d, '#808080')) for d in directions}

        if HAS_NUMPY:
            return _create_gradient_numpy(width, height, color_points)
        else:
            return _create_gradient_python(width, height, color_points)

    except Exception as e:
        print(f"Gradient creation error: {e}")
        return Image.new('RGB', (max(1, width), max(1, height)), hex_to_rgb('#808080'))

def _create_gradient_numpy(width, height, color_points):
    """Vectorized gradient using numpy (fast path)"""
    x_norm = np.linspace(0.0, 1.0, width, dtype=np.float32)
    y_norm = np.linspace(0.0, 1.0, height, dtype=np.float32)
    X, Y = np.meshgrid(x_norm, y_norm)

    tl = np.array(color_points['top_left'],    dtype=np.float32)
    t  = np.array(color_points['top'],         dtype=np.float32)
    tr = np.array(color_points['top_right'],   dtype=np.float32)
    bl = np.array(color_points['bottom_left'], dtype=np.float32)
    b  = np.array(color_points['bottom'],      dtype=np.float32)
    br = np.array(color_points['bottom_right'],dtype=np.float32)

    x2  = np.clip(X * 2,         0.0, 1.0)[..., np.newaxis]
    x2b = np.clip((X - 0.5) * 2, 0.0, 1.0)[..., np.newaxis]
    left_half = X <= 0.5

    top_row = np.where(left_half[..., np.newaxis],
                       tl * (1 - x2)  + t  * x2,
                       t  * (1 - x2b) + tr * x2b)

    bot_row = np.where(left_half[..., np.newaxis],
                       bl * (1 - x2)  + b  * x2,
                       b  * (1 - x2b) + br * x2b)

    Y3 = Y[..., np.newaxis]
    final = top_row * (1 - Y3) + bot_row * Y3

    img_array = np.clip(final, 0, 255).astype(np.uint8)
    return Image.fromarray(img_array, 'RGB')

def _create_gradient_python(width, height, color_points):
    """Pure Python fallback gradient"""
    img = Image.new('RGB', (width, height))
    pixels = []

    w_1 = max(1, width - 1)
    h_1 = max(1, height - 1)

    for y in range(height):
        y_norm = max(0.0, min(1.0, y / h_1)) if height > 1 else 0.0
        for x in range(width):
            x_norm = max(0.0, min(1.0, x / w_1)) if width > 1 else 0.0

            top_color = interpolate_3_points(
                color_points['top_left'], color_points['top'], color_points['top_right'], x_norm
            )
            bottom_color = interpolate_3_points(
                color_points['bottom_left'], color_points['bottom'], color_points['bottom_right'], x_norm
            )
            pixels.append(interpolate_rgb_tuple(top_color, bottom_color, y_norm))

    img.putdata(pixels)
    return img

def interpolate_3_points(color1, color2, color3, factor):
    """Interpolate between 3 colors using factor 0.0 to 1.0"""
    try:
        factor = max(0.0, min(1.0, factor))
        if factor <= 0.5:
            return interpolate_rgb_tuple(color1, color2, factor * 2)
        else:
            return interpolate_rgb_tuple(color2, color3, (factor - 0.5) * 2)
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

        self._is_destroyed = False
        self._detection_thread = None
        self._animation_thread = None

        self._lock = Lock()
        self._stop_event = Event()
        self._needs_redraw = False

        self.base_color = color if color and color.startswith('#') else "#000000"
        self.current_color = self.base_color
        self.is_dynamic = is_dynamic

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

        self.transition_start_time = 0
        self.transition_duration = Config.TRANSITION_DURATION
        self.is_transitioning = False

        w = max(Config.MIN_BLOCK_SIZE, min(w, Config.MAX_BLOCK_WIDTH))
        h = max(Config.MIN_BLOCK_SIZE, min(h, Config.MAX_BLOCK_HEIGHT))
        sw, sh = get_screen_size()
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h))

        self._drag_data = {"x": 0, "y": 0, "action": None}

        try:
            self.overrideredirect(True)
            self.attributes("-topmost", True)
            self.config(bg=self.current_color)
            self.geometry(f"{w}x{h}+{x}+{y}")

            self.canvas = tk.Canvas(self, width=w, height=h, highlightthickness=0, bg=self.current_color)
            self.canvas.pack(fill=tk.BOTH, expand=True)

            self.draw_block_smooth(w, h, use_gradient=False)

            self.canvas.bind("<Button-1>", self.start_drag)
            self.canvas.bind("<B1-Motion>", self.do_drag)
            self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
            self.canvas.bind("<Button-3>", self.start_resize)
            self.canvas.bind("<B3-Motion>", self.do_resize)
            self.canvas.bind("<ButtonRelease-3>", self.stop_resize)
            self.canvas.bind("<Double-Button-1>", self.delete_block)
            self.canvas.bind("<Button-2>", self.change_color)

            if self.is_dynamic:
                self.start_dynamic_color()
                self.after(33, self._ui_tick)

        except Exception as e:
            print(f"Block initialization error: {e}")
            self._is_destroyed = True
            raise

    def start_dynamic_color(self):
        """Start the color detection and animation background threads."""
        with self._lock:
            if self._detection_thread and self._detection_thread.is_alive():
                return

            self._stop_event.clear()

            self._detection_thread = threading.Thread(target=self._color_detection_loop, daemon=True)
            self._detection_thread.start()

            self._animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self._animation_thread.start()

    def stop_dynamic_color(self):
        """Signal both background threads to stop and wait for them to exit."""
        self._stop_event.set()

        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=1.0)

        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)

    def _color_detection_loop(self):
        """Background thread: samples screen colors at 8 points around the block
        every DETECTION_INTERVAL seconds and triggers a transition when colors change."""

        while not self._stop_event.is_set() and not self._is_destroyed:
            try:
                current_time = time.time()

                if current_time - last_detection_time < Config.DETECTION_INTERVAL:
                    time.sleep(0.1)
                    continue

                if not safe_widget_exists(self):
                    break

                try:
                    x, y = self.winfo_x(), self.winfo_y()
                    w, h = self.winfo_width(), self.winfo_height()
                except tk.TclError:
                    break

                margin = Config.SAMPLE_MARGIN
                sample_size = Config.SAMPLE_SIZE
                sw, sh = get_screen_size()

                sample_areas = {
                    'top_left':     (max(0, x - margin),                                max(0, y - margin),
                                     max(0, x - margin + sample_size),                   max(0, y - margin + sample_size)),
                    'top_right':    (min(sw - sample_size, x + w + margin - sample_size), max(0, y - margin),
                                     min(sw, x + w + margin),                            max(0, y - margin + sample_size)),
                    'bottom_left':  (max(0, x - margin),                                min(sh - sample_size, y + h + margin - sample_size),
                                     max(0, x - margin + sample_size),                   min(sh, y + h + margin)),
                    'bottom_right': (min(sw - sample_size, x + w + margin - sample_size), min(sh - sample_size, y + h + margin - sample_size),
                                     min(sw, x + w + margin),                            min(sh, y + h + margin)),
                    'top':          (max(0, x + w//2 - 6),                              max(0, y - margin),
                                     max(0, x + w//2 + 6),                               max(0, y - margin + sample_size)),
                    'bottom':       (max(0, x + w//2 - 6),                              min(sh - sample_size, y + h + margin - sample_size),
                                     max(0, x + w//2 + 6),                               min(sh, y + h + margin)),
                    'left':         (max(0, x - margin),                                max(0, y + h//2 - 6),
                                     max(0, x - margin + sample_size),                   max(0, y + h//2 + 6)),
                    'right':        (min(sw - sample_size, x + w + margin - sample_size), max(0, y + h//2 - 6),
                                     min(sw, x + w + margin),                            max(0, y + h//2 + 6))
                }

                new_colors = {}
                for direction, area in sample_areas.items():
                    x1, y1, x2, y2 = area
                    if x2 - x1 < 8 or y2 - y1 < 8:
                        with self._lock:
                            new_colors[direction] = self.target_colors.get(direction, '#808080')
                        continue
                    try:
                        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                        new_colors[direction] = analyze_single_pixel_area(screenshot)
                        screenshot.close()
                    except Exception:
                        with self._lock:
                            new_colors[direction] = self.target_colors.get(direction, '#808080')

                colors_changed = False
                with self._lock:
                    for direction in self.target_colors.keys():
                        if color_distance_fast(
                            self.target_colors.get(direction, '#808080'),
                            new_colors.get(direction, '#808080')
                        ) > Config.COLOR_CHANGE_THRESHOLD:
                            colors_changed = True
                            break

                if colors_changed:
                    self.target_gradient = should_use_gradient(new_colors)
                    mode = "gradient" if self.target_gradient else "solid"
                    dominant_color = new_colors.get('top', '#808080')
                    if dominant_color != self.last_printed_color:
                        print(f"Block adapting: {mode.upper()} -> {dominant_color}")
                        self.last_printed_color = dominant_color
                    self.start_transition(new_colors)

                last_detection_time = current_time

            except Exception as e:
                print(f"Detection error: {e}")
                time.sleep(1.0)

    def _animation_loop(self):
        """Background thread: compute interpolated colors. Never calls Tkinter directly."""
        while not self._stop_event.is_set() and not self._is_destroyed:
            try:
                if self.is_transitioning:
                    current_time = time.time()
                    elapsed = current_time - self.transition_start_time

                    with self._lock:
                        if elapsed >= self.transition_duration:
                            self.current_colors = self.target_colors.copy()
                            self.should_gradient = self.target_gradient
                            self.is_transitioning = False
                        else:
                            factor = self.ease_in_out(elapsed / self.transition_duration)
                            for direction in self.current_colors.keys():
                                self.current_colors[direction] = interpolate_color(
                                    self.current_colors[direction],
                                    self.target_colors[direction],
                                    factor
                                )

                    self._needs_redraw = True

                time.sleep(1 / Config.ANIMATION_FPS)

            except Exception as e:
                print(f"Animation error: {e}")
                time.sleep(0.1)

    def _ui_tick(self):
        """Main-thread loop: checks the redraw flag and updates the visual if needed."""
        if self._is_destroyed:
            return
        if not safe_widget_exists(self):
            return

        if self._needs_redraw:
            self._needs_redraw = False
            self._update_animation_ui()

        self.after(33, self._ui_tick)

    def _update_animation_ui(self):
        """Build the current frame and redraw. Always called from the main thread."""
        try:
            if self._is_destroyed or not safe_widget_exists(self):
                return

            try:
                w, h = self.winfo_width(), self.winfo_height()
            except tk.TclError:
                return

            if w <= 0 or h <= 0:
                return

            with self._lock:
                use_gradient = self.should_gradient or self.target_gradient
                colors_snapshot = self.current_colors.copy()
                transitioning = self.is_transitioning

            if use_gradient:
                gradient_img = create_advanced_gradient(w, h, colors_snapshot)
                self.gradient_photo = ImageTk.PhotoImage(gradient_img)
                solid_color = None
            else:
                self.gradient_photo = None
                solid_color = colors_snapshot.get('top', '#808080') if self.is_dynamic else self.current_color
                if self.is_dynamic:
                    self.current_color = solid_color

            self.draw_block_smooth(w, h, use_gradient=use_gradient,
                                   solid_color=solid_color, transitioning=transitioning)

        except tk.TclError:
            pass
        except Exception as e:
            print(f"Animation UI error: {e}")

    def ease_in_out(self, t):
        """Cubic ease-in-out: slow start, fast middle, slow end (t in 0.0..1.0)."""
        try:
            t = max(0.0, min(1.0, t))
            if t < 0.5:
                return 4 * t * t * t
            else:
                return 1 - pow(-2 * t + 2, 3) / 2
        except Exception:
            return t

    def start_transition(self, new_target_colors):
        """Set new target colors and begin a timed transition toward them."""
        with self._lock:
            self.target_colors = new_target_colors.copy()
            self.transition_start_time = time.time()
            self.is_transitioning = True

    def draw_block_smooth(self, w, h, use_gradient=False, solid_color=None, transitioning=False):
        """Draw the block. Takes all display state as parameters."""
        try:
            if self._is_destroyed:
                return

            self.canvas.delete("all")

            if use_gradient and self.gradient_photo:
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.gradient_photo)
            else:
                color = solid_color if solid_color else self.current_color
                self.canvas.create_rectangle(0, 0, w, h, fill=color, outline=color)

            # D = solid dynamic, D+ = gradient, D> = transitioning
            if self.is_dynamic and w > 20 and h > 20:
                indicator_text = ("D>" if transitioning else "D+") if use_gradient else "D"
                self.canvas.create_text(5, 5, text=indicator_text,
                                        fill=get_contrasting_color(solid_color or self.current_color),
                                        font=("Arial", 8, "bold"), anchor="nw")
        except tk.TclError:
            pass

    def get_block_data(self):
        try:
            if self._is_destroyed or not safe_widget_exists(self):
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

                try:
                    curr_x, curr_y = self.winfo_x(), self.winfo_y()
                except tk.TclError:
                    return

                if curr_x + w > sw:
                    w = sw - curr_x
                if curr_y + h > sh:
                    h = sh - curr_y

                self.geometry(f"{w}x{h}+{curr_x}+{curr_y}")
                self.canvas.config(width=w, height=h)

                if self.is_dynamic:
                    self.after_idle(self._update_animation_ui)
                else:
                    self.after_idle(lambda: self.draw_block_smooth(
                        w, h, use_gradient=False, solid_color=self.current_color))

            except tk.TclError:
                pass

    def stop_resize(self, event):
        self._drag_data["action"] = None
        try:
            self.canvas.config(cursor="")
        except tk.TclError:
            pass

    def delete_block(self, event):
        try:
            self.stop_dynamic_color()
            if self in self.master.blocks:
                self.master.blocks.remove(self)
            self._is_destroyed = True
            self.destroy()
        except (tk.TclError, AttributeError):
            pass

    def change_color(self, event):
        try:
            if self.is_dynamic:
                print("Color change skipped: block is in dynamic mode.")
            else:
                color = colorchooser.askcolor(initialcolor=self.base_color)[1]
                if color and color.startswith('#'):
                    self.base_color = color
                    self.current_color = color
                    self.should_gradient = False
                    self.is_transitioning = False
                    w, h = self.winfo_width(), self.winfo_height()
                    self.draw_block_smooth(w, h, use_gradient=False, solid_color=color)
        except (tk.TclError, AttributeError):
            pass


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _section_label(parent, text):
    """Uppercase muted section label, similar to VS Code sidebar headers"""
    tk.Label(parent, text=text.upper(),
             font=("Segoe UI", 7, "bold"),
             bg=Theme.BG, fg=Theme.FG_DIM,
             anchor="w").pack(fill=tk.X, padx=16, pady=(14, 4))

def _divider(parent):
    tk.Frame(parent, bg=Theme.BORDER, height=1).pack(fill=tk.X, padx=0, pady=0)

def _flat_btn(parent, text, command, bg, fg, width=None, padx=10, pady=6):
    kw = dict(text=text, command=command,
              bg=bg, fg=fg,
              font=Theme.FONT_BTN,
              relief=tk.FLAT, bd=0,
              cursor="hand2",
              padx=padx, pady=pady,
              activebackground=bg, activeforeground=fg)
    if width is not None:
        kw["width"] = width
    return tk.Button(parent, **kw)


class OverlayApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("StreamBlock")
        self.resizable(False, False)
        self.configure(bg=Theme.BG)

        self.current_color = "#000000"
        self.use_dynamic_color = False
        self.config_file = Config.CONFIG_FILE
        self.blocks = []

        self._drag_origin = {"x": 0, "y": 0}

        self.setup_ui()

        # Let tkinter measure all widgets, then size the window to fit exactly.
        # Cap to 90% of the physical screen height so it never overflows on
        # small monitors (get_screen_size already applies DPI-aware metrics).
        self.update_idletasks()
        w = 360
        content_h = self.winfo_reqheight()
        _, sh = get_screen_size()
        max_h = int(sh * 0.90)
        h = min(content_h, max_h)
        self.geometry(f"{w}x{h}")

        self.after(5000, self.cleanup_blocks)

    # --- UI construction ---

    def setup_ui(self):
        self._build_titlebar()
        _divider(self)
        self._build_color_section()
        _divider(self)
        self._build_dynamic_section()
        _divider(self)
        self._build_actions()
        _divider(self)
        self._build_layout_section()
        _divider(self)
        self._build_controls_section()

    def _bind_drag_recursive(self, widget):
        """Bind drag handlers to a widget and all its children."""
        widget.bind("<Button-1>", self._drag_start)
        widget.bind("<B1-Motion>", self._drag_move)
        for child in widget.winfo_children():
            self._bind_drag_recursive(child)

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=Theme.BG, cursor="fleur")
        bar.pack(fill=tk.X, padx=0, pady=0)

        tk.Label(bar, text="StreamBlock",
                 font=Theme.FONT_TITLE,
                 bg=Theme.BG, fg=Theme.FG,
                 cursor="fleur").pack(side=tk.LEFT, padx=16, pady=12)

        tk.Label(bar, text="v0.4",
                 font=("Segoe UI", 8),
                 bg=Theme.BG, fg=Theme.FG_DIM,
                 cursor="fleur").pack(side=tk.LEFT, pady=12)

        # Drag handle on the right so there is always a large grabbable area
        tk.Label(bar, text="  \u28FF  ",
                 font=("Segoe UI", 10),
                 bg=Theme.BG, fg=Theme.FG_DIM,
                 cursor="fleur").pack(side=tk.RIGHT, padx=12)

        # Bind drag to the frame and every child (labels eat events by default)
        self._bind_drag_recursive(bar)

    def _build_color_section(self):
        _section_label(self, "Block Color")

        row = tk.Frame(self, bg=Theme.BG)
        row.pack(fill=tk.X, padx=16, pady=(0, 12))

        # Color swatch
        self.color_swatch = tk.Label(row, text="", width=3,
                                     bg=self.current_color,
                                     relief=tk.FLAT)
        self.color_swatch.pack(side=tk.LEFT, ipady=10, padx=(0, 8))

        # Hex label
        self.color_hex_label = tk.Label(row, text=self.current_color.upper(),
                                        font=Theme.FONT_MONO,
                                        bg=Theme.BG_INPUT, fg=Theme.FG,
                                        padx=8, pady=4)
        self.color_hex_label.pack(side=tk.LEFT, padx=(0, 8))

        btn = _flat_btn(row, "Pick Color", self.choose_color,
                        bg=Theme.BTN_NEUTRAL, fg=Theme.FG_LABEL)
        btn.pack(side=tk.LEFT)

    def _build_dynamic_section(self):
        _section_label(self, "Detection Mode")

        row = tk.Frame(self, bg=Theme.BG)
        row.pack(fill=tk.X, padx=16, pady=(0, 12))

        self.dynamic_var = tk.BooleanVar(value=False)
        self._dyn_btn = _flat_btn(row, "Static", self._toggle_dynamic,
                                  bg=Theme.BTN_NEUTRAL, fg=Theme.FG_LABEL, padx=14, pady=6)
        self._dyn_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._dyn_status = tk.Label(row, text="Fixed color",
                                    font=("Segoe UI", 8),
                                    bg=Theme.BG, fg=Theme.FG_DIM)
        self._dyn_status.pack(side=tk.LEFT)

        _flat_btn(row, "?", self._show_dynamic_info,
                  bg=Theme.BG, fg=Theme.FG_DIM,
                  padx=6, pady=4).pack(side=tk.RIGHT)

    def _build_actions(self):
        _section_label(self, "Blocks")

        row = tk.Frame(self, bg=Theme.BG)
        row.pack(fill=tk.X, padx=16, pady=(0, 12))

        add_btn = _flat_btn(row, "+ Add Block", self.add_block,
                            bg=Theme.BTN_ADD_BG, fg=Theme.BTN_ADD_FG,
                            padx=16, pady=8)
        add_btn.configure(font=Theme.FONT_BTN_PRIMARY)
        add_btn.pack(side=tk.LEFT, padx=(0, 8))

        _flat_btn(row, "Clear All", self.clear_all_blocks,
                  bg=Theme.DANGER, fg=Theme.DANGER_FG,
                  padx=12, pady=8).pack(side=tk.LEFT)

    def _build_layout_section(self):
        _section_label(self, "Layout")

        row = tk.Frame(self, bg=Theme.BG)
        row.pack(fill=tk.X, padx=16, pady=(0, 12))

        _flat_btn(row, "Save", self.save_layout,
                  bg=Theme.SUCCESS, fg=Theme.SUCCESS_FG,
                  padx=14, pady=7).pack(side=tk.LEFT, padx=(0, 8))

        _flat_btn(row, "Load", self.load_layout,
                  bg=Theme.LOAD, fg=Theme.LOAD_FG,
                  padx=14, pady=7).pack(side=tk.LEFT)

        self._layout_status = tk.Label(row, text="",
                                       font=("Segoe UI", 8),
                                       bg=Theme.BG, fg=Theme.FG_DIM)
        self._layout_status.pack(side=tk.LEFT, padx=10)

    def _build_controls_section(self):
        _section_label(self, "Controls")

        controls = [
            ("Left-drag",         "Move block"),
            ("Right-drag",        "Resize block"),
            ("Double-click",      "Delete block"),
            ("Middle-click",      "Change color (static)"),
        ]

        panel = tk.Frame(self, bg=Theme.BG)
        panel.pack(fill=tk.X, padx=16, pady=(0, 14))

        for key, desc in controls:
            row = tk.Frame(panel, bg=Theme.BG)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=key,
                     font=("Consolas", 8),
                     bg=Theme.BG_INPUT, fg=Theme.ACCENT,
                     padx=5, pady=2).pack(side=tk.LEFT)

            tk.Label(row, text=desc,
                     font=("Segoe UI", 8),
                     bg=Theme.BG, fg=Theme.FG_DIM).pack(side=tk.LEFT, padx=8)

        # Dynamic indicators legend
        ind_row = tk.Frame(panel, bg=Theme.BG)
        ind_row.pack(fill=tk.X, pady=(8, 0))

        tk.Label(ind_row, text="Block indicators:",
                 font=("Segoe UI", 8),
                 bg=Theme.BG, fg=Theme.FG_DIM).pack(side=tk.LEFT)

        for tag, tip in [("D", "solid"), ("D+", "gradient"), ("D>", "transitioning")]:
            tk.Label(ind_row, text=tag,
                     font=("Consolas", 8),
                     bg=Theme.BG_INPUT, fg=Theme.ACCENT,
                     padx=4, pady=1).pack(side=tk.LEFT, padx=(6, 2))
            tk.Label(ind_row, text=tip,
                     font=("Segoe UI", 8),
                     bg=Theme.BG, fg=Theme.FG_DIM).pack(side=tk.LEFT, padx=(0, 4))

    # --- Window dragging (title bar only) ---

    def _drag_start(self, event):
        self._drag_origin["x"] = event.x
        self._drag_origin["y"] = event.y

    def _drag_move(self, event):
        try:
            dx = event.x - self._drag_origin["x"]
            dy = event.y - self._drag_origin["y"]
            self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")
        except tk.TclError:
            pass

    # --- Dynamic mode toggle ---

    def _toggle_dynamic(self):
        if not self.dynamic_var.get():
            confirmed = messagebox.askyesno(
                "CPU Usage Warning",
                "Dynamic color mode uses continuous background processing. "
                "Especially on older CPUs this may affect performance.\n\n"
                "Continue with dynamic mode?"
            )
            if not confirmed:
                return

            self.dynamic_var.set(True)
            self.use_dynamic_color = True
            self._dyn_btn.config(bg=Theme.DYNAMIC_ON, fg=Theme.DYNAMIC_FG, text="Dynamic")
            self._dyn_status.config(text="8-point screen sampling", fg=Theme.DYNAMIC_FG)
            self.color_swatch.config(bg="#4ECDC4")
            self.color_hex_label.config(text="8PT DYNAMIC")
        else:
            self.dynamic_var.set(False)
            self.use_dynamic_color = False
            self._dyn_btn.config(bg=Theme.BTN_NEUTRAL, fg=Theme.FG_LABEL, text="Static")
            self._dyn_status.config(text="Fixed color", fg=Theme.FG_DIM)
            self.color_swatch.config(bg=self.current_color)
            self.color_hex_label.config(text=self.current_color.upper())

    def _show_dynamic_info(self):
        messagebox.showinfo("Dynamic Color Mode",
            "Samples 8 points around each block's edges (4 corners + 4 midpoints) "
            "every 2 seconds and smoothly transitions the block color or gradient "
            "to match the surrounding content."
        )

    # --- Color picker ---

    def choose_color(self):
        try:
            color = colorchooser.askcolor(initialcolor=self.current_color)[1]
            if color and color.startswith('#'):
                self.current_color = color
                if not self.use_dynamic_color:
                    self.color_swatch.config(bg=color)
                    self.color_hex_label.config(text=color.upper())
        except Exception as e:
            print(f"Color selection error: {e}")

    # --- Block management ---

    def add_block(self):
        try:
            sw, sh = get_screen_size()
            w, h = sw // 8, sh // 15
            x, y = sw // 3, sh // 3

            block = BlackBlock(self, x, y, w, h, self.current_color, self.use_dynamic_color)
            self.blocks.append(block)

            mode = "dynamic" if self.use_dynamic_color else "static"
            print(f"Added {mode} block ({self.current_color}) at ({x},{y}) {w}x{h}")

        except Exception as e:
            print(f"Failed to create block: {e}")
            messagebox.showerror("Error", f"Failed to create block: {str(e)}")

    def cleanup_blocks(self):
        self.blocks = [
            b for b in self.blocks
            if not getattr(b, '_is_destroyed', False) and safe_widget_exists(b)
        ]
        self.after(5000, self.cleanup_blocks)

    def save_layout(self):
        if not self.blocks:
            messagebox.showwarning("No Blocks", "There are no blocks to save.")
            return

        try:
            layout_data = [b.get_block_data() for b in self.blocks]
            layout_data = [d for d in layout_data if d]

            if not layout_data:
                messagebox.showwarning("No Blocks", "No valid blocks found.")
                return

            with open(self.config_file, 'w') as f:
                json.dump(layout_data, f, indent=2)

            n = len(layout_data)
            self._layout_status.config(text=f"Saved {n} block{'s' if n != 1 else ''}")
            print(f"Saved {n} blocks to {self.config_file}")

        except Exception as e:
            print(f"Failed to save: {e}")
            messagebox.showerror("Save Error", str(e))

    def load_layout(self):
        if not os.path.exists(self.config_file):
            messagebox.showwarning("Not Found", f"{self.config_file} does not exist.")
            return

        try:
            with open(self.config_file, 'r') as f:
                layout_data = json.load(f)

            if not isinstance(layout_data, list):
                raise ValueError("Invalid layout file format")

            self.clear_all_blocks()

            valid_blocks = 0
            for block_data in layout_data:
                try:
                    if not all(k in block_data for k in ['x', 'y', 'width', 'height']):
                        print(f"Skipping invalid block data: {block_data}")
                        continue

                    block = BlackBlock(
                        self,
                        int(block_data['x']), int(block_data['y']),
                        int(block_data['width']), int(block_data['height']),
                        block_data.get('color', '#000000'),
                        block_data.get('is_dynamic', False)
                    )
                    self.blocks.append(block)
                    valid_blocks += 1

                except (ValueError, TypeError, KeyError) as e:
                    print(f"Skipping invalid block: {e}")

            if valid_blocks > 0:
                self._layout_status.config(text=f"Loaded {valid_blocks} block{'s' if valid_blocks != 1 else ''}")
                print(f"Loaded {valid_blocks} blocks from {self.config_file}")
            else:
                messagebox.showwarning("Empty Layout", "No valid blocks in layout file.")

        except Exception as e:
            print(f"Failed to load: {e}")
            messagebox.showerror("Load Error", str(e))

    def clear_all_blocks(self):
        for block in self.blocks[:]:
            try:
                block.stop_dynamic_color()
                block._is_destroyed = True
                block.destroy()
            except tk.TclError:
                pass
        self.blocks.clear()
        self._layout_status.config(text="")
        print("Cleared all blocks")


if __name__ == "__main__":
    app = OverlayApp()
    app.mainloop()
