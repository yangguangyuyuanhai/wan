# -*- coding: utf-8 -*-
"""
OpenCV图像处理节点插件
负责边缘检测、轮廓检测等OpenCV操作

迁移自：service_new/services/opencv_service.py
响应任务：任务 14.1 - 创建 OpenCVProcessNode 插件
关键优化：使用 run_in_executor 避免 GIL 阻塞
"""

import asyncio
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import concurrent.futures

from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult, NodeState
from engine.port import InputPort, OutputPort
from core.data_types import ImageType, DetectionListType
from core.exceptions import NodeExecutionError


@dataclass
class OpenCVConfig:
    """OpenCV处理配置"""
    # 边缘检测
    edge_detection_enabled: bool = False
    canny_threshold1: int = 50
    canny_threshold2: int = 150
    
    # 轮廓检测
    contour_detection_enabled: bool = False
    contour_min_area: int = 100
    contour_max_area: int = 10000
    draw_contours: bool = True
    contour_color: tuple = (0, 255, 0)  # BGR格式
    contour_thickness: int = 2
    
    # 形态学操作
    morphology_enabled: bool = False
    morphology_operation: str = "open"  # open/close/gradient/erode/dilate
    morphology_kernel_size: int = 5
    morphology_iterations: int = 1
    
    # 高斯模糊
    blur_enabled: bool = False
    blur_kernel_size: int = 5
    blur_sigma_x: float = 0.0
    blur_sigma_y: float = 0.0
    
    # 双边滤波
    bilateral_enabled: bool = False
    bilateral_d: int = 9
    bilateral_sigma_color: float = 75.0
    bilateral_sigma_space: float = 75.0


