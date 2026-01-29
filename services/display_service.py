# -*- coding: utf-8 -*-
"""
图像显示服务
负责实时显示处理结果
"""

import cv2
import time
from pipeline_core import Filter, DataPacket
from logger_config import get_logger

logger = get_logger("DisplayService")


class DisplayService(Filter):
    """图像显示服务"""
    
    def __init__(self, config):
        """
        初始化显示服务
        
        Args:
            config: DisplayServiceConfig配置对象
        """
        super().__init__("DisplayService", config)
        
        self.window_created = False
        self.last_display_time = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        logger.info("显示服务初始化完成")
    
    def process(self, packet: DataPacket) -> DataPacket:
        """
        处理数据包（显示图像）
        
        Args:
            packet: 输入数据包
            
        Returns:
            原样返回数据包
        """
        if packet is None or packet.processed_image is None:
            return packet
        
        try:
            # 帧率限制
            current_time = time.time()
            if self.config.display_fps_limit > 0:
                min_interval = 1.0 / self.config.display_fps_limit
                if current_time - self.last_display_time < min_interval:
                    return packet
            
            self.last_display_time = current_time
            
            # 创建窗口
            if not self.window_created:
                cv2.namedWindow(self.config.window_name, cv2.WINDOW_NORMAL)
                if self.config.window_width > 0 and self.config.window_height > 0:
                    cv2.resizeWindow(
                        self.config.window_name,
                        self.config.window_width,
                        self.config.window_height
                    )
                self.window_created = True
            
            # 准备显示图像
            display_image = packet.processed_image.copy()
            
            # 绘制检测结果
            if self.config.show_detections and packet.detections:
                display_image = self._draw_detections(display_image, packet.detections)
            
            # 添加信息叠加
            if self.config.show_fps or self.config.show_frame_count or self.config.show_timestamp:
                display_image = self._add_overlay_info(display_image, packet)
            
            # 显示图像
            cv2.imshow(self.config.window_name, display_image)
            
            # 处理按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' 或 ESC
                logger.info("用户请求退出")
                packet.metadata['user_exit'] = True
            
            # 更新FPS
            self._update_fps()
            
            return packet
            
        except Exception as e:
            logger.exception(f"显示异常: {e}")
            return packet
    
    def _draw_detections(self, image, detections):
        """绘制检测结果"""
        for det in detections:
            bbox = det['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            
            # 绘制边界框
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            label = f"{det['class_name']}: {det['confidence']:.2f}"
            cv2.putText(
                image,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        return image
    
    def _add_overlay_info(self, image, packet):
        """添加信息叠加"""
        y_offset = 30
        
        # FPS
        if self.config.show_fps:
            fps_text = f"FPS: {self.current_fps:.1f}"
            cv2.putText(
                image,
                fps_text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            y_offset += 30
        
        # 帧计数
        if self.config.show_frame_count:
            frame_text = f"Frame: {packet.frame_number}"
            cv2.putText(
                image,
                frame_text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            y_offset += 30
        
        # 检测信息
        if self.config.show_detection_info and packet.detections:
            det_text = f"Detections: {len(packet.detections)}"
            cv2.putText(
                image,
                det_text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        return image
    
    def _update_fps(self):
        """更新FPS计算"""
        self.fps_counter += 1
        elapsed = time.time() - self.fps_start_time
        
        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = time.time()
    
    def __del__(self):
        """析构函数"""
        try:
            cv2.destroyAllWindows()
        except:
            pass
