# -*- coding: utf-8 -*-
"""
YOLO目标检测节点插件
负责使用YOLO模型进行目标检测

迁移自：service_new/services/yolo_service.py
响应任务：任务 13.1 - 创建 YoloInferenceNode 插件
关键优化：使用 run_in_executor 避免 GIL 阻塞
"""

import asyncio
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import concurrent.futures

from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult, NodeState
from engine.port import InputPort, OutputPort
from core.data_types import ImageType, DetectionListType, BBoxType
from core.exceptions import NodeExecutionError


@dataclass
class YoloConfig:
    """YOLO配置"""
    model_path: str = "./models/yolov8n.pt"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    max_detections: int = 100
    device: str = "cpu"  # cpu/cuda
    
    # 性能优化
    use_half_precision: bool = False
    batch_size: int = 1


class YoloInferenceNode(INode):
    """
    YOLO目标检测节点
    
    功能：
    - YOLO模型加载（YOLOv8/YOLOv5）
    - 目标检测推理
    - 检测结果解析和过滤
    - 标注图像生成
    
    性能优化：
    - 使用 run_in_executor 避免 GIL 阻塞
    - 支持 GPU 加速
    - 支持半精度推理
    """
    
    # 插件元数据
    __plugin_metadata__ = {
        "type": "yolo_v8",
        "name": "YOLO目标检测节点",
        "version": "1.0.0",
        "author": "Kiro AI Assistant",
        "description": "YOLO目标检测：支持YOLOv8/YOLOv5，GPU加速，实时推理",
        "category": "algo",
        "dependencies": ["ultralytics", "torch", "torchvision", "opencv-python", "numpy"]
    }
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        初始化YOLO节点
        
        Args:
            node_id: 节点ID
            config: 节点配置
        """
        self.node_id = node_id
        self.config = YoloConfig(**config)
        self.state = NodeState.IDLE
        
        # YOLO模型
        self.model = None
        self.model_loaded = False
        
        # 线程池执行器（用于CPU密集任务）
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,  # YOLO推理通常单线程更稳定
            thread_name_prefix=f"yolo_{node_id}"
        )
        
        # 统计信息
        self.inference_count = 0
        self.error_count = 0
        self.total_inference_time = 0.0
        self.detection_count = 0
        
        # 输入输出端口
        self._input_ports = [
            InputPort("image", ImageType, required=True, description="输入图像")
        ]
        self._output_ports = [
            OutputPort("detections", DetectionListType, description="检测结果列表"),
            OutputPort("annotated_image", ImageType, description="标注后的图像")
        ]
    
    def get_metadata(self) -> NodeMetadata:
        """获取节点元数据"""
        return NodeMetadata(
            name=self.__plugin_metadata__["name"],
            version=self.__plugin_metadata__["version"],
            author=self.__plugin_metadata__["author"],
            description=self.__plugin_metadata__["description"],
            category=self.__plugin_metadata__["category"],
            tags=["yolo", "detection", "ai", "computer_vision"]
        )
    
    def get_ports(self) -> tuple[List[InputPort], List[OutputPort]]:
        """获取输入输出端口"""
        return self._input_ports, self._output_ports
    
    def validate_config(self) -> bool:
        """验证节点配置"""
        try:
            # 验证置信度阈值
            if not (0.0 <= self.config.confidence_threshold <= 1.0):
                return False
            
            # 验证IoU阈值
            if not (0.0 <= self.config.iou_threshold <= 1.0):
                return False
            
            # 验证最大检测数
            if self.config.max_detections <= 0:
                return False
            
            # 验证设备
            if self.config.device not in ["cpu", "cuda", "mps"]:
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
            
            # 在线程池中加载模型（避免阻塞主线程）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self._load_model)
            
            if not self.model_loaded:
                raise NodeExecutionError(f"节点 {self.node_id} 模型加载失败")
            
            self.state = NodeState.IDLE
            return True
            
        except Exception as e:
            self.state = NodeState.ERROR
            raise NodeExecutionError(f"节点 {self.node_id} 初始化失败: {e}")
    
    def _load_model(self):
        """加载YOLO模型（在线程池中执行）"""
        try:
            # 尝试导入ultralytics（YOLOv8）
            try:
                from ultralytics import YOLO
                
                # 加载模型
                self.model = YOLO(self.config.model_path)
                
                # 配置设备
                if self.config.device == "cuda":
                    import torch
                    if torch.cuda.is_available():
                        self.model.to("cuda")
                    else:
                        print(f"CUDA不可用，使用CPU")
                        self.config.device = "cpu"
                
                # 配置半精度
                if self.config.use_half_precision and self.config.device == "cuda":
                    self.model.half()
                
                self.model_loaded = True
                print(f"YOLOv8模型加载成功: {self.config.model_path}")
                
            except ImportError as e:
                raise NodeExecutionError(f"ultralytics未安装: {e}")
                
        except Exception as e:
            self.model_loaded = False
            raise NodeExecutionError(f"加载YOLO模型失败: {e}")
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        """
        执行YOLO推理
        
        Args:
            context: 执行上下文，包含输入数据
            
        Returns:
            NodeResult: 包含检测结果和标注图像
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
            
            # 在线程池中执行推理（避免GIL阻塞）
            loop = asyncio.get_event_loop()
            detections, annotated_image = await loop.run_in_executor(
                self.executor, 
                self._infer, 
                input_data
            )
            
            # 更新统计
            self.inference_count += 1
            self.detection_count += len(detections.detections)
            inference_time = asyncio.get_event_loop().time() - start_time
            self.total_inference_time += inference_time
            
            self.state = NodeState.COMPLETED
            
            # 返回结果
            return NodeResult(
                success=True,
                outputs={
                    "detections": detections,
                    "annotated_image": annotated_image
                },
                metadata={"inference_time": inference_time,
                         "detection_count": len(detections.detections),
                         "inference_count": self.inference_count,
                         "node_id": self.node_id}
            )
            
        except Exception as e:
            self.error_count += 1
            self.state = NodeState.ERROR
            
            return NodeResult(
                success=False,
                outputs={},
                error=f"YOLO推理失败: {e}",
                metadata={"error_count": self.error_count,
                         "node_id": self.node_id}
            )
    
    def _infer(self, input_image: ImageType) -> tuple[DetectionListType, ImageType]:
        """
        执行YOLO推理（在线程池中执行）
        
        Args:
            input_image: 输入图像
            
        Returns:
            tuple: (检测结果, 标注图像)
        """
        if not self.model_loaded or self.model is None:
            raise NodeExecutionError("YOLO模型未加载")
        
        try:
            # 获取图像数据
            image = input_image.data
            
            # 执行推理
            results = self.model.predict(
                image,
                conf=self.config.confidence_threshold,
                iou=self.config.iou_threshold,
                max_det=self.config.max_detections,
                verbose=False,
                device=self.config.device
            )
            
            # 解析检测结果
            detections = []
            annotated_image = image.copy()
            
            if len(results) > 0:
                result = results[0]
                
                # 获取检测框
                if result.boxes is not None:
                    boxes = result.boxes
                    
                    for i, box in enumerate(boxes):
                        # 提取边界框坐标 [x1, y1, x2, y2]
                        xyxy = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id]
                        
                        # 转换为 [x, y, w, h] 格式
                        x1, y1, x2, y2 = xyxy
                        x, y, w, h = x1, y1, x2 - x1, y2 - y1
                        
                        # 创建检测对象
                        detection = BBoxType(
                            x=float(x), y=float(y), 
                            width=float(w), height=float(h),
                            confidence=confidence,
                            class_id=class_id,
                            class_name=class_name
                        )
                        detections.append(detection)
                        
                        # 在图像上绘制检测框
                        annotated_image = self._draw_detection(
                            annotated_image, detection
                        )
            
            # 创建检测结果列表
            detection_list = DetectionListType(detections=detections)
            
            # 创建标注图像
            annotated_image_type = ImageType(
                data=annotated_image,
                width=annotated_image.shape[1],
                height=annotated_image.shape[0],
                channels=annotated_image.shape[2] if len(annotated_image.shape) == 3 else 1,
                format=input_image.format
            )
            
            return detection_list, annotated_image_type
            
        except Exception as e:
            raise NodeExecutionError(f"YOLO推理执行失败: {e}")
    
    def _draw_detection(self, image: np.ndarray, detection: BBoxType) -> np.ndarray:
        """
        在图像上绘制检测框
        
        Args:
            image: 输入图像
            detection: 检测结果
            
        Returns:
            绘制后的图像
        """
        try:
            # 计算边界框坐标
            x1 = int(detection.x)
            y1 = int(detection.y)
            x2 = int(detection.x + detection.width)
            y2 = int(detection.y + detection.height)
            
            # 绘制边界框
            color = (0, 255, 0)  # 绿色
            thickness = 2
            cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
            
            # 绘制标签
            label = f"{detection.class_name}: {detection.confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            
            # 标签背景
            cv2.rectangle(
                image, 
                (x1, y1 - label_size[1] - 10), 
                (x1 + label_size[0], y1), 
                color, 
                -1
            )
            
            # 标签文字
            cv2.putText(
                image, 
                label, 
                (x1, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (255, 255, 255), 
                1
            )
            
            return image
            
        except Exception as e:
            # 绘制失败不影响主流程
            print(f"绘制检测框失败: {e}")
            return image
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 关闭线程池
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            
            # 释放模型内存
            if self.model is not None:
                del self.model
                self.model = None
            
            # 清理GPU内存
            if self.config.device == "cuda":
                try:
                    import torch
                    torch.cuda.empty_cache()
                except ImportError:
                    pass
            
            self.model_loaded = False
            self.state = NodeState.STOPPED
            
        except Exception as e:
            print(f"YOLO节点清理失败: {e}")
    
    def input_data_processed_hook(self, input_name: str) -> None:
        """输入数据处理完成钩子（用于引用计数）"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        avg_time = (self.total_inference_time / self.inference_count 
                   if self.inference_count > 0 else 0.0)
        
        avg_detections = (self.detection_count / self.inference_count 
                         if self.inference_count > 0 else 0.0)
        
        return {
            "inference_count": self.inference_count,
            "error_count": self.error_count,
            "detection_count": self.detection_count,
            "average_inference_time": avg_time,
            "average_detections_per_frame": avg_detections,
            "total_inference_time": self.total_inference_time,
            "error_rate": self.error_count / max(self.inference_count, 1),
            "model_loaded": self.model_loaded,
            "device": self.config.device
        }
