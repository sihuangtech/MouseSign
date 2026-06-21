"""屏幕覆盖层 - 用于选择签名区域"""

import tkinter as tk
from typing import Callable, Tuple, Optional


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
        
        # 状态变量
        self.start_x: Optional[int] = None
        self.start_y: Optional[int] = None
        self.current_x: Optional[int] = None
        self.current_y: Optional[int] = None
        self.is_selecting = False
        
        # 创建覆盖窗口
        self.root = tk.Toplevel(master)
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)  # 半透明
        self.root.configure(bg='gray')
        
        # 绑定事件
        self.root.bind('<ButtonPress-1>', self.on_mouse_down)
        self.root.bind('<B1-Motion>', self.on_mouse_move)
        self.root.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.root.bind('<Escape>', self.on_escape)
        
        # 创建画布
        self.canvas = tk.Canvas(self.root, bg='gray', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 提示文本
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            50,
            text="请拖拽鼠标选择签名区域\n按 ESC 取消",
            fill='white',
            font=('Arial', 20, 'bold')
        )

    def show(self):
        """显示覆盖层"""
        self.root.focus_force()

    def on_mouse_down(self, event):
        """鼠标按下事件"""
        self.start_x = event.x
        self.start_y = event.y
        self.is_selecting = True
        
        # 清除之前的矩形
        self.canvas.delete("selection")

    def on_mouse_move(self, event):
        """鼠标移动事件"""
        if not self.is_selecting:
            return
        
        self.current_x = event.x
        self.current_y = event.y
        
        # 绘制选择矩形
        self.canvas.delete("selection")
        self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.current_x, self.current_y,
            outline='red',
            width=2,
            tags="selection"
        )

    def on_mouse_up(self, event):
        """鼠标释放事件"""
        if not self.is_selecting:
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
        
        # 关闭覆盖层
        self.root.destroy()
        
        # 调用回调函数
        region = (x1, y1, width, height)
        self.on_region_selected(region)

    def on_escape(self, event):
        """ESC 键事件"""
        self.root.destroy()
        if self.on_cancel:
            self.on_cancel()
