#!/usr/bin/env python3
"""
鼠标手写签名生成器
=================
用户输入姓名，程序自动生成手写风格的签名轨迹，并在屏幕上指定区域内用鼠标绘制出来。
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from utils.platform_utils import check_platform_requirements


def main():
    """主函数"""
    # 检查平台要求
    platform_ok, message = check_platform_requirements()
    if not platform_ok:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("平台要求", message)
        return

    # 创建并运行主窗口
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()