"""平台相关工具"""

import sys
import platform
from typing import Tuple


def check_platform_requirements() -> Tuple[bool, str]:
    """
    检查平台要求
    
    Returns:
        (是否满足要求, 提示信息)
    """
    system = platform.system()
    
    if system == "Darwin":
        # macOS
        try:
            import pyautogui
            # 检查是否需要辅助功能权限
            try:
                # 尝试获取鼠标位置，如果没有权限会抛出异常
                pyautogui.position()
                return True, "macOS 平台已就绪"
            except Exception:
                return False, (
                    "macOS 需要授予辅助功能权限才能控制鼠标。\n\n"
                    "请前往：系统偏好设置 -> 安全性与隐私 -> 辅助功能\n"
                    "添加并勾选终端或 Python 应用。"
                )
        except ImportError:
            return False, "缺少必要的依赖库，请运行: pip install pyautogui"
    
    elif system == "Windows":
        # Windows
        try:
            import pyautogui
            return True, "Windows 平台已就绪"
        except ImportError:
            return False, "缺少必要的依赖库，请运行: pip install pyautogui"
    
    else:
        return False, f"不支持的操作系统: {system}\n目前仅支持 macOS 和 Windows。"


def get_screen_scaling() -> float:
    """
    获取屏幕缩放比例
    
    Returns:
        缩放比例 (1.0 表示 100%)
    """
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        scaling = root.winfo_fpixels('1i') / 96.0
        root.destroy()
        return scaling
    except Exception:
        return 1.0


def get_screen_size() -> Tuple[int, int]:
    """
    获取屏幕分辨率
    
    Returns:
        (宽度, 高度) 像素
    """
    try:
        import pyautogui
        return pyautogui.size()
    except Exception:
        # 备用方案
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return (width, height)
        except Exception:
            return (1920, 1080)  # 默认分辨率


def get_mouse_position() -> Tuple[int, int]:
    """
    获取当前鼠标位置
    
    Returns:
        (x, y) 坐标
    """
    try:
        import pyautogui
        return pyautogui.position()
    except Exception:
        return (0, 0)