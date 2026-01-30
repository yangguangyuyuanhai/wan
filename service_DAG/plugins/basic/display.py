# -*- coding: utf-8 -*-
"""
图像显示节点插件
实时显示处理结果
"""

import cv2
import time
from typing import Dict, Any, List, Tuple

from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult
from engine.port import Port, PortType, DataType
from core.data_types import ImageType, DetectionListType
from logger_config import get_logger

logger = get_logger("DisplayNode")


class DisplayNode(INode):
    """
    图像显示节点
    接收图像数据并在窗口中显示
    """
    
    __plugin_metadata__ = {
        'type': 'display',
        'name': '图像显示',
        'version': '1.0.0',
        'author': 'System',
        'description': '实时显示图像和检测结果',
        'category': 'ui',
        'dependencies': ['cv2']  # 声明依赖OpenCV
    }
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)
        
        # 配置参数
        self.window_name = config.get('window_name', 'Display')
        self.window_width = config.get('window_width', 800)
        self.window_height = config.get('window_height', 600)
        self.show_fps = config.get('show_fps', True)
        self.show_frame_count = config.get('show_frame_count', True)
        self.show_detections = config.get('show_detections', True)
        self.show_detection_info = config.get('show_detection_info', True)
        self.display_fps_limit = config.get('display_fps_limit', 30)  # 限制显示帧率
        
        # 状态变量
        self.window_created = False
        self.last_display_time = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        self.frame_count = 0
    
    def get_metadata(self) -> NodeMetadata:
        return NodeMetadata(
            name=self.__plugin_metadata__['name'],
            version=self.__plugin_metadata__['version'],
            author=self.__plugin_metadata__['author'],
            description=self.__plugin_metadata__['description'],
            category=self.__plugin_metadata__['category']
        )
    
    def get_ports(self) -> Tuple[List[Port], List[Port]]:
        """
        定义端口
        显示节点接收图像输入，可选接收检测结果，无输出
        """
        inputs = [
            Port(
                name="image",
                port_type=PortType.INPUT,
                data_type=DataType.IMAGE,
                required=True,
                description="要显示的图像"
            ),
            Port(
                name="detections",
                port_type=PortType.INPUT,
                data_type=DataType.DETECTIONS,
                required=False,
                description="检测结果（可选）"
            )
        ]
        outputs = []  # 显示节点无输出
        return inputs, outputs
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        try:
            if 'window_name' in config:
                if not isinstance(config['window_name'], str):
                    logger.error("window_name 必须是字符串")
                    return False
            
            if 'display_fps_limit' in config:
                if not isinstance(config['display_fps_limit'], (int, float)) or config['display_fps_limit'] < 0:
                    logger.error("display_fps_limit 必须是非负数")
                    return False
            
            return True
            
        except Exception as e:
            logger.exception(f"配置验证异常: {e}")
            return False
    
    async def initialize(self):
        """初始化节点（创建窗口）"""
        try:
            # 创建窗口
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            if self.window_width > 0 and self.window_height > 0:
                cv2.resizeWindow(
                    self.window_name,
                    self.window_width,
                    self.window_height
                )
            self.window_created = True
            
            logger.info(f"显示节点 {self.node_id} 初始化成功，窗口: {self.window_name}")
            return True
            
        except Exception as e:
            logger.exception(f"初始化异常: {e}")
            return False
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        """
        执行节点（显示图像）
        """
        try:
            # 获取输入数据
            image_data = context.inputs.get('image')
            detections_data = context.inputs.get('detections')
            
            if image_data is None:
                return NodeResult(
                    success=False,
                    outputs={},
                    error="未接收到图像数据"
                )
            
            # 帧率限制
            current_time = time.time()
            if self.display_fps_limit > 0:
                min_interval = 1.0 / self.display_fps_limit
                if current_time - self.last_display_time < min_interval:
                    # 跳过此帧显示
                    return NodeResult(
                        success=True,
                        outputs={},
                        metadata={'skipped': True}
                    )
            
            self.last_display_time = current_time
            self.frame_count += 1
            
            # 获取图像数据
            if isinstance(image_data, ImageType):
                display_image = image_data.data.copy()
            else:
                display_image = image_data.copy()
            
            # 绘制检测结果
            if self.show_detections and detections_data:
                display_image = self._draw_detections(display_image, detections_data)
            
            # 添加信息叠加
            if self.show_fps or self.show_frame_count or self.show_detection_info:
                display_image = self._add_overlay_info(
                    display_image,
                    self.frame_count,
                    detections_data
                )
            
            # 显示图像
            cv2.imshow(self.window_name, display_image)
            
            # 处理按键
            key = cv2.waitKey(1) & 0xFF
            user_exit = False
            if key == ord('q') or key == 27:  # 'q' 或 ESC
                logger.info("用户请求退出")
                user_exit = True
            
            # 更新FPS
            self._update_fps()
            
            return NodeResult(
                success=True,
                outputs={},
                metadata={
                    'frame_count': self.frame_count,
                    'current_fps': self.current_fps,
                    'user_exit': user_exit
                }
            )
            
        except Exception as e:
            logger.exception(f"显示异常: {e}")
            return NodeResult(
                success=False,
                outputs={},
                error=str(e)
            )
    
    def _draw_detections(self, image, detections):
        """绘制检测结果"""
        try:
            if isinstance(detections, DetectionListType):
                detections = detections.detections
            
            for det in detections:
                # 获取边界框
                if hasattr(det, 'bbox'):
                    bbox = det.bbox
                    x1, y1, x2, y2 = int(bbox.x), int(bbox.y), int(bbox.x + bbox.w), int(bbox.y + bbox.h)
                elif isinstance(det, dict):
                    bbox = det.get('bbox', [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = map(int, bbox)
                    else:
                        continue
                else:
                    continue
                
                # 绘制边界框
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # 获取标签信息
                if hasattr(det, 'class_name'):
                    class_name = det.class_name
                    confidence = det.confidence
                elif isinstance(det, dict):
                    class_name = det.get('class_name', 'Unknown')
                    confidence = det.get('confidence', 0.0)
                else:
                    continue
                
                # 绘制标签
                label = f"{class_name}: {confidence:.2f}"
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
            
        except Exception as e:
            logger.exception(f"绘制检测结果异常: {e}")
            return image
    
    def _add_overlay_info(self, image, frame_count, detections):
        """添加信息叠加"""
        try:
            y_offset = 30
            
            # FPS
            if self.show_fps:
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
            if self.show_frame_count:
                frame_text = f"Frame: {frame_count}"
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
            if self.show_detection_info and detections:
                det_count = len(detections.detections) if isinstance(detections, DetectionListType) else len(detections)
                det_text = f"Detections: {det_count}"
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
            
        except Exception as e:
            logger.exception(f"添加信息叠加异常: {e}")
            return image
    
    def _update_fps(self):
        """更新FPS计算"""
        self.fps_counter += 1
        elapsed = time.time() - self.fps_start_time
        
        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = time.time()
    
    async def cleanup(self):
        """清理资源（关闭窗口）"""
        try:
            if self.window_created:
                cv2.destroyWindow(self.window_name)
                logger.info(f"显示节点 {self.node_id} 清理完成")
            
        except Exception as e:
            logger.exception(f"清理资源异常: {e}")
