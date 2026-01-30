# -*- coding: utf-8 -*-
"""
图像保存节点插件
负责保存图像和检测结果，包含磁盘空间监控

迁移自：service_new/services/storage_service.py
响应任务：任务 15.1 - 创建 ImageWriterNode 插件
新增功能：磁盘空间监控，防止单机环境硬盘写满
"""

import asyncio
import cv2
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import concurrent.futures

from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult, NodeState
from engine.port import InputPort, OutputPort
from core.data_types import ImageType, DetectionListType
from core.exceptions import NodeExecutionError


@dataclass
class ImageWriterConfig:
    """图像保存配置"""
    # 基本保存设置
    save_images: bool = True
    save_path: str = "./output/images"
    save_format: str = "jpg"  # jpg/png/bmp
    jpeg_quality: int = 95
    
    # 保存条件
    save_all_frames: bool = False
    save_interval: int = 10  # 每N帧保存一次
    save_on_detection: bool = True  # 有检测结果时保存
    
    # 检测结果保存
    save_detections: bool = True
    detection_log_path: str = "./output/detections.json"
    detection_batch_size: int = 100  # 批量保存大小
    
    # 磁盘空间管理（新增）
    disk_monitor_enabled: bool = True
    disk_warning_threshold: float = 0.2  # 剩余空间20%时警告
    disk_critical_threshold: float = 0.1  # 剩余空间10%时停止保存
    max_files_count: int = 1000  # 最大文件数量
    max_days_keep: int = 7  # 保留天数
    auto_cleanup_enabled: bool = True  # 自动清理旧文件


