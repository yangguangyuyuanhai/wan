# -*- coding: utf-8 -*-
"""
YOLO目标检测服务
负责使用YOLO模型进行目标检测
"""

import cv2
import numpy as np
from pipeline_core import Filter, DataPacket
from logger_config import get_logger

logger = get_logger("YOLOService")


class YOLOService(Filter):
    """YOLO目标检测服务"""
    
    def __init__(self, config):
        """
        初始化YOLO服务
        
        Args:
            config: YOLOServiceConfig配置对象
        """
        super().__init__("YOLOService", config)
        
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载YOLO模型"""
        try:
            # 尝试导入ultralytics（YOLOv8）
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.config.model_path)
                logger.info(f"YOLOv8模型加载成功: {self.config.model_path}")
                return
            except ImportError:
                logger.warning("ultralytics未安装，尝试使用OpenCV DNN")
            
            # 使用OpenCV DNN作为备选
            # 注意：这里需要ONNX格式的模型
            if self.config.model_path.endswith('.onnx'):
                self.model = cv2.dnn.readNetFromONNX(self.config.model_path)
                logger.info(f"使用OpenCV DNN加载模型: {self.config.model_path}")
            else:
                logger.error("模型格式不支持，请使用.pt或.onnx格式")
                self.enabled = False
                
        except Exception as e:
            logger.exception(f"加载模型失败: {e}")
            self.enabled = False
    
    def process(self, packet: DataPacket) -> DataPacket:
        """
        处理数据包（目标检测）
        
        Args:
            packet: 输入数据包
            
        Returns:
            包含检测结果的数据包
        """
        if packet is None or packet.processed_image is None:
            return packet
        
        if self.model is None:
            return packet
        
        try:
            image = packet.processed_image
            
            # 使用ultralytics YOLO
            if hasattr(self.model, 'predict'):
                results = self.model.predict(
                    image,
                    conf=self.config.confidence_threshold,
                    iou=self.config.iou_threshold,
                    max_det=self.config.max_detections,
                    verbose=False
                )
                
                # 解析检测结果
                detections = []
                if len(results) > 0:
                    result = results[0]
                    boxes = result.boxes
                    
                    for box in boxes:
                        detection = {
                            'bbox': box.xyxy[0].cpu().numpy().tolist(),  # [x1, y1, x2, y2]
                            'confidence': float(box.conf[0]),
                            'class_id': int(box.cls[0]),
                            'class_name': result.names[int(box.cls[0])]
                        }
                        detections.append(detection)
                
                packet.detections = detections
                
                # 记录检测结果
                if len(detections) > 0:
                    logger.debug(f"检测到 {len(detections)} 个目标 [帧 {packet.frame_number}]")
            
            return packet
            
        except Exception as e:
            logger.exception(f"目标检测异常: {e}")
            return packet
