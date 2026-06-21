"""文字转轨迹模块"""

import json
import os
import re
import urllib.request
import numpy as np
from typing import List, Dict, Tuple, Optional

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(PROJECT_ROOT, 'fonts')
CACHE_DIR = os.path.join(FONTS_DIR, 'svgsZhHans')

# animCJK GitHub 基础 URL
ANIMCJK_BASE_URL = "https://raw.githubusercontent.com/parsimonhi/animCJK/master/svgsZhHans"


class TextToTrajectory:
    """文字转轨迹类"""

    def __init__(self, font_name: str = 'cursive', allow_download: bool = True):
        self.font_name = font_name
        self.allow_download = allow_download
        self.fonts_data = None
        self.char_map = {}
        self.load_hershey_fonts()

    def load_hershey_fonts(self):
        """加载 Hershey 字体（英文）"""
        font_file = os.path.join(FONTS_DIR, 'hersheytext.json')
        
        if not os.path.exists(font_file):
            print(f"警告: Hershey 字体文件不存在: {font_file}")
            return
        
        try:
            with open(font_file, 'r', encoding='utf-8') as f:
                self.fonts_data = json.load(f)
            
            # 构建字符映射表
            self._build_char_map()
        except Exception as e:
            print(f"加载 Hershey 字体失败: {e}")

    def _build_char_map(self):
        """构建英文字符映射表"""
        if not self.fonts_data:
            return
        
        # 获取指定字体
        font_data = self.fonts_data.get(self.font_name)
        if not font_data:
            font_data = self.fonts_data.get('cursive')
            if not font_data:
                return
        
        chars = font_data.get('chars', [])
        ascii_start = 33
        
        for i, char_data in enumerate(chars):
            char_code = ascii_start + i
            if 33 <= char_code <= 126:
                char = chr(char_code)
                self.char_map[char] = char_data

    def parse_svg_path(self, path_data: str) -> List[Tuple[float, float]]:
        """
        解析 SVG 路径数据为坐标点列表
        
        Args:
            path_data: SVG 路径字符串，如 "M190 302L233 335L296 580"
            
        Returns:
            坐标点列表
        """
        points = []
        
        # 提取所有坐标对
        # 支持 M, L, C 命令
        tokens = re.findall(r'[MLC]\s*[\d\-.,\s]+', path_data)
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            
            cmd = token[0]
            coords_str = token[1:].strip()
            
            # 提取坐标
            coords = re.findall(r'[\-]?\d+(?:\.\d+)?', coords_str)
            
            if cmd in ('M', 'L'):
                # 移动或直线
                for i in range(0, len(coords) - 1, 2):
                    x, y = float(coords[i]), float(coords[i + 1])
                    points.append((x, y))
            
            elif cmd == 'C':
                # 贝塞尔曲线，取起止点
                if len(coords) >= 6:
                    # 控制点1: coords[0:2], 控制点2: coords[2:4], 终点: coords[4:6]
                    x, y = float(coords[4]), float(coords[5])
                    points.append((x, y))
        
        return points

    def download_svg(self, unicode_decimal: int) -> Optional[str]:
        """
        从 animCJK 下载 SVG 文件
        
        Args:
            unicode_decimal: 字符的 Unicode 十进制值
            
        Returns:
            SVG 文件内容，失败返回 None
        """
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        svg_file = os.path.join(CACHE_DIR, f"{unicode_decimal}.svg")
        
        # 检查缓存
        if os.path.exists(svg_file):
            with open(svg_file, 'r', encoding='utf-8') as f:
                return f.read()

        if not self.allow_download:
            return None
        
        # 下载
        url = f"{ANIMCJK_BASE_URL}/{unicode_decimal}.svg"
        try:
            response = urllib.request.urlopen(url, timeout=10)
            content = response.read().decode('utf-8')
            
            # 保存到缓存
            with open(svg_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return content
        except Exception as e:
            print(f"下载 SVG 失败 (U+{unicode_decimal:04X}): {e}")
            return None

    def parse_chinese_svg(self, svg_content: str) -> List[List[Tuple[float, float]]]:
        """
        解析中文字符 SVG，提取中线轨迹
        
        Args:
            svg_content: SVG 文件内容
            
        Returns:
            笔画列表，每个笔画是坐标点列表
        """
        strokes = []
        
        # 找到所有带 clip-path 的 path 元素（中线轨迹）
        # 使用正则表达式，因为 SVG 可能包含 CDATA
        pattern = r'<path[^>]*clip-path="url\([^)]+\)"[^>]*d="([^"]+)"[^>]*/>'
        matches = re.findall(pattern, svg_content)
        
        for d_attr in matches:
            points = self.parse_svg_path(d_attr)
            if points:
                strokes.append(points)
        
        return strokes

    def get_chinese_character_trajectory(self, char: str) -> List[List[Tuple[float, float]]]:
        """
        获取中文字符的轨迹
        
        Args:
            char: 中文字符
            
        Returns:
            笔画列表
        """
        unicode_decimal = ord(char)
        
        # 下载 SVG
        svg_content = self.download_svg(unicode_decimal)
        if not svg_content:
            return []
        
        # 解析 SVG
        return self.parse_chinese_svg(svg_content)

    def parse_english_svg_path(self, path_data: str) -> List[List[Tuple[float, float]]]:
        """
        解析英文 SVG 路径为多个笔画
        
        Args:
            path_data: SVG 路径字符串
            
        Returns:
            笔画列表
        """
        strokes = []
        current_stroke = []
        
        tokens = re.findall(r'[ML]\s*[\d\-.,\s]+', path_data)
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            
            cmd = token[0]
            coords_str = token[1:].strip()
            coords = re.findall(r'[\-]?\d+(?:\.\d+)?', coords_str)
            
            if cmd == 'M':
                if current_stroke:
                    strokes.append(current_stroke)
                    current_stroke = []
                if len(coords) >= 2:
                    x, y = float(coords[0]), float(coords[1])
                    current_stroke.append((x, y))
            
            elif cmd == 'L':
                for i in range(0, len(coords) - 1, 2):
                    x, y = float(coords[i]), float(coords[i + 1])
                    current_stroke.append((x, y))
        
        if current_stroke:
            strokes.append(current_stroke)
        
        return strokes

    def get_english_character_trajectory(self, char: str) -> List[List[Tuple[float, float]]]:
        """
        获取英文字符的轨迹
        
        Args:
            char: 英文字符
            
        Returns:
            笔画列表
        """
        if not self.char_map:
            return []
        
        char_data = self.char_map.get(char)
        if not char_data:
            char_data = self.char_map.get(char.upper())
        if not char_data:
            char_data = self.char_map.get(char.lower())
        if not char_data:
            return []
        
        path_data = char_data.get('d', '')
        if not path_data:
            return []
        
        return self.parse_english_svg_path(path_data)

    def get_char_width(self, char: str, is_chinese: bool = False) -> float:
        """获取字符宽度"""
        if is_chinese:
            return 1024.0  # animCJK 使用 1024x1024 视口
        
        if not self.char_map:
            return 16.0
        
        char_data = self.char_map.get(char)
        if not char_data:
            return 16.0
        
        return float(char_data.get('o', 16))

    def is_chinese(self, char: str) -> bool:
        """判断是否为中文字符"""
        cp = ord(char)
        # CJK 统一汉字范围
        return (0x4E00 <= cp <= 0x9FFF or  # CJK Unified Ideographs
                0x3400 <= cp <= 0x4DBF or  # CJK Unified Ideographs Extension A
                0x20000 <= cp <= 0x2A6DF or  # CJK Unified Ideographs Extension B
                0x2A700 <= cp <= 0x2B73F or  # CJK Unified Ideographs Extension C
                0x2B740 <= cp <= 0x2B81F or  # CJK Unified Ideographs Extension D
                0xF900 <= cp <= 0xFAFF)  # CJK Compatibility Ideographs

    def text_to_strokes(self, text: str, 
                       char_spacing: float = 0.1,
                       connect_threshold: float = 50.0) -> List[List[Tuple[float, float]]]:
        """
        将文本转换为笔画序列
        
        Args:
            text: 输入文本
            char_spacing: 字符间距比例
            connect_threshold: 连笔距离阈值
            
        Returns:
            笔画列表
        """
        all_strokes = []
        current_x = 0.0
        last_end_point = None
        
        for char in text:
            if char == ' ':
                current_x += 100.0
                last_end_point = None
                continue
            
            # 判断是否为中文
            is_zh = self.is_chinese(char)
            
            # 获取字符轨迹
            if is_zh:
                char_strokes = self.get_chinese_character_trajectory(char)
                char_width = 1024.0
            else:
                char_strokes = self.get_english_character_trajectory(char)
                char_width = self.get_char_width(char)
            
            if not char_strokes:
                continue

            char_origin_x = current_x
            
            # 平移字符位置
            translated_strokes = []
            for stroke in char_strokes:
                translated_stroke = []
                for point in stroke:
                    new_x = point[0] + current_x
                    new_y = point[1]
                    translated_stroke.append((new_x, new_y))
                translated_strokes.append(translated_stroke)
            
            # 判断是否连笔
            if last_end_point and translated_strokes:
                first_stroke = translated_strokes[0]
                if first_stroke:
                    first_point = first_stroke[0]
                    distance = np.sqrt(
                        (first_point[0] - last_end_point[0]) ** 2 +
                        (first_point[1] - last_end_point[1]) ** 2
                    )
                    
                    if distance < connect_threshold:
                        if all_strokes:
                            last_stroke = all_strokes[-1]
                            all_strokes[-1] = last_stroke + translated_strokes[0]
                            translated_strokes = translated_strokes[1:]
            
            all_strokes.extend(translated_strokes)
            
            # 更新位置
            current_x += char_width + char_width * char_spacing
            
            # `translated_strokes` may have had its first stroke consumed by a
            # connection above.  Keep the actual final point of the character.
            if char_strokes and char_strokes[-1]:
                last_point = char_strokes[-1][-1]
                last_end_point = (last_point[0] + char_origin_x, last_point[1])
        
        return all_strokes

    def get_text_width(self, text: str) -> float:
        """
        获取文本的总宽度
        
        Args:
            text: 输入文本
            
        Returns:
            总宽度
        """
        total_width = 0.0
        char_spacing = 0.1
        
        for char in text:
            if char == ' ':
                total_width += 100.0
                continue
            
            is_zh = self.is_chinese(char)
            char_width = 1024.0 if is_zh else self.get_char_width(char)
            total_width += char_width + char_width * char_spacing
        
        return total_width
