import math
import numpy as np

def point_in_polygon(point, polygon):
    """
    检查点是否在多边形内部
    
    参数:
        point: 待检查的点坐标 (x, y)
        polygon: 多边形顶点坐标列表
        
    返回:
        bool: 如果点在多边形内部则为True，否则为False
    """
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def distance_to_polygon(point, polygon):
    """
    计算点到多边形边缘的最小距离
    
    参数:
        point: 待计算的点坐标 (x, y)
        polygon: 多边形顶点坐标列表
        
    返回:
        float: 点到多边形边缘的最小距离
    """
    min_distance = float('inf')
    x, y = point
    n = len(polygon)
    
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        
        # 计算点到线段的距离
        A = x - x1
        B = y - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        # 避免除以零
        if len_sq == 0:
            dist = math.sqrt(A * A + B * B)
        else:
            param = dot / len_sq
            
            if param < 0:
                xx = x1
                yy = y1
            elif param > 1:
                xx = x2
                yy = y2
            else:
                xx = x1 + param * C
                yy = y1 + param * D
                
            dist = math.sqrt((x - xx) ** 2 + (y - yy) ** 2)
            
        min_distance = min(min_distance, dist)
    
    return min_distance 