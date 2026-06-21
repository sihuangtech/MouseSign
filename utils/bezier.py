"""贝塞尔曲线工具"""

import numpy as np
from typing import List, Tuple


class BezierCurve:
    """贝塞尔曲线类"""

    @staticmethod
    def cubic_bezier(t: float, p0: Tuple[float, float], p1: Tuple[float, float],
                     p2: Tuple[float, float], p3: Tuple[float, float]) -> Tuple[float, float]:
        """
        计算三次贝塞尔曲线上的点
        
        Args:
            t: 参数 t ∈ [0, 1]
            p0, p1, p2, p3: 控制点
            
        Returns:
            曲线上的点坐标 (x, y)
        """
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt

        x = mt3 * p0[0] + 3 * mt2 * t * p1[0] + 3 * mt * t2 * p2[0] + t3 * p3[0]
        y = mt3 * p0[1] + 3 * mt2 * t * p1[1] + 3 * mt * t2 * p2[1] + t3 * p3[1]

        return (x, y)

    @staticmethod
    def catmull_rom_spline(t: float, p0: Tuple[float, float], p1: Tuple[float, float],
                           p2: Tuple[float, float], p3: Tuple[float, float],
                           tension: float = 0.5) -> Tuple[float, float]:
        """
        Catmull-Rom 样条曲线
        
        Args:
            t: 参数 t ∈ [0, 1]
            p0, p1, p2, p3: 控制点
            tension: 张力系数，0.5 为标准 Catmull-Rom
            
        Returns:
            曲线上的点坐标 (x, y)
        """
        # Cubic Hermite form of Catmull-Rom.  The previous implementation
        # accidentally gave p2 a non-zero coefficient at t=0, so every
        # segment jumped away from its source point and Chinese strokes became
        # dense zig-zag scribbles.
        t2 = t * t
        t3 = t2 * t
        h00 = 2 * t3 - 3 * t2 + 1
        h10 = t3 - 2 * t2 + t
        h01 = -2 * t3 + 3 * t2
        h11 = t3 - t2

        m1 = (tension * (p2[0] - p0[0]), tension * (p2[1] - p0[1]))
        m2 = (tension * (p3[0] - p1[0]), tension * (p3[1] - p1[1]))
        x = h00 * p1[0] + h10 * m1[0] + h01 * p2[0] + h11 * m2[0]
        y = h00 * p1[1] + h10 * m1[1] + h01 * p2[1] + h11 * m2[1]

        return (x, y)

    @staticmethod
    def interpolate_points(points: List[Tuple[float, float]], 
                          num_points: int = 50,
                          curve_type: str = 'catmull_rom',
                          tension: float = 0.5) -> List[Tuple[float, float]]:
        """
        使用贝塞尔曲线或 Catmull-Rom 样条插值点序列
        
        Args:
            points: 原始控制点列表
            num_points: 每两个控制点之间插值的点数
            curve_type: 曲线类型 ('bezier' 或 'catmull_rom')
            tension: Catmull-Rom 张力系数
            
        Returns:
            插值后的点列表
        """
        if len(points) < 2:
            return points

        if len(points) == 2:
            # 只有两个点，线性插值
            return [
                (points[0][0] + (points[1][0] - points[0][0]) * i / num_points,
                 points[0][1] + (points[1][1] - points[0][1]) * i / num_points)
                for i in range(num_points + 1)
            ]

        result = []

        for i in range(len(points) - 1):
            # 获取四个控制点（对于首尾点进行特殊处理）
            p0 = points[max(0, i - 1)]
            p1 = points[i]
            p2 = points[min(len(points) - 1, i + 1)]
            p3 = points[min(len(points) - 1, i + 2)]

            # 插值
            for j in range(num_points):
                t = j / num_points
                if curve_type == 'bezier':
                    point = BezierCurve.cubic_bezier(t, p0, p1, p2, p3)
                else:
                    point = BezierCurve.catmull_rom_spline(t, p0, p1, p2, p3, tension)
                result.append(point)

        # 添加最后一个点
        result.append(points[-1])

        return result

    @staticmethod
    def smooth_trajectory(points: List[Tuple[float, float]], 
                         window_size: int = 5) -> List[Tuple[float, float]]:
        """
        使用移动平均平滑轨迹
        
        Args:
            points: 原始点列表
            window_size: 窗口大小
            
        Returns:
            平滑后的点列表
        """
        if len(points) < window_size:
            return points

        result = []
        half_window = window_size // 2

        for i in range(len(points)):
            start = max(0, i - half_window)
            end = min(len(points), i + half_window + 1)
            window = points[start:end]

            avg_x = sum(p[0] for p in window) / len(window)
            avg_y = sum(p[1] for p in window) / len(window)
            result.append((avg_x, avg_y))

        return result

    @staticmethod
    def calculate_curvature(points: List[Tuple[float, float]]) -> List[float]:
        """
        计算轨迹上每个点的曲率
        
        Args:
            points: 点列表
            
        Returns:
            曲率列表
        """
        if len(points) < 3:
            return [0.0] * len(points)

        curvatures = [0.0]  # 第一个点曲率为0

        for i in range(1, len(points) - 1):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[i + 1]

            # 计算向量
            v1 = (p1[0] - p0[0], p1[1] - p0[1])
            v2 = (p2[0] - p1[0], p2[1] - p1[1])

            # 计算叉积（用于判断转弯方向）
            cross = v1[0] * v2[1] - v1[1] * v2[0]

            # 计算向量长度
            len1 = np.sqrt(v1[0] ** 2 + v1[1] ** 2)
            len2 = np.sqrt(v2[0] ** 2 + v2[1] ** 2)

            if len1 > 0 and len2 > 0:
                # 使用叉积计算曲率
                curvature = abs(cross) / (len1 * len2)
                curvatures.append(curvature)
            else:
                curvatures.append(0.0)

        curvatures.append(0.0)  # 最后一个点曲率为0

        return curvatures
