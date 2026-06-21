"""主窗口"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple, List, Dict

from core.trajectory import TrajectoryGenerator
from core.mouse_control import MouseController
from core.text_to_trajectory import TextToTrajectory
from core.hotkeys import EmergencyStopListener
from gui.overlay import ScreenOverlay


class MainWindow:
    """主窗口类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("鼠标手写签名生成器")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # 初始化组件
        self.trajectory_generator = TrajectoryGenerator()
        self.mouse_controller = MouseController()
        self.text_to_trajectory = TextToTrajectory()
        
        # 状态变量
        self.preview_trajectories: Optional[List[Dict]] = None
        self.selected_region: Optional[Tuple[int, int, int, int]] = None
        self.countdown_active = False
        self.emergency_stop = EmergencyStopListener(self.request_emergency_stop)
        
        # 参数变量
        self.text_var = tk.StringVar(value="张三")
        self.size_var = tk.DoubleVar(value=0.9)
        self.speed_var = tk.DoubleVar(value=1.0)
        # Position jitter is intentionally conservative: independent noise
        # should never make a legible Chinese stroke look corrupted.
        self.jitter_var = tk.DoubleVar(value=0.08)
        self.slant_var = tk.DoubleVar(value=0.0)
        
        # 创建界面
        self.create_widgets()
        self.configure_style()
        
        # 绑定快捷键
        self.root.bind('<Escape>', lambda e: self.cancel_execution())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def configure_style(self):
        """Use an ink-and-paper visual system rather than platform defaults."""
        style = ttk.Style(self.root)
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        self.root.configure(bg='#ece8df')
        style.configure('TFrame', background='#ece8df')
        style.configure('TLabelframe', background='#ece8df', foreground='#1b1b1b')
        style.configure('TLabelframe.Label', background='#ece8df', foreground='#30443a', font=('Georgia', 12, 'bold'))
        style.configure('TLabel', background='#ece8df', foreground='#1b1b1b', font=('Georgia', 11))
        style.configure('TButton', padding=(12, 7), font=('Georgia', 11, 'bold'))
        style.configure('Accent.TButton', background='#30443a', foreground='white')

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="姓名:").grid(row=0, column=0, sticky=tk.W)
        self.text_entry = ttk.Entry(input_frame, textvariable=self.text_var, width=30)
        self.text_entry.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0))
        
        # 参数区域
        params_frame = ttk.LabelFrame(main_frame, text="参数调整", padding="10")
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 大小
        ttk.Label(params_frame, text="大小:").grid(row=0, column=0, sticky=tk.W)
        self.size_scale = ttk.Scale(params_frame, from_=0.5, to=1.0, variable=self.size_var, orient=tk.HORIZONTAL)
        self.size_scale.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0))
        ttk.Label(params_frame, textvariable=self.size_var).grid(row=0, column=2, padx=(5, 0))
        
        # 速度
        ttk.Label(params_frame, text="速度:").grid(row=1, column=0, sticky=tk.W)
        self.speed_scale = ttk.Scale(params_frame, from_=0.5, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        self.speed_scale.grid(row=1, column=1, sticky=tk.EW, padx=(5, 0))
        ttk.Label(params_frame, textvariable=self.speed_var).grid(row=1, column=2, padx=(5, 0))
        
        # 随机扰动
        ttk.Label(params_frame, text="扰动:").grid(row=2, column=0, sticky=tk.W)
        self.jitter_scale = ttk.Scale(params_frame, from_=0.0, to=1.0, variable=self.jitter_var, orient=tk.HORIZONTAL)
        self.jitter_scale.grid(row=2, column=1, sticky=tk.EW, padx=(5, 0))
        ttk.Label(params_frame, textvariable=self.jitter_var).grid(row=2, column=2, padx=(5, 0))
        
        # 倾斜角度
        ttk.Label(params_frame, text="倾斜:").grid(row=3, column=0, sticky=tk.W)
        self.slant_scale = ttk.Scale(params_frame, from_=-30.0, to=30.0, variable=self.slant_var, orient=tk.HORIZONTAL)
        self.slant_scale.grid(row=3, column=1, sticky=tk.EW, padx=(5, 0))
        ttk.Label(params_frame, textvariable=self.slant_var).grid(row=3, column=2, padx=(5, 0))
        
        # 配置网格权重
        params_frame.columnconfigure(1, weight=1)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_frame, bg='#fffdf7', width=500, height=200,
                                        highlightthickness=1, highlightbackground='#c8bfae')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind('<Configure>', lambda event: self.draw_preview())
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.preview_button = ttk.Button(button_frame, text="预览", command=self.preview_signature)
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_region_button = ttk.Button(button_frame, text="选择区域", command=self.select_region)
        self.select_region_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="开始签名", command=self.start_signature,
                                       style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="取消", command=self.cancel_execution, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def preview_signature(self):
        """预览签名"""
        text = self.text_var.get().strip()
        if not text:
            messagebox.showwarning("警告", "请输入姓名")
            return
        
        self.status_var.set("正在生成预览...")
        self.root.update()
        
        # 生成轨迹
        try:
            # text_to_strokes handles Chinese, English, and mixed input.
            strokes = self.text_to_trajectory.text_to_strokes(text)
            
            if not strokes:
                messagebox.showerror("错误", "无法生成轨迹")
                return
            
            # 生成轨迹
            self.preview_trajectories = self.trajectory_generator.generate_signature_trajectory(
                strokes,
                jitter_amount=self.jitter_var.get()
            )

            self.preview_trajectories = self.trajectory_generator.apply_slant(
                self.preview_trajectories, self.slant_var.get()
            )
            
            # 归一化轨迹
            self.preview_trajectories = self.trajectory_generator.normalize_trajectory(
                self.preview_trajectories,
                target_width=900,
                target_height=800
            )
            
            # 绘制预览
            self.draw_preview()
            
            self.status_var.set("预览生成完成")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成预览时出错: {e}")
            self.status_var.set("预览生成失败")

    def draw_preview(self):
        """绘制预览"""
        self.preview_canvas.delete("all")
        
        if not self.preview_trajectories:
            return
        
        canvas_width = max(self.preview_canvas.winfo_width(), 1)
        canvas_height = max(self.preview_canvas.winfo_height(), 1)
        padding = 20
        scale = min((canvas_width - 2 * padding) / 1000, (canvas_height - 2 * padding) / 1000)
        offset_x = (canvas_width - 1000 * scale) / 2
        offset_y = (canvas_height - 1000 * scale) / 2

        for trajectory in self.preview_trajectories:
            points = trajectory['points']
            pen_down = trajectory['pen_down']
            
            if len(points) < 2:
                continue
            
            # 转换坐标
            canvas_points = []
            for point in points:
                x, y = point[0], point[1]
                canvas_x = offset_x + x * scale
                canvas_y = offset_y + y * scale
                canvas_points.append((canvas_x, canvas_y))
            
            # 绘制线条
            if pen_down:
                for i in range(len(canvas_points) - 1):
                    x1, y1 = canvas_points[i]
                    x2, y2 = canvas_points[i + 1]
                    self.preview_canvas.create_line(x1, y1, x2, y2, fill='#1b1b1b', width=2,
                                                    capstyle=tk.ROUND, smooth=True)

    def select_region(self):
        """选择屏幕区域"""
        self.status_var.set("请选择签名区域...")
        self.root.withdraw()  # 隐藏主窗口
        
        # 等待一下再显示覆盖层
        self.root.after(500, self.show_overlay)

    def show_overlay(self):
        """显示覆盖层"""
        def on_region_selected(region: Tuple[int, int, int, int]):
            self.selected_region = region
            self.root.deiconify()  # 显示主窗口
            self.status_var.set(f"已选择区域: {region}")
        
        def on_cancel():
            self.root.deiconify()
            self.status_var.set("已取消选择区域")

        overlay = ScreenOverlay(self.root, on_region_selected, on_cancel)
        overlay.show()

    def start_signature(self):
        """开始签名"""
        if not self.preview_trajectories:
            messagebox.showwarning("警告", "请先预览签名")
            return
        
        if not self.selected_region:
            messagebox.showwarning("警告", "请先选择签名区域")
            return
        
        # 禁用按钮
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.countdown_active = True
        if not self.emergency_stop.start():
            self.status_var.set("macOS 使用屏幕角落紧急停止；倒计时内可按 ESC 取消")
        
        # 开始倒计时
        self.countdown(3)

    def countdown(self, seconds: int):
        """倒计时"""
        if not self.countdown_active:
            return
        if seconds > 0:
            self.status_var.set(f"倒计时: {seconds} 秒")
            self.root.after(1000, lambda: self.countdown(seconds - 1))
        else:
            self.status_var.set("正在执行签名...")
            self.execute_signature()

    def execute_signature(self):
        """执行签名"""
        region = self.selected_region
        
        def on_progress(progress: float):
            self.root.after(0, lambda: self.status_var.set(f"执行进度: {progress * 100:.1f}%"))
        
        def on_complete():
            self.root.after(0, self.on_signature_complete)

        def on_error(message: str):
            self.root.after(0, lambda: self.on_signature_error(message))
        
        # 执行轨迹
        self.mouse_controller.execute_trajectory(
            self.preview_trajectories,
            region,
            scale_factor=self.size_var.get(),
            speed_factor=self.speed_var.get(),
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
        )

    def on_signature_complete(self):
        """签名完成"""
        self.status_var.set("签名完成")
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.emergency_stop.stop()

    def on_signature_error(self, message: str):
        """Restore the interface after a replay failure."""
        self.status_var.set("签名执行失败")
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.emergency_stop.stop()
        messagebox.showerror("签名执行失败", message)

    def cancel_execution(self):
        """取消执行"""
        self.countdown_active = False
        self.mouse_controller.stop()
        self.emergency_stop.stop()
        self.status_var.set("已取消")
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def request_emergency_stop(self):
        """The listener callback runs off the Tk thread."""
        self.root.after(0, self.cancel_execution)

    def on_close(self):
        self.cancel_execution()
        self.root.destroy()

    def run(self):
        """运行主窗口"""
        self.root.mainloop()
