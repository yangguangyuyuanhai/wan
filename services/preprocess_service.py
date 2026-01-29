# -*- coding: utf-8 -*-
"""
图像预处理服务
负责图像格式转换、增强等预处理操作
"""

import numpy as np
import cv2
from pipeline_core import Filter, DataPacket
from logger_config import get_logger

logger = get_logger("PreprocessService")


class PreprocessService(Filter):
    """图像预处理服务"""
    
    def __init__(self, config):
        """
        初始化预处理服务
        
        Args:
            config: PreprocessServiceConfig配置对象
        """
        super().__init__("PreprocessService", config)
        logger.info("预处理服务初始化完成")
    
    def process(self, packet: DataPacket) -> DataPacket:
        """
        处理数据包
        
        Args:
            packet: 输入数据包
            
        Returns:
            处理后的数据包
        """
        if packet is None or packet.image is None:
            return packet
        
        try:
            # 转换图像格式
            image = self._convert_image(packet)
            
            if image is None:
                logger.warning(f"图像转换失败 [帧 {packet.frame_number}]")
                return packet
            
            # 调整大小
            if self.config.resize_enabled:
                image = self._resize_image(image)
            
            # 降噪
            if self.config.denoise_enabled:
                image = self._denoise_image(image)
            
            # 锐化
            if self.config.sharpen_enabled:
                image = self._sharpen_image(image)
            
            # 亮度对比度调整
            if self.config.brightness_adjust != 0 or self.config.contrast_adjust != 0:
                image = self._adjust_brightness_contrast(image)
            
            # 更新数据包
            packet.processed_image = image
            
            return packet
            
        except Exception as e:
            logger.exception(f"预处理异常: {e}")
            return packet
    
    def _convert_image(self, packet: DataPacket):
        """转换图像格式"""
        try:
            # 将ctypes指针转换为numpy数组
            image_array = np.frombuffer(packet.image, dtype=np.uint8)
            
            # 根据像素格式处理
            if packet.pixel_format == 0x01080001:  # Mono8
                image = image_array.reshape((packet.height, packet.width))
                if self.config.convert_to_bgr:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                # 尝试作为灰度图处理
                image = image_array.reshape((packet.height, packet.width))
                if self.config.convert_to_bgr:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            return image
            
        except Exception as e:
            logger.exception(f"图像转换异常: {e}")
            return None
    
    def _resize_image(self, image):
        """调整图像大小"""
        return cv2.resize(
            image,
            (self.config.resize_width, self.config.resize_height)
        )
    
    def _denoise_image(self, image):
        """图像降噪"""
        return cv2.fastNlMeansDenoisingColored(
            image,
            None,
            self.config.denoise_strength,
            self.config.denoise_strength,
            7,
            21
        )
    
    def _sharpen_image(self, image):
        """图像锐化"""
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]]) * self.config.sharpen_strength
        return cv2.filter2D(image, -1, kernel)
    
    def _adjust_brightness_contrast(self, image):
        """调整亮度和对比度"""
        alpha = 1.0 + self.config.contrast_adjust / 100.0
        beta = self.config.brightness_adjust
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
