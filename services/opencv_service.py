# -*- coding: utf-8 -*-
"""
OpenCV图像处理服务
负责边缘检测、轮廓检测等OpenCV操作
"""

import cv2
import numpy as np
from pipeline_core import Filter, DataPacket
from logger_config import get_logger

logger = get_logger("OpenCVService")


class OpenCVService(Filter):
    """OpenCV图像处理服务"""
    
    def __init__(self, config):
        """
        初始化OpenCV服务
        
        Args:
            config: OpenCVServiceConfig配置对象
        """
        super().__init__("OpenCVService", config)
        logger.info("OpenCV服务初始化完成")
    
    def process(self, packet: DataPacket) -> DataPacket:
        """
        处理数据包
        
        Args:
            packet: 输入数据包
            
        Returns:
            处理后的数据包
        """
        if packet is None or packet.processed_image is None:
            return packet
        
        try:
            image = packet.processed_image.copy()
            
            # 边缘检测
            if self.config.edge_detection_enabled:
                edges = self._detect_edges(image)
                packet.metadata['edges'] = edges
            
            # 轮廓检测
            if self.config.contour_detection_enabled:
                contours = self._detect_contours(image)
                packet.metadata['contours'] = contours
                
                # 在图像上绘制轮廓
                cv2.drawContours(image, contours, -1, (0, 255, 0), 2)
            
            # 形态学操作
            if self.config.morphology_enabled:
                image = self._apply_morphology(image)
            
            packet.processed_image = image
            
            return packet
            
        except Exception as e:
            logger.exception(f"OpenCV处理异常: {e}")
            return packet
    
    def _detect_edges(self, image):
        """边缘检测"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        edges = cv2.Canny(
            gray,
            self.config.canny_threshold1,
            self.config.canny_threshold2
        )
        return edges
    
    def _detect_contours(self, image):
        """轮廓检测"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 过滤轮廓
        filtered_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.config.contour_min_area <= area <= self.config.contour_max_area:
                filtered_contours.append(contour)
        
        return filtered_contours
    
    def _apply_morphology(self, image):
        """形态学操作"""
        kernel = np.ones(
            (self.config.morphology_kernel_size, self.config.morphology_kernel_size),
            np.uint8
        )
        
        if self.config.morphology_operation == "open":
            return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        elif self.config.morphology_operation == "close":
            return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        elif self.config.morphology_operation == "gradient":
            return cv2.morphologyEx(image, cv2.MORPH_GRADIENT, kernel)
        
        return image
