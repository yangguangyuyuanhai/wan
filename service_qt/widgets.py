# -*- coding: utf-8 -*-
"""
自定义Qt控件
包含图像显示、图表等专用控件
"""

from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
import numpy as np
import cv2


class ImageDisplayWidget(QLabel):
    """
    图像显示控件
    支持图像缩放、检测框绘制
    """
    
    clicked = pyqtSignal(int, int)  # 点击信号(x, y)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 480)
        self.setScaledContents(False)
        self.setStyleSheet("""
            background-color: #1A1A1A;
            border: 2px solid #3E3E3E;
            border-radius: 5px;
        """)
        
        self.current_image = None
        self.detections = []
        self.show_detections = True
        
    def set_image(self, image, detections=None):
        """
        设置显示图像
        
        Args:
            image: numpy数组 (BGR格式)
            detections: 检测结果列表
        """
        if image is None:
            return
        
        self.current_image = image.copy()
        self.detections = detections if detections else []
        
        # 绘制检测框
        if self.show_detections and self.detections:
            self._draw_detections()
        
        # 转换为QPixmap
        self._update_pixmap()
    
    def _draw_detections(self):
        """在图像上绘制检测框"""
        if self.current_image is None:
            return
        
        for det in self.detections:
            # 获取检测框信息
            x1, y1, x2, y2 = det.get('bbox', [0, 0, 0, 0])
            confidence = det.get('confidence', 0.0)
            class_name = det.get('class', 'unknown')
            
            # 绘制矩形框
            color = (0, 217, 255)  # 海康蓝色 (BGR)
            thickness = 2
            cv2.rectangle(self.current_image, (int(x1), int(y1)), 
                         (int(x2), int(y2)), color, thickness)
            
            # 绘制标签背景
            label = f"{class_name}: {confidence:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 2
            
            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, font_thickness
            )
            
            # 标签背景矩形
            cv2.rectangle(
                self.current_image,
                (int(x1), int(y1) - text_height - 10),
                (int(x1) + text_width + 10, int(y1)),
                color,
                -1
            )
            
            # 绘制文字
            cv2.putText(
                self.current_image,
                label,
                (int(x1) + 5, int(y1) - 5),
                font,
                font_scale,
                (255, 255, 255),
                font_thickness
            )
    
    def _update_pixmap(self):
        """更新显示的Pixmap"""
        if self.current_image is None:
            return
        
        # 转换BGR到RGB
        rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        
        # 创建QImage
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # 创建QPixmap并缩放
        pixmap = QPixmap.fromImage(qt_image)
        
        # 按比例缩放以适应控件大小
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
    
    def toggle_detections(self, show):
        """切换检测框显示"""
        self.show_detections = show
        if self.current_image is not None:
            self.set_image(self.current_image, self.detections)
    
    def clear(self):
        """清除显示"""
        self.current_image = None
        self.detections = []
        self.setText("等待图像...")
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(event.x(), event.y())
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        if self.current_image is not None:
            self._update_pixmap()


class StatusIndicator(QWidget):
    """
    状态指示器控件
    显示圆形状态灯
    """
    
    def __init__(self, label="状态", parent=None):
        super().__init__(parent)
        self.label = label
        self.status = "inactive"  # inactive, active, warning, error
        self.setMinimumSize(100, 30)
    
    def set_status(self, status):
        """
        设置状态
        
        Args:
            status: inactive/active/warning/error
        """
        self.status = status
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 状态颜色映射
        colors = {
            "inactive": QColor(100, 100, 100),  # 灰色
            "active": QColor(0, 204, 102),      # 绿色
            "warning": QColor(255, 165, 0),     # 橙色
            "error": QColor(255, 68, 68)        # 红色
        }
        
        color = colors.get(self.status, colors["inactive"])
        
        # 绘制圆形指示灯
        painter.setBrush(color)
        painter.setPen(QPen(color.darker(120), 2))
        painter.drawEllipse(5, 5, 20, 20)
        
        # 绘制文字
        painter.setPen(QColor(224, 224, 224))
        painter.setFont(QFont("Microsoft YaHei", 10))
        painter.drawText(30, 20, self.label)


class PerformanceChart(QWidget):
    """
    性能图表控件
    显示FPS、处理时间等实时曲线
    """
    
    def __init__(self, title="性能", max_points=100, parent=None):
        super().__init__(parent)
        self.title = title
        self.max_points = max_points
        self.data_points = []
        self.setMinimumSize(300, 150)
        
        self.setStyleSheet("""
            background-color: #2D2D2D;
            border: 1px solid #3E3E3E;
            border-radius: 3px;
        """)
    
    def add_data_point(self, value):
        """添加数据点"""
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()
    
    def clear(self):
        """清除数据"""
        self.data_points.clear()
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        if not self.data_points:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景网格
        painter.setPen(QPen(QColor(62, 62, 62), 1))
        width = self.width()
        height = self.height()
        
        # 水平网格线
        for i in range(5):
            y = int(height * i / 4)
            painter.drawLine(0, y, width, y)
        
        # 垂直网格线
        for i in range(10):
            x = int(width * i / 9)
            painter.drawLine(x, 0, x, height)
        
        # 绘制数据曲线
        if len(self.data_points) > 1:
            painter.setPen(QPen(QColor(0, 217, 255), 2))
            
            max_value = max(self.data_points) if self.data_points else 1
            min_value = min(self.data_points) if self.data_points else 0
            value_range = max_value - min_value if max_value != min_value else 1
            
            points = []
            for i, value in enumerate(self.data_points):
                x = int(width * i / (self.max_points - 1))
                y = int(height - (height * (value - min_value) / value_range))
                points.append((x, y))
            
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], 
                               points[i+1][0], points[i+1][1])
        
        # 绘制标题和当前值
        painter.setPen(QColor(224, 224, 224))
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        
        current_value = self.data_points[-1] if self.data_points else 0
        text = f"{self.title}: {current_value:.2f}"
        painter.drawText(10, 20, text)


class CameraListWidget(QWidget):
    """
    相机列表控件
    显示已连接的相机列表
    """
    
    camera_selected = pyqtSignal(int)  # 相机索引
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cameras = []
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # TODO: 添加相机列表显示
    
    def update_cameras(self, camera_list):
        """更新相机列表"""
        self.cameras = camera_list
        # TODO: 更新显示


class DetectionResultWidget(QWidget):
    """
    检测结果显示控件
    以卡片形式显示检测到的对象
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detections = []
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # TODO: 添加检测结果卡片
    
    def update_detections(self, detections):
        """更新检测结果"""
        self.detections = detections
        # TODO: 更新显示
