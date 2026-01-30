"""
算法处理插件模块

包含图像预处理、YOLO检测、OpenCV处理等算法插件
"""

from .preprocess import PreprocessNode
from .yolo_infer import YoloInferenceNode
from .opencv_proc import OpenCVProcessNode

__all__ = [
    'PreprocessNode',
    'YoloInferenceNode', 
    'OpenCVProcessNode'
]