class OpenCVProcessNode(INode):
    """
    OpenCV图像处理节点
    
    功能：
    - 边缘检测（Canny）
    - 轮廓检测和绘制
    - 形态学操作（开运算、闭运算、梯度等）
    - 高斯模糊
    - 双边滤波
    
    性能优化：
    - 使用 run_in_executor 避免 GIL 阻塞
    - 支持多种操作组合
    - 可配置的处理参数
    """
    
    # 插件元数据
    __plugin_metadata__ = {
        "type": "opencv_process",
        "name": "OpenCV图像处理节点",
        "version": "1.0.0",
        "author": "Kiro AI Assistant",
        "description": "OpenCV图像处理：边缘检测、轮廓检测、形态学操作、滤波等",
        "category": "algo",
        "dependencies": ["opencv-python", "numpy"]
    }
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        初始化OpenCV处理节点
        
        Args:
            node_id: 节点ID
            config: 节点配置
        """
        self.node_id = node_id
        self.config = OpenCVConfig(**config)
        self.state = NodeState.IDLE
        
        # 线程池执行器（用于CPU密集任务）
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,  # OpenCV操作通常单线程
            thread_name_prefix=f"opencv_{node_id}"
        )
        
        # 统计信息
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.contour_count = 0
        
        # 输入输出端口
        self._input_ports = [
            InputPort("image", ImageType, required=True, description="输入图像"),
            InputPort("detections", DetectionListType, required=False, description="检测结果（可选）")
        ]
        self._output_ports = [
            OutputPort("processed_image", ImageType, description="处理后的图像"),
            OutputPort("metadata", MetadataType, description="处理元数据（边缘、轮廓等）")
        ]
    
    def get_metadata(self) -> NodeMetadata:
        """获取节点元数据"""
        return NodeMetadata(
            name=self.__plugin_metadata__["name"],
            version=self.__plugin_metadata__["version"],
            author=self.__plugin_metadata__["author"],
            description=self.__plugin_metadata__["description"],
            category=self.__plugin_metadata__["category"],
            tags=["opencv", "image_processing", "edge_detection", "contour"]
        )
    
    def get_ports(self) -> tuple[List[InputPort], List[OutputPort]]:
        """获取输入输出端口"""
        return self._input_ports, self._output_ports
    
    def validate_config(self) -> bool:
        """验证节点配置"""
        try:
            # 验证Canny参数
            if self.config.edge_detection_enabled:
                if not (0 <= self.config.canny_threshold1 <= 255):
                    return False
                if not (0 <= self.config.canny_threshold2 <= 255):
                    return False
                if self.config.canny_threshold1 >= self.config.canny_threshold2:
                    return False
            
            # 验证轮廓参数
            if self.config.contour_detection_enabled:
                if self.config.contour_min_area < 0:
                    return False
                if self.config.contour_max_area <= self.config.contour_min_area:
                    return False
            
            # 验证形态学参数
            if self.config.morphology_enabled:
                if self.config.morphology_operation not in [
                    "open", "close", "gradient", "erode", "dilate"
                ]:
                    return False
                if self.config.morphology_kernel_size <= 0:
                    return False
                if self.config.morphology_iterations <= 0:
                    return False
            
            # 验证模糊参数
            if self.config.blur_enabled:
                if self.config.blur_kernel_size <= 0 or self.config.blur_kernel_size % 2 == 0:
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def initialize(self) -> bool:
        """初始化节点"""
        try:
            # 验证配置
            if not self.validate_config():
                raise NodeExecutionError(f"节点 {self.node_id} 配置验证失败")
            
            self.state = NodeState.IDLE
            return True
            
        except Exception as e:
            self.state = NodeState.ERROR
            raise NodeExecutionError(f"节点 {self.node_id} 初始化失败: {e}")
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        """
        执行OpenCV处理
        
        Args:
            context: 执行上下文，包含输入数据
            
        Returns:
            NodeResult: 包含处理结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.state = NodeState.RUNNING
            
            # 获取输入图像
            input_data = context.inputs.get("image")
            if input_data is None:
                raise NodeExecutionError("缺少输入图像")
            
            # 验证输入类型
            if not isinstance(input_data, ImageType):
                raise NodeExecutionError(f"输入数据类型错误，期望 ImageType，得到 {type(input_data)}")
            
            # 获取可选的检测结果
            detections = context.inputs.get("detections")
            
            # 在线程池中执行处理（避免GIL阻塞）
            loop = asyncio.get_event_loop()
            processed_image, metadata = await loop.run_in_executor(
                self.executor, 
                self._process_image, 
                input_data,
                detections
            )
            
            # 更新统计
            self.processed_count += 1
            processing_time = asyncio.get_event_loop().time() - start_time
            self.total_processing_time += processing_time
            
            # 更新轮廓计数
            if 'contours' in metadata.data:
                self.contour_count += len(metadata.data['contours'])
            
            self.state = NodeState.COMPLETED
            
            # 返回结果
            return NodeResult(
                success=True,
                outputs={
                    "processed_image": processed_image,
                    "metadata": metadata
                },
                metadata={"processing_time": processing_time,
                         "processed_count": self.processed_count,
                         "node_id": self.node_id}
            )
            
        except Exception as e:
            self.error_count += 1
            self.state = NodeState.ERROR
            
            return NodeResult(
                success=False,
                outputs={},
                error=f"OpenCV处理失败: {e}",
                metadata={"error_count": self.error_count,
                         "node_id": self.node_id}
            )
    
    def _process_image(self, input_image: ImageType, detections: Optional[DetectionListType] = None) -> tuple[ImageType, MetadataType]:
        """
        执行OpenCV图像处理（在线程池中执行）
        
        Args:
            input_image: 输入图像
            detections: 可选的检测结果
            
        Returns:
            tuple: (处理后的图像, 元数据)
        """
        try:
            # 复制图像以避免修改原始数据
            image = input_image.data.copy()
            metadata_dict = {}
            
            # 1. 高斯模糊
            if self.config.blur_enabled:
                image = self._apply_gaussian_blur(image)
                metadata_dict['blur_applied'] = True
            
            # 2. 双边滤波
            if self.config.bilateral_enabled:
                image = self._apply_bilateral_filter(image)
                metadata_dict['bilateral_applied'] = True
            
            # 3. 边缘检测
            if self.config.edge_detection_enabled:
                edges = self._detect_edges(image)
                metadata_dict['edges'] = edges
                metadata_dict['edge_pixels'] = np.count_nonzero(edges)
            
            # 4. 轮廓检测
            if self.config.contour_detection_enabled:
                contours = self._detect_contours(image)
                metadata_dict['contours'] = contours
                metadata_dict['contour_count'] = len(contours)
                
                # 绘制轮廓
                if self.config.draw_contours and len(contours) > 0:
                    image = self._draw_contours(image, contours)
            
            # 5. 形态学操作
            if self.config.morphology_enabled:
                image = self._apply_morphology(image)
                metadata_dict['morphology_applied'] = self.config.morphology_operation
            
            # 创建输出图像
            processed_image = ImageType(
                data=image,
                width=image.shape[1],
                height=image.shape[0],
                channels=image.shape[2] if len(image.shape) == 3 else 1,
                format=input_image.format
            )
            
            # 创建元数据
            metadata = MetadataType(metadata_dict)
            
            return processed_image, metadata
            
        except Exception as e:
            raise NodeExecutionError(f"OpenCV处理执行失败: {e}")
    
    def _apply_gaussian_blur(self, image: np.ndarray) -> np.ndarray:
        """应用高斯模糊"""
        try:
            return cv2.GaussianBlur(
                image,
                (self.config.blur_kernel_size, self.config.blur_kernel_size),
                self.config.blur_sigma_x,
                sigmaY=self.config.blur_sigma_y
            )
        except Exception as e:
            raise NodeExecutionError(f"高斯模糊失败: {e}")
    
    def _apply_bilateral_filter(self, image: np.ndarray) -> np.ndarray:
        """应用双边滤波"""
        try:
            return cv2.bilateralFilter(
                image,
                self.config.bilateral_d,
                self.config.bilateral_sigma_color,
                self.config.bilateral_sigma_space
            )
        except Exception as e:
            raise NodeExecutionError(f"双边滤波失败: {e}")
    
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """边缘检测"""
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Canny边缘检测
            edges = cv2.Canny(
                gray,
                self.config.canny_threshold1,
                self.config.canny_threshold2
            )
            
            return edges
            
        except Exception as e:
            raise NodeExecutionError(f"边缘检测失败: {e}")
    
    def _detect_contours(self, image: np.ndarray) -> List[np.ndarray]:
        """轮廓检测"""
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 二值化
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # 查找轮廓
            contours, _ = cv2.findContours(
                thresh, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # 过滤轮廓
            filtered_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.config.contour_min_area <= area <= self.config.contour_max_area:
                    filtered_contours.append(contour)
            
            return filtered_contours
            
        except Exception as e:
            raise NodeExecutionError(f"轮廓检测失败: {e}")
    
    def _draw_contours(self, image: np.ndarray, contours: List[np.ndarray]) -> np.ndarray:
        """绘制轮廓"""
        try:
            # 绘制所有轮廓
            cv2.drawContours(
                image, 
                contours, 
                -1,  # 绘制所有轮廓
                self.config.contour_color, 
                self.config.contour_thickness
            )
            
            return image
            
        except Exception as e:
            # 绘制失败不影响主流程
            print(f"绘制轮廓失败: {e}")
            return image
    
    def _apply_morphology(self, image: np.ndarray) -> np.ndarray:
        """应用形态学操作"""
        try:
            # 创建结构元素
            kernel = np.ones(
                (self.config.morphology_kernel_size, self.config.morphology_kernel_size),
                np.uint8
            )
            
            # 选择操作类型
            if self.config.morphology_operation == "open":
                return cv2.morphologyEx(
                    image, cv2.MORPH_OPEN, kernel, 
                    iterations=self.config.morphology_iterations
                )
            elif self.config.morphology_operation == "close":
                return cv2.morphologyEx(
                    image, cv2.MORPH_CLOSE, kernel,
                    iterations=self.config.morphology_iterations
                )
            elif self.config.morphology_operation == "gradient":
                return cv2.morphologyEx(
                    image, cv2.MORPH_GRADIENT, kernel,
                    iterations=self.config.morphology_iterations
                )
            elif self.config.morphology_operation == "erode":
                return cv2.erode(
                    image, kernel, 
                    iterations=self.config.morphology_iterations
                )
            elif self.config.morphology_operation == "dilate":
                return cv2.dilate(
                    image, kernel,
                    iterations=self.config.morphology_iterations
                )
            else:
                return image
                
        except Exception as e:
            raise NodeExecutionError(f"形态学操作失败: {e}")
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 关闭线程池
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            
            self.state = NodeState.STOPPED
            
        except Exception as e:
            print(f"OpenCV节点清理失败: {e}")
    
    def input_data_processed_hook(self, input_name: str) -> None:
        """输入数据处理完成钩子（用于引用计数）"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        avg_time = (self.total_processing_time / self.processed_count 
                   if self.processed_count > 0 else 0.0)
        
        avg_contours = (self.contour_count / self.processed_count 
                       if self.processed_count > 0 else 0.0)
        
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "contour_count": self.contour_count,
            "average_processing_time": avg_time,
            "average_contours_per_frame": avg_contours,
            "total_processing_time": self.total_processing_time,
            "error_rate": self.error_count / max(self.processed_count, 1),
            "enabled_operations": {
                "edge_detection": self.config.edge_detection_enabled,
                "contour_detection": self.config.contour_detection_enabled,
                "morphology": self.config.morphology_enabled,
                "blur": self.config.blur_enabled,
                "bilateral": self.config.bilateral_enabled
            }
        }
