# -*- coding: utf-8 -*-
"""
数据存储服务
负责保存图像和检测结果
"""

import cv2
import json
import os
from datetime import datetime
from pipeline_core import Filter, DataPacket
from logger_config import get_logger

logger = get_logger("StorageService")


class StorageService(Filter):
    """数据存储服务"""
    
    def __init__(self, config):
        """
        初始化存储服务
        
        Args:
            config: StorageServiceConfig配置对象
        """
        super().__init__("StorageService", config)
        
        # 创建保存目录
        if self.config.save_images:
            os.makedirs(self.config.save_path, exist_ok=True)
        
        self.detection_log = []
        
        logger.info("存储服务初始化完成")
    
    def process(self, packet: DataPacket) -> DataPacket:
        """
        处理数据包（保存数据）
        
        Args:
            packet: 输入数据包
            
        Returns:
            原样返回数据包
        """
        if packet is None:
            return packet
        
        try:
            # 判断是否需要保存
            should_save = False
            
            if self.config.save_all_frames:
                should_save = True
            elif packet.frame_number % self.config.save_interval == 0:
                should_save = True
            elif self.config.save_on_detection and len(packet.detections) > 0:
                should_save = True
            
            # 保存图像
            if should_save and self.config.save_images and packet.processed_image is not None:
                self._save_image(packet)
            
            # 保存检测结果
            if self.config.save_detections and len(packet.detections) > 0:
                self._save_detection(packet)
            
            return packet
            
        except Exception as e:
            logger.exception(f"存储异常: {e}")
            return packet
    
    def _save_image(self, packet: DataPacket):
        """保存图像"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"frame_{packet.frame_number}_{timestamp}.{self.config.save_format}"
            filepath = os.path.join(self.config.save_path, filename)
            
            if self.config.save_format.lower() == 'jpg':
                cv2.imwrite(
                    filepath,
                    packet.processed_image,
                    [cv2.IMWRITE_JPEG_QUALITY, self.config.jpeg_quality]
                )
            else:
                cv2.imwrite(filepath, packet.processed_image)
            
            logger.debug(f"保存图像: {filename}")
            
        except Exception as e:
            logger.exception(f"保存图像异常: {e}")
    
    def _save_detection(self, packet: DataPacket):
        """保存检测结果"""
        try:
            detection_record = {
                'frame_number': packet.frame_number,
                'timestamp': packet.timestamp,
                'detections': packet.detections,
                'processing_times': packet.processing_times
            }
            
            self.detection_log.append(detection_record)
            
            # 每100条记录保存一次
            if len(self.detection_log) >= 100:
                self._flush_detection_log()
            
        except Exception as e:
            logger.exception(f"保存检测结果异常: {e}")
    
    def _flush_detection_log(self):
        """刷新检测日志到文件"""
        try:
            if not self.detection_log:
                return
            
            # 读取现有数据
            existing_data = []
            if os.path.exists(self.config.detection_log_path):
                with open(self.config.detection_log_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # 追加新数据
            existing_data.extend(self.detection_log)
            
            # 保存
            with open(self.config.detection_log_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"保存 {len(self.detection_log)} 条检测记录")
            self.detection_log = []
            
        except Exception as e:
            logger.exception(f"刷新检测日志异常: {e}")
    
    def __del__(self):
        """析构函数"""
        # 保存剩余的检测记录
        if self.detection_log:
            self._flush_detection_log()
