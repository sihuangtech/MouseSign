"""鼠标控制器"""

import time
import threading
from typing import List, Dict, Tuple, Optional, Callable
import platform

# 导入平台相关的鼠标控制库
if platform.system() == "Darwin":
    try:
        import pyautogui
        import Quartz
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        import pyautogui
elif platform.system() == "Windows":
    try:
        import pyautogui
        import ctypes
        from ctypes import wintypes
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        import pyautogui
else:
    import pyautogui


class MouseController:
    """鼠标控制器类"""

    def __init__(self):
        self.is_running = False
        self.should_stop = False
        self.current_thread: Optional[threading.Thread] = None
        
        # 平台特定的初始化
        self.system = platform.system()
        self.use_quartz = False
        self.use_win32 = False
        pyautogui.FAILSAFE = True
        # Keep a small per-call pause so users can still trigger the corner
        # fail-safe while a signature is being replayed.
        pyautogui.PAUSE = 0.01
        
        if self.system == "Darwin" and MACOS_AVAILABLE:
            # macOS 使用 Quartz 进行更精细的控制
            self.use_quartz = True
        elif self.system == "Windows" and WINDOWS_AVAILABLE:
            # Windows 使用 ctypes 调用 SendInput
            self.use_win32 = True
        else:
            self.use_quartz = False
            self.use_win32 = False

    def move_to(self, x: int, y: int, duration: float = 0.0):
        """
        移动鼠标到指定位置
        
        Args:
            x, y: 目标坐标
            duration: 移动持续时间（秒）
        """
        # Quartz/Win32 bypass PyAutoGUI's normal movement implementation, so
        # perform its fail-safe check explicitly on every emitted point.
        pyautogui.failSafeCheck()
        if self.use_quartz:
            self._move_to_quartz(x, y, duration)
        elif self.use_win32:
            self._move_to_win32(x, y, duration)
        else:
            self._move_to_pyautogui(x, y, duration)

    def mouse_down(self):
        """按下鼠标左键"""
        if self.use_quartz:
            self._mouse_down_quartz()
        elif self.use_win32:
            self._mouse_down_win32()
        else:
            pyautogui.mouseDown()

    def mouse_up(self):
        """释放鼠标左键"""
        if self.use_quartz:
            self._mouse_up_quartz()
        elif self.use_win32:
            self._mouse_up_win32()
        else:
            pyautogui.mouseUp()

    def execute_trajectory(self, trajectories: List[Dict], 
                         region: Tuple[int, int, int, int],
                         scale_factor: float = 1.0,
                         speed_factor: float = 1.0,
                         on_progress: Optional[Callable] = None,
                         on_complete: Optional[Callable] = None,
                         on_error: Optional[Callable[[str], None]] = None):
        """
        执行轨迹
        
        Args:
            trajectories: 轨迹列表
            region: 目标区域 (x, y, width, height)
            scale_factor: 缩放因子；会限制为 0.1~1.0，确保不越出区域
            speed_factor: 书写速度倍率
            on_progress: 进度回调函数
            on_complete: 完成回调函数
        """
        if self.is_running:
            return

        self.is_running = True
        self.should_stop = False

        def run():
            mouse_is_down = False
            try:
                region_x, region_y, region_w, region_h = region
                if region_w <= 0 or region_h <= 0:
                    raise ValueError("签名区域必须具有正的宽度和高度")

                # Scale around the centre.  Never allow a point outside the
                # region, even when a caller provides an invalid size value.
                safe_scale = min(max(scale_factor, 0.1), 1.0)
                stroke_duration = 1.3 / max(speed_factor, 0.1)

                def to_screen(point):
                    norm_x = min(max(float(point[0]), 0.0), 1000.0)
                    norm_y = min(max(float(point[1]), 0.0), 1000.0)
                    norm_x = 500 + (norm_x - 500) * safe_scale
                    norm_y = 500 + (norm_y - 500) * safe_scale
                    x = round(region_x + norm_x * region_w / 1000)
                    y = round(region_y + norm_y * region_h / 1000)
                    return (
                        min(max(x, region_x), region_x + region_w),
                        min(max(y, region_y), region_y + region_h),
                    )
                
                for traj_idx, traj in enumerate(trajectories):
                    if self.should_stop:
                        break
                    
                    points = traj['points']
                    pen_down = traj['pen_down']
                    
                    if not points:
                        continue
                    
                    # 计算第一个点的绝对坐标
                    first_point = points[0]
                    if len(first_point) >= 2:
                        abs_x, abs_y = to_screen(first_point)
                        
                        # 移动到起始点
                        self.move_to(abs_x, abs_y, duration=0.1)
                        
                        if pen_down:
                            self.mouse_down()
                            mouse_is_down = True
                        
                        # 执行轨迹
                        for point_idx in range(1, len(points)):
                            if self.should_stop:
                                break
                            
                            point = points[point_idx]
                            abs_x, abs_y = to_screen(point)
                            
                            # 计算移动时间（基于时间戳）
                            if len(point) > 2 and len(points[point_idx - 1]) > 2:
                                time_diff = point[2] - points[point_idx - 1][2]
                                move_time = max(time_diff * stroke_duration, 0.003)
                            else:
                                move_time = 0.02  # 默认50fps
                            
                            # 移动鼠标
                            self.move_to(abs_x, abs_y, duration=move_time)
                            
                            # 更新进度
                            if on_progress:
                                progress = (traj_idx + point_idx / len(points)) / len(trajectories)
                                on_progress(progress)
                        
                        if pen_down:
                            self.mouse_up()
                            mouse_is_down = False
                
                if on_complete and not self.should_stop:
                    on_complete()
                    
            except Exception as e:
                message = f"执行轨迹时出错: {e}"
                print(message)
                if on_error:
                    on_error(message)
            finally:
                if mouse_is_down:
                    try:
                        self.mouse_up()
                    except Exception:
                        pass
                self.is_running = False

        self.current_thread = threading.Thread(target=run)
        self.current_thread.daemon = True
        self.current_thread.start()

    def stop(self):
        """停止执行"""
        self.should_stop = True
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=1.0)

    # macOS Quartz 实现
    def _move_to_quartz(self, x: int, y: int, duration: float):
        """使用 Quartz 移动鼠标"""
        if not MACOS_AVAILABLE:
            return self._move_to_pyautogui(x, y, duration)
        
        event = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventMouseMoved,
            (x, y),
            Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        
        if duration > 0:
            time.sleep(duration)

    def _mouse_down_quartz(self):
        """使用 Quartz 按下鼠标"""
        if not MACOS_AVAILABLE:
            return pyautogui.mouseDown()
        
        x, y = pyautogui.position()
        event = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseDown,
            (x, y),
            Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    def _mouse_up_quartz(self):
        """使用 Quartz 释放鼠标"""
        if not MACOS_AVAILABLE:
            return pyautogui.mouseUp()
        
        x, y = pyautogui.position()
        event = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseUp,
            (x, y),
            Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    # Windows 实现
    def _move_to_win32(self, x: int, y: int, duration: float):
        """使用 Windows API 移动鼠标"""
        if not WINDOWS_AVAILABLE:
            return self._move_to_pyautogui(x, y, duration)
        
        # 使用 ctypes 调用 SetCursorPos
        ctypes.windll.user32.SetCursorPos(x, y)
        
        if duration > 0:
            time.sleep(duration)

    def _mouse_down_win32(self):
        """使用 Windows API 按下鼠标"""
        if not WINDOWS_AVAILABLE:
            return pyautogui.mouseDown()
        
        # 使用 SendInput
        MOUSEEVENTF_LEFTDOWN = 0x0002
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    def _mouse_up_win32(self):
        """使用 Windows API 释放鼠标"""
        if not WINDOWS_AVAILABLE:
            return pyautogui.mouseUp()
        
        # 使用 SendInput
        MOUSEEVENTF_LEFTUP = 0x0004
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    # 通用 pyautogui 实现
    def _move_to_pyautogui(self, x: int, y: int, duration: float):
        """使用 pyautogui 移动鼠标"""
        pyautogui.moveTo(x, y, duration=duration)
