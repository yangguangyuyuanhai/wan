# -*- coding: utf-8 -*-
"""
图像预处理节点插件
负责图像格式转换、增强等预处理操作

迁移自：service_new/services/preprocess_service.py
响应任务：任务 12.1 - 创建 PreprocessNode 插件
"""

import asyncio
import numpy as np
import cv2
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult, NodeState
from engine.port import InputPort, OutputPort
from core.data_types import ImageType
from core.exceptions import NodeExecutionError


@dataclass
class PreprocessConfig:
    """预处理配置"""
    # 格式转换
    convert_to_bgr: bool = True
    
    # 图像缩放
    resize_enabled: bool = False
    resize_width: int = 640
    resize_height: int = 480
    
    # 降噪
    denoise_enabled: bool = False
    denoise_strength: float = 10.0
    
    # 锐化
    sharpen_enabled: bool = False
    sharpen_strength: float = 0.5
    
    # 亮度对比度
    brightness_adjust: int = 0  # -100 到 100
    contrast_adjust: int = 0    # -100 到 100


class PreprocessNode(INode):
    """
    图像预处理节点
    
    功能：
    - 图像格式转换（Mono8 → BGR）
    - 图像缩放
    - 降噪（fastNlMeansDenoisingColored）
    - 锐化
    - 亮度对比度调整
    """
    
    # 插件元数据
    __plugin_metadata__ = {
        "type": "preprocess",
        "name": "图像预处理节点",
        "version": "1.0.0",
        "author": "Kiro AI Assistant",
        "description": "图像预处理：格式转换、缩放、降噪、锐化、亮度对比度调整",
        "category": "algo",
        "dependencies": ["opencv-python", "numpy"]
    }
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        初始化预处理节点
        
        Args:
            node_id: 节点ID
            config: 节点配置
        """
        self.node_id = node_id
        self.config = PreprocessConfig(**config)
        self.state = NodeState.IDLE
        
        # 统计信息
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        
        # 输入输出端口
        self._input_ports = [
            InputPort("image", ImageType, required=True, description="输入图像")
        ]
        self._output_ports = [
            OutputPort("image", ImageType, description="预处理后的图像")
        ]
    
    def get_metadata(self) -> NodeMetadata:
        """获取节点元数据"""
        return NodeMetadata(
            name=self.__plugin_metadata__["name"],
            version=self.__plugin_metadata__["version"],
            author=self.__plugin_metadata__["author"],
            description=self.__plugin_metadata__["description"],
            category=self.__plugin_metadata__["category"],
            tags=["preprocess", "image", "opencv"]
        )
    
    def get_ports(self) -> tuple[List[InputPort], List[OutputPort]]:
        """获取输入输出端口"""
        return self._input_ports, self._output_ports
    
    def validate_config(self) -> bool:
        """验证节点配置"""
        try:
            # 验证缩放参数
            if self.config.resize_enabled:
                if self.config.resize_width <= 0 or self.config.resize_height <= 0:
                    return False
            
            # 验证降噪参数
            if self.config.denoise_enabled:
                if self.config.denoise_strength < 0 or self.config.denoise_strength > 100:
                    return False
            
            # 验证锐化参数
            if self.config.sharpen_enabled:
                if self.config.sharpen_strength < 0 or self.config.sharpen_strength > 2.0:
                    return False
            
            # 验证亮度对比度参数
            if not (-100 <= self.config.brightness_adjust <= 100):
                return False
            if not (-100 <= self.config.contrast_adjust <= 100):
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
        执行预处理
        
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
            
            # 执行预处理
            processed_image = await self._process_image(input_data)
            
            # 更新统计
            self.processed_count += 1
            processing_time = asyncio.get_event_loop().time() - start_time
            self.total_processing_time += processing_time
            
            self.state = NodeState.COMPLETED
            
            # 返回结果
            return NodeResult(
                success=True,
                outputs={"image": processed_image},
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
                error=f"预处理失败: {e}",
                metadata={"error_count": self.error_count,
                         "node_id": self.node_id}
            )
    
    async def _process_image(self, input_image: ImageType) -> ImageType:
        """
        执行图像预处理
        
        Args:
            input_image: 输入图像
            
        Returns:
            ImageType: 处理后的图像
        """
        # 获取原始图像数据
        image = input_image.data.copy()  # 复制以避免修改原始数据
        
        # 1. 格式转换
        image = self._convert_image_format(image, input_image)
        
        # 2. 调整大小
        if self.config.resize_enabled:
            image = self._resize_image(image)
        
        # 3. 降噪
        if self.config.denoise_enabled:
            image = self._denoise_image(image)
        
        # 4. 锐化
        if self.config.sharpen_enabled:
            image = self._sharpen_image(image)
        
        # 5. 亮度对比度调整
        if self.config.brightness_adjust != 0 or self.config.contrast_adjust != 0:
            image = self._adjust_brightness_contrast(image)
        
        # 创建输出图像类型
        return ImageType(
            data=image,
            width=image.shape[1],
            height=image.shape[0],
            channels=image.shape[2] if len(image.shape) == 3 else 1,
            format="BGR" if len(image.shape) == 3 else "GRAY"
        )
    
    def _convert_image_format(self, image: np.ndarray, input_image: ImageType) -> np.ndarray:
        """转换图像格式"""
        try:
            # 如果是单通道图像且需要转换为BGR
            if len(image.shape) == 2 and self.config.convert_to_bgr:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            return image
            
        except Exception as e:
            raise NodeExecutionError(f"图像格式转换失败: {e}")
    
    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """调整图像大小"""
        try:
            return cv2.resize(
                image,
                (self.config.resize_width, self.config.resize_height)
            )
        except Exception as e:
            raise NodeExecutionError(f"图像缩放失败: {e}")
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """图像降噪"""
        try:
            if len(image.shape) == 3:  # 彩色图像
                return cv2.fastNlMeansDenoisingColored(
                    image,
                    None,
                    self.config.denoise_strength,
                    self.config.denoise_strength,
                    7,
                    21
                )
            else:  # 灰度图像
                return cv2.fastNlMeansDenoising(
                    image,
                    None,
                    self.config.denoise_strength,
                    7,
                    21
                )
        except Exception as e:
            raise NodeExecutionError(f"图像降噪失败: {e}")
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """图像锐化"""
        try:
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]]) * self.config.sharpen_strength
            return cv2.filter2D(image, -1, kernel)
        except Exception as e:
            raise NodeExecutionError(f"图像锐化失败: {e}")
    
    def _adjust_brightness_contrast(self, image: np.ndarray) -> np.ndarray:
        """调整亮度和对比度"""
        try:
            alpha = 1.0 + self.config.contrast_adjust / 100.0
            beta = self.config.brightness_adjust
            return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        except Exception as e:
            raise NodeExecutionError(f"亮度对比度调整失败: {e}")
    
    async def cleanup(self) -> None:
        """清理资源"""
        # 预处理节点无需特殊清理
        self.state = NodeState.STOPPED
    
    def input_data_processed_hook(self, input_name: str) -> None:
        """输入数据处理完成钩子（用于引用计数）"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        avg_time = (self.total_processing_time / self.processed_count 
                   if self.processed_count > 0 else 0.0)
        
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "average_processing_time": avg_time,
            "total_processing_time": self.total_processing_time,
            "error_rate": self.error_count / max(self.processed_count, 1)
        }
