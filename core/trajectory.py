"""轨迹生成器"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from utils.bezier import BezierCurve


class TrajectoryGenerator:
    """轨迹生成器类"""

    def __init__(self):
        self.bezier = BezierCurve()

    def generate_stroke_trajectory(self, stroke_points: List[Tuple[float, float]],
                                  pen_down: bool = True,
                                  num_interpolations: int = 10,
                                  jitter_amount: float = 0.0) -> Dict:
        """
        生成单个笔画的轨迹
        
        Args:
            stroke_points: 笔画关键点列表
            pen_down: 是否落笔
            num_interpolations: 每两个关键点之间的插值点数
            jitter_amount: 随机扰动幅度 (0.0 - 1.0)
            
        Returns:
            笔画轨迹字典
        """
        if len(stroke_points) < 2:
            return {
                'stroke_id': 0,
                'points': [list(p) for p in stroke_points],
                'pen_down': pen_down
            }

        # 使用贝塞尔曲线插值
        interpolated = self.bezier.interpolate_points(
            stroke_points, 
            num_points=num_interpolations,
            curve_type='catmull_rom',
            tension=0.5
        )

        # 平滑处理
        smoothed = self.bezier.smooth_trajectory(interpolated, window_size=3)

        # 添加随机扰动
        if jitter_amount > 0:
            smoothed = self.add_jitter(smoothed, jitter_amount)

        # 计算时间戳（基于曲率的速度）
        points_with_time = self.add_time_stamps(smoothed)

        return {
            'stroke_id': 0,
            'points': points_with_time,
            'pen_down': pen_down
        }

    def add_jitter(self, points: List[Tuple[float, float]], 
                  amount: float) -> List[Tuple[float, float]]:
        """
        添加随机扰动
        
        Args:
            points: 原始点列表
            amount: 扰动幅度 (0.0 - 1.0)
            
        Returns:
            添加扰动后的点列表
        """
        if amount <= 0:
            return points

        # 计算轨迹的整体尺度
        if len(points) < 2:
            return points

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        scale = max(max(xs) - min(xs), max(ys) - min(ys))
        
        if scale == 0:
            return points

        # 计算扰动标准差
        jitter_std = scale * amount * 0.02  # 2% 的尺度

        result = []
        for x, y in points:
            jitter_x = np.random.normal(0, jitter_std)
            jitter_y = np.random.normal(0, jitter_std)
            result.append((x + jitter_x, y + jitter_y))

        return result

    def add_time_stamps(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
        """
        添加时间戳（基于曲率的速度）
        
        Args:
            points: 点列表
            
        Returns:
            带时间戳的点列表 [(x, y, t), ...]
        """
        if len(points) < 2:
            return [(p[0], p[1], 0.0) for p in points]

        # 计算曲率
        curvatures = self.bezier.calculate_curvature(points)

        # 计算每段距离
        distances = []
        for i in range(len(points) - 1):
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            dist = np.sqrt(dx * dx + dy * dy)
            distances.append(dist)

        # 基于曲率计算速度（曲率越大，速度越慢）
        speeds = []
        base_speed = 1.0
        for i in range(len(points)):
            curvature = curvatures[i]
            # 速度与曲率成反比，但设置最小速度
            speed = base_speed / (1.0 + curvature * 10)
            speeds.append(speed)

        # 计算时间戳
        timestamps = [0.0]
        current_time = 0.0
        for i in range(len(points) - 1):
            avg_speed = (speeds[i] + speeds[i + 1]) / 2
            if avg_speed > 0:
                time_delta = distances[i] / avg_speed
            else:
                time_delta = 1.0
            current_time += time_delta
            timestamps.append(current_time)

        # 归一化时间到 [0, 1]
        if timestamps[-1] > 0:
            timestamps = [t / timestamps[-1] for t in timestamps]

        # 组合结果
        result = []
        for i, (x, y) in enumerate(points):
            result.append((x, y, timestamps[i]))

        return result

    def generate_signature_trajectory(self, strokes: List[List[Tuple[float, float]]],
                                     pen_down_list: Optional[List[bool]] = None,
                                     **kwargs) -> List[Dict]:
        """
        生成完整签名轨迹
        
        Args:
            strokes: 笔画列表，每个笔画是一个关键点列表
            pen_down_list: 每个笔画的落笔状态列表
            **kwargs: 传递给 generate_stroke_trajectory 的参数
            
        Returns:
            轨迹列表
        """
        if pen_down_list is None:
            pen_down_list = [True] * len(strokes)

        trajectories = []
        for i, (stroke, pen_down) in enumerate(zip(strokes, pen_down_list)):
            trajectory = self.generate_stroke_trajectory(
                stroke, pen_down=pen_down, **kwargs
            )
            trajectory['stroke_id'] = i
            trajectories.append(trajectory)

        return trajectories

    def normalize_trajectory(self, trajectories: List[Dict],
                           target_width: float = 900,
                           target_height: float = 800) -> List[Dict]:
        """
        归一化轨迹到指定范围
        
        Args:
            trajectories: 轨迹列表
            target_width: 目标宽度
            target_height: 目标高度
            
        Returns:
            归一化后的轨迹列表
        """
        if not trajectories:
            return trajectories

        # 收集所有点
        all_points = []
        for traj in trajectories:
            for point in traj['points']:
                all_points.append(point[:2])  # 只取 x, y

        if not all_points:
            return trajectories

        # 计算边界
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # 计算缩放比例
        width = max_x - min_x
        height = max_y - min_y

        if width == 0:
            width = 1
        if height == 0:
            height = 1

        scale_x = target_width / width
        scale_y = target_height / height
        scale = min(scale_x, scale_y)  # 保持比例

        # 计算偏移量（居中）
        offset_x = (target_width - width * scale) / 2
        offset_y = (target_height - height * scale) / 2

        # 归一化轨迹
        normalized = []
        for traj in trajectories:
            new_traj = traj.copy()
            new_points = []
            for point in traj['points']:
                x, y = point[0], point[1]
                t = point[2] if len(point) > 2 else 0.0
                
                # 归一化坐标
                new_x = (x - min_x) * scale + offset_x
                new_y = (y - min_y) * scale + offset_y
                new_points.append((new_x, new_y, t))
            
            new_traj['points'] = new_points
            normalized.append(new_traj)

        return normalized

    def apply_slant(self, trajectories: List[Dict], angle_degrees: float) -> List[Dict]:
        """Apply a horizontal shear around the signature's vertical centre.

        The operation deliberately happens before normalization, so a slanted
        signature still fits inside the final 0..1000 coordinate space.
        """
        if not trajectories or abs(angle_degrees) < 1e-6:
            return trajectories

        all_y = [point[1] for traj in trajectories for point in traj['points']]
        if not all_y:
            return trajectories

        centre_y = (min(all_y) + max(all_y)) / 2
        shear = np.tan(np.deg2rad(angle_degrees))
        result = []
        for traj in trajectories:
            new_traj = traj.copy()
            new_traj['points'] = [
                (point[0] + (point[1] - centre_y) * shear, point[1], *point[2:])
                for point in traj['points']
            ]
            result.append(new_traj)
        return result
