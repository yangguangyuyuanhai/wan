# -*- coding: utf-8 -*-
"""
Qt前端界面包
工业视觉系统GUI - 海康威视风格
"""

__version__ = "1.0.0"
__author__ = "Kiro AI Assistant"

from .main_window import MainWindow
from .widgets import (
    ImageDisplayWidget,
    StatusIndicator,
    PerformanceChart,
    CameraListWidget,
    DetectionResultWidget
)
from .styles import get_hikvision_style, get_svg_icons

__all__ = [
    'MainWindow',
    'ImageDisplayWidget',
    'StatusIndicator',
    'PerformanceChart',
    'CameraListWidget',
    'DetectionResultWidget',
    'get_hikvision_style',
    'get_svg_icons',
]
