"""屏幕覆盖层 - 用于选择签名区域"""

import tkinter as tk
from typing import Callable, Tuple, Optional

from utils.platform_utils import get_display_bounds


class ScreenOverlay:
    """屏幕覆盖层类"""

    def __init__(self, master: tk.Misc,
                 on_region_selected: Callable[[Tuple[int, int, int, int]], None],
                 on_cancel: Optional[Callable[[], None]] = None):
        """
        初始化覆盖层
        
        Args:
            on_region_selected: 区域选择完成后的回调函数
        """
        self.on_region_selected = on_region_selected
        self.on_cancel = on_cancel
        
        # State.  A drag is intentionally constrained to one display: a
        # signature widget belongs to one window, and this preserves a simple,
        # unambiguous global coordinate rectangle.
        self.start_x: Optional[int] = None
        self.start_y: Optional[int] = None
        self.current_x: Optional[int] = None
        self.current_y: Optional[int] = None
        self.is_selecting = False
        
        self.windows = []
        self.active_window = None
        self._create_overlays(master)

    def _create_overlays(self, master: tk.Misc):
        """Create a translucent selector window on each active display."""
        displays = get_display_bounds()
        for index, (x, y, width, height) in enumerate(displays):
            if width <= 0 or height <= 0:
                continue
            window = tk.Toplevel(master)
            window.overrideredirect(True)
            window.geometry(f"{width}x{height}{x:+d}{y:+d}")
            window.attributes('-topmost', True)
            window.attributes('-alpha', 0.30)
            window.configure(bg='gray')

            canvas = tk.Canvas(window, bg='gray', highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.create_text(
                width // 2, 50,
                text="拖拽选择签名区域 · ESC 取消",
                fill='white', font=('Arial', 18, 'bold')
            )

            for widget in (window, canvas):
                widget.bind('<ButtonPress-1>', lambda event, item=(window, canvas, x, y): self.on_mouse_down(event, item))
                widget.bind('<B1-Motion>', lambda event, item=(window, canvas, x, y): self.on_mouse_move(event, item))
                widget.bind('<ButtonRelease-1>', lambda event, item=(window, canvas, x, y): self.on_mouse_up(event, item))
                widget.bind('<Escape>', self.on_escape)
            self.windows.append((window, canvas, x, y))

    def show(self):
        """显示覆盖层"""
        for window, _, _, _ in self.windows:
            window.deiconify()
            window.lift()
        if self.windows:
            self.windows[0][0].focus_force()

    def on_mouse_down(self, event, item):
        """鼠标按下事件"""
        window, canvas, origin_x, origin_y = item
        self.active_window = item
        self.start_x = event.x
        self.start_y = event.y
        self.is_selecting = True
        
        # 清除之前的矩形
        canvas.delete("selection")

    def on_mouse_move(self, event, item):
        """鼠标移动事件"""
        if not self.is_selecting or item != self.active_window:
            return
        _, canvas, _, _ = item
        
        self.current_x = event.x
        self.current_y = event.y
        
        # 绘制选择矩形
        canvas.delete("selection")
        canvas.create_rectangle(
            self.start_x, self.start_y,
            self.current_x, self.current_y,
            outline='red',
            width=2,
            tags="selection"
        )

    def on_mouse_up(self, event, item):
        """鼠标释放事件"""
        if not self.is_selecting or item != self.active_window:
            return
        
        self.is_selecting = False
        self.current_x = event.x
        self.current_y = event.y
        
        # 确保坐标是左上角和右下角
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        # 检查区域大小
        width = x2 - x1
        height = y2 - y1
        
        if width < 10 or height < 10:
            # 区域太小，忽略
            return
        
        _, _, origin_x, origin_y = item
        self._destroy_overlays()
        
        # Convert local canvas coordinates into virtual-desktop coordinates.
        region = (origin_x + x1, origin_y + y1, width, height)
        self.on_region_selected(region)

    def on_escape(self, event):
        """ESC 键事件"""
        self._destroy_overlays()
        if self.on_cancel:
            self.on_cancel()

    def _destroy_overlays(self):
        for window, _, _, _ in self.windows:
            try:
                window.destroy()
            except tk.TclError:
                pass
        self.windows.clear()