class ImageWriterNode(INode):
    """
    图像保存节点
    
    功能：
    - 图像保存（JPG/PNG/BMP）
    - 检测结果保存（JSON）
    - 条件保存（按帧号、检测结果）
    - 磁盘空间监控
    - 自动清理旧文件
    
    新增功能：
    - 磁盘空间实时监控
    - 循环覆盖机制
    - 文件数量限制
    - 按时间自动清理
    """
    
    # 插件元数据
    __plugin_metadata__ = {
        "type": "image_writer",
        "name": "图像保存节点",
        "version": "1.0.0",
        "author": "Kiro AI Assistant",
        "description": "图像和检测结果保存：支持多格式、磁盘监控、自动清理",
        "category": "io",
        "dependencies": ["opencv-python", "numpy"]
    }
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        初始化图像保存节点
        
        Args:
            node_id: 节点ID
            config: 节点配置
        """
        self.node_id = node_id
        self.config = ImageWriterConfig(**config)
        self.state = NodeState.IDLE
        
        # 线程池执行器（用于文件I/O）
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,  # 文件I/O单线程避免竞争
            thread_name_prefix=f"writer_{node_id}"
        )
        
        # 检测结果缓存
        self.detection_log = []
        
        # 统计信息
        self.saved_count = 0
        self.error_count = 0
        self.total_save_time = 0.0
        self.disk_warnings = 0
        self.cleanup_count = 0
        
        # 磁盘状态
        self.disk_space_ok = True
        self.last_disk_check = 0
        
        # 输入端口（无输出端口，终端节点）
        self._input_ports = [
            InputPort("image", ImageType, required=True, description="要保存的图像"),
            InputPort("detections", DetectionListType, required=False, description="检测结果（可选）")
        ]
        self._output_ports = []
    
    def get_metadata(self) -> NodeMetadata:
        """获取节点元数据"""
        return NodeMetadata(
            name=self.__plugin_metadata__["name"],
            version=self.__plugin_metadata__["version"],
            author=self.__plugin_metadata__["author"],
            description=self.__plugin_metadata__["description"],
            category=self.__plugin_metadata__["category"],
            tags=["storage", "image", "save", "disk_monitor"]
        )
    
    def get_ports(self) -> tuple[List[InputPort], List[OutputPort]]:
        """获取输入输出端口"""
        return self._input_ports, self._output_ports
    
    def validate_config(self) -> bool:
        """验证节点配置"""
        try:
            # 验证保存格式
            if self.config.save_format.lower() not in ["jpg", "jpeg", "png", "bmp"]:
                return False
            
            # 验证JPEG质量
            if not (1 <= self.config.jpeg_quality <= 100):
                return False
            
            # 验证保存间隔
            if self.config.save_interval <= 0:
                return False
            
            # 验证磁盘阈值
            if not (0.0 <= self.config.disk_critical_threshold <= self.config.disk_warning_threshold <= 1.0):
                return False
            
            # 验证文件数量和天数
            if self.config.max_files_count <= 0 or self.config.max_days_keep <= 0:
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
            
            # 创建保存目录
            if self.config.save_images:
                os.makedirs(self.config.save_path, exist_ok=True)
            
            # 创建检测结果目录
            if self.config.save_detections:
                detection_dir = os.path.dirname(self.config.detection_log_path)
                if detection_dir:
                    os.makedirs(detection_dir, exist_ok=True)
            
            # 初始磁盘检查
            if self.config.disk_monitor_enabled:
                await self._check_disk_space()
            
            self.state = NodeState.IDLE
            return True
            
        except Exception as e:
            self.state = NodeState.ERROR
            raise NodeExecutionError(f"节点 {self.node_id} 初始化失败: {e}")
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        """
        执行图像保存
        
        Args:
            context: 执行上下文，包含输入数据
            
        Returns:
            NodeResult: 保存结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.state = NodeState.RUNNING
            
            # 获取输入数据
            input_image = context.inputs.get("image")
            detections = context.inputs.get("detections")
            
            if input_image is None:
                raise NodeExecutionError("缺少输入图像")
            
            # 验证输入类型
            if not isinstance(input_image, ImageType):
                raise NodeExecutionError(f"输入数据类型错误，期望 ImageType，得到 {type(input_image)}")
            
            # 检查磁盘空间
            if self.config.disk_monitor_enabled:
                await self._check_disk_space()
            
            # 判断是否需要保存
            should_save = await self._should_save_image(detections, context)
            
            save_result = {}
            
            # 在线程池中执行保存操作
            if should_save and self.disk_space_ok:
                loop = asyncio.get_event_loop()
                save_result = await loop.run_in_executor(
                    self.executor,
                    self._save_data,
                    input_image,
                    detections,
                    context
                )
            
            # 更新统计
            if save_result.get('image_saved', False):
                self.saved_count += 1
            
            save_time = asyncio.get_event_loop().time() - start_time
            self.total_save_time += save_time
            
            self.state = NodeState.COMPLETED
            
            # 返回结果
            return NodeResult(
                success=True,
                outputs={},  # 终端节点无输出
                metadata={"save_time": save_time,
                         "image_saved": save_result.get('image_saved', False),
                         "detection_saved": save_result.get('detection_saved', False),
                         "disk_space_ok": self.disk_space_ok,
                         "saved_count": self.saved_count,
                         "node_id": self.node_id}
            )
            
        except Exception as e:
            self.error_count += 1
            self.state = NodeState.ERROR
            
            return NodeResult(
                success=False,
                outputs={},
                error=f"图像保存失败: {e}",
                metadata={"error_count": self.error_count,
                         "node_id": self.node_id}
            )
    
    async def _should_save_image(self, detections: Optional[DetectionListType], context: ExecutionContext) -> bool:
        """判断是否应该保存图像"""
        # 获取帧号（从上下文或元数据中）
        frame_number = context.metadata.get('frame_number', 0)
        
        # 保存所有帧
        if self.config.save_all_frames:
            return True
        
        # 按间隔保存
        if frame_number % self.config.save_interval == 0:
            return True
        
        # 有检测结果时保存
        if (self.config.save_on_detection and 
            detections is not None and 
            len(detections.detections) > 0):
            return True
        
        return False
    
    def _save_data(self, image: ImageType, detections: Optional[DetectionListType], context: ExecutionContext) -> Dict[str, bool]:
        """
        保存数据（在线程池中执行）
        
        Args:
            image: 图像数据
            detections: 检测结果
            context: 执行上下文
            
        Returns:
            保存结果字典
        """
        result = {"image_saved": False, "detection_saved": False}
        
        try:
            # 保存图像
            if self.config.save_images:
                result["image_saved"] = self._save_image(image, context)
            
            # 保存检测结果
            if self.config.save_detections and detections is not None:
                result["detection_saved"] = self._save_detection(detections, context)
            
            # 自动清理
            if self.config.auto_cleanup_enabled:
                self._auto_cleanup()
            
            return result
            
        except Exception as e:
            raise NodeExecutionError(f"数据保存执行失败: {e}")
    
    def _save_image(self, image: ImageType, context: ExecutionContext) -> bool:
        """保存图像文件"""
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            frame_number = context.metadata.get('frame_number', 0)
            filename = f"frame_{frame_number}_{timestamp}.{self.config.save_format}"
            filepath = os.path.join(self.config.save_path, filename)
            
            # 保存图像
            if self.config.save_format.lower() in ['jpg', 'jpeg']:
                success = cv2.imwrite(
                    filepath,
                    image.data,
                    [cv2.IMWRITE_JPEG_QUALITY, self.config.jpeg_quality]
                )
            else:
                success = cv2.imwrite(filepath, image.data)
            
            if success:
                print(f"保存图像: {filename}")
                return True
            else:
                print(f"保存图像失败: {filename}")
                return False
                
        except Exception as e:
            print(f"保存图像异常: {e}")
            return False
    
    def _save_detection(self, detections: DetectionListType, context: ExecutionContext) -> bool:
        """保存检测结果"""
        try:
            # 构建检测记录
            detection_record = {
                'frame_number': context.metadata.get('frame_number', 0),
                'timestamp': datetime.now().isoformat(),
                'detection_count': len(detections.detections),
                'detections': []
            }
            
            # 转换检测结果
            for detection in detections.detections:
                detection_dict = {
                    'bbox': [detection.x, detection.y, detection.width, detection.height],
                    'confidence': detection.confidence,
                    'class_id': detection.class_id,
                    'class_name': detection.class_name
                }
                detection_record['detections'].append(detection_dict)
            
            # 添加到缓存
            self.detection_log.append(detection_record)
            
            # 批量保存
            if len(self.detection_log) >= self.config.detection_batch_size:
                self._flush_detection_log()
            
            return True
            
        except Exception as e:
            print(f"保存检测结果异常: {e}")
            return False
    
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
            
            print(f"保存 {len(self.detection_log)} 条检测记录")
            self.detection_log = []
            
        except Exception as e:
            print(f"刷新检测日志异常: {e}")
    
    async def _check_disk_space(self):
        """检查磁盘空间"""
        try:
            current_time = asyncio.get_event_loop().time()
            
            # 每10秒检查一次
            if current_time - self.last_disk_check < 10:
                return
            
            self.last_disk_check = current_time
            
            # 获取磁盘使用情况
            total, used, free = shutil.disk_usage(self.config.save_path)
            free_ratio = free / total
            
            # 检查阈值
            if free_ratio < self.config.disk_critical_threshold:
                self.disk_space_ok = False
                self.disk_warnings += 1
                print(f"磁盘空间严重不足: {free_ratio:.1%}，停止保存")
            elif free_ratio < self.config.disk_warning_threshold:
                self.disk_space_ok = True
                self.disk_warnings += 1
                print(f"磁盘空间不足警告: {free_ratio:.1%}")
            else:
                self.disk_space_ok = True
            
        except Exception as e:
            print(f"磁盘空间检查失败: {e}")
    
    def _auto_cleanup(self):
        """自动清理旧文件"""
        try:
            if not os.path.exists(self.config.save_path):
                return
            
            # 获取所有图像文件
            files = []
            for filename in os.listdir(self.config.save_path):
                filepath = os.path.join(self.config.save_path, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append((filepath, stat.st_mtime))
            
            # 按修改时间排序（最旧的在前）
            files.sort(key=lambda x: x[1])
            
            # 检查文件数量限制
            if len(files) > self.config.max_files_count:
                files_to_delete = files[:len(files) - self.config.max_files_count]
                for filepath, _ in files_to_delete:
                    os.remove(filepath)
                    self.cleanup_count += 1
                
                print(f"清理 {len(files_to_delete)} 个旧文件（数量限制）")
            
            # 检查时间限制
            current_time = datetime.now().timestamp()
            max_age = self.config.max_days_keep * 24 * 3600  # 转换为秒
            
            old_files = [f for f in files if current_time - f[1] > max_age]
            for filepath, _ in old_files:
                if os.path.exists(filepath):  # 可能已被数量限制删除
                    os.remove(filepath)
                    self.cleanup_count += 1
            
            if old_files:
                print(f"清理 {len(old_files)} 个过期文件（时间限制）")
                
        except Exception as e:
            print(f"自动清理失败: {e}")
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 保存剩余的检测记录
            if self.detection_log:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, self._flush_detection_log)
            
            # 关闭线程池
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            
            self.state = NodeState.STOPPED
            
        except Exception as e:
            print(f"图像保存节点清理失败: {e}")
    
    def input_data_processed_hook(self, input_name: str) -> None:
        """输入数据处理完成钩子（用于引用计数）"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        avg_time = (self.total_save_time / self.saved_count 
                   if self.saved_count > 0 else 0.0)
        
        return {
            "saved_count": self.saved_count,
            "error_count": self.error_count,
            "cleanup_count": self.cleanup_count,
            "disk_warnings": self.disk_warnings,
            "average_save_time": avg_time,
            "total_save_time": self.total_save_time,
            "error_rate": self.error_count / max(self.saved_count, 1),
            "disk_space_ok": self.disk_space_ok,
            "detection_log_size": len(self.detection_log),
            "config": {
                "save_format": self.config.save_format,
                "save_path": self.config.save_path,
                "disk_monitor_enabled": self.config.disk_monitor_enabled,
                "auto_cleanup_enabled": self.config.auto_cleanup_enabled
            }
        }
