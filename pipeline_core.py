# -*- coding: utf-8 -*-
"""
管道核心模块
实现管道-过滤器架构的基础设施
"""

import threading
import queue
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from logger_config import get_logger

logger = get_logger("PipelineCore")


# ==================== 数据包定义 ====================
@dataclass
class DataPacket:
    """
    管道中传输的数据包
    包含图像数据和元数据
    """
    # 唯一标识
    packet_id: int
    
    # 时间戳
    timestamp: float = field(default_factory=time.time)
    
    # 图像数据
    image: Any = None           # 原始图像
    processed_image: Any = None # 处理后图像
    
    # 图像信息
    width: int = 0
    height: int = 0
    pixel_format: int = 0
    frame_number: int = 0
    
    # 检测结果
    detections: list = field(default_factory=list)
    
    # 处理信息
    processing_times: Dict[str, float] = field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_processing_time(self, stage_name: str, duration: float):
        """添加处理时间"""
        self.processing_times[stage_name] = duration
    
    def get_total_processing_time(self) -> float:
        """获取总处理时间"""
        return sum(self.processing_times.values())
    
    def __str__(self):
        return (f"DataPacket(id={self.packet_id}, "
                f"frame={self.frame_number}, "
                f"detections={len(self.detections)}, "
                f"time={self.get_total_processing_time():.2f}ms)")


# ==================== 过滤器基类 ====================
class Filter(ABC):
    """
    过滤器基类
    所有处理模块都继承此类
    """
    
    def __init__(self, name: str, config: Any = None):
        """
        初始化过滤器
        
        Args:
            name: 过滤器名称
            config: 配置对象
        """
        self.name = name
        self.config = config
        self.enabled = True
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        
        logger.info(f"[{self.name}] 过滤器初始化")
    
    @abstractmethod
    def process(self, packet: DataPacket) -> Optional[DataPacket]:
        """
        处理数据包（抽象方法，子类必须实现）
        
        Args:
            packet: 输入数据包
            
        Returns:
            处理后的数据包，如果处理失败返回None
        """
        pass
    
    def execute(self, packet: DataPacket) -> Optional[DataPacket]:
        """
        执行处理（包含性能监控和错误处理）
        
        Args:
            packet: 输入数据包
            
        Returns:
            处理后的数据包
        """
        if not self.enabled:
            logger.debug(f"[{self.name}] 过滤器已禁用，跳过处理")
            return packet
        
        try:
            start_time = time.time()
            
            # 调用子类实现的处理方法
            result = self.process(packet)
            
            # 记录处理时间
            duration = (time.time() - start_time) * 1000  # 转换为毫秒
            if result:
                result.add_processing_time(self.name, duration)
            
            # 更新统计
            self.processed_count += 1
            self.total_processing_time += duration
            
            # 记录性能
            if self.processed_count % 100 == 0:
                avg_time = self.total_processing_time / self.processed_count
                logger.debug(f"[{self.name}] 已处理 {self.processed_count} 帧, "
                           f"平均耗时: {avg_time:.2f}ms")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.exception(f"[{self.name}] 处理异常: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_time = (self.total_processing_time / self.processed_count 
                   if self.processed_count > 0 else 0)
        
        return {
            "name": self.name,
            "enabled": self.enabled,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "total_time": self.total_processing_time,
            "average_time": avg_time,
            "error_rate": (self.error_count / self.processed_count * 100 
                          if self.processed_count > 0 else 0)
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        logger.info(f"[{self.name}] 统计信息已重置")


# ==================== 管道类 ====================
class Pipeline:
    """
    管道类
    管理多个过滤器的执行流程
    """
    
    def __init__(self, name: str = "Pipeline", buffer_size: int = 10):
        """
        初始化管道
        
        Args:
            name: 管道名称
            buffer_size: 缓冲区大小
        """
        self.name = name
        self.filters = []
        self.input_queue = queue.Queue(maxsize=buffer_size)
        self.output_queue = queue.Queue(maxsize=buffer_size)
        self.running = False
        self.thread = None
        self.packet_id_counter = 0
        
        logger.info(f"[{self.name}] 管道初始化，缓冲区大小: {buffer_size}")
    
    def add_filter(self, filter_obj: Filter):
        """
        添加过滤器到管道
        
        Args:
            filter_obj: 过滤器对象
        """
        self.filters.append(filter_obj)
        logger.info(f"[{self.name}] 添加过滤器: {filter_obj.name}")
    
    def remove_filter(self, filter_name: str):
        """
        从管道移除过滤器
        
        Args:
            filter_name: 过滤器名称
        """
        self.filters = [f for f in self.filters if f.name != filter_name]
        logger.info(f"[{self.name}] 移除过滤器: {filter_name}")
    
    def start(self):
        """启动管道"""
        if self.running:
            logger.warning(f"[{self.name}] 管道已在运行")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"[{self.name}] 管道已启动")
    
    def stop(self):
        """停止管道"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"[{self.name}] 管道已停止")
    
    def _run(self):
        """管道运行主循环"""
        logger.info(f"[{self.name}] 管道线程启动")
        
        while self.running:
            try:
                # 从输入队列获取数据包（超时1秒）
                packet = self.input_queue.get(timeout=1)
                
                # 依次通过所有过滤器
                for filter_obj in self.filters:
                    if packet is None:
                        break
                    packet = filter_obj.execute(packet)
                
                # 将结果放入输出队列
                if packet is not None:
                    try:
                        self.output_queue.put(packet, timeout=1)
                    except queue.Full:
                        logger.warning(f"[{self.name}] 输出队列已满，丢弃数据包")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.exception(f"[{self.name}] 管道运行异常: {e}")
        
        logger.info(f"[{self.name}] 管道线程退出")
    
    def put(self, packet: DataPacket, timeout: float = 1.0) -> bool:
        """
        向管道输入数据包
        
        Args:
            packet: 数据包
            timeout: 超时时间（秒）
            
        Returns:
            是否成功放入
        """
        try:
            self.input_queue.put(packet, timeout=timeout)
            return True
        except queue.Full:
            logger.warning(f"[{self.name}] 输入队列已满")
            return False
    
    def get(self, timeout: float = 1.0) -> Optional[DataPacket]:
        """
        从管道获取输出数据包
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            数据包，如果超时返回None
        """
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def create_packet(self, **kwargs) -> DataPacket:
        """
        创建新的数据包
        
        Args:
            **kwargs: 数据包参数
            
        Returns:
            数据包对象
        """
        self.packet_id_counter += 1
        return DataPacket(packet_id=self.packet_id_counter, **kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取管道统计信息"""
        stats = {
            "name": self.name,
            "running": self.running,
            "input_queue_size": self.input_queue.qsize(),
            "output_queue_size": self.output_queue.qsize(),
            "filters": [f.get_statistics() for f in self.filters]
        }
        return stats
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print(f"管道统计: {stats['name']}")
        print("=" * 60)
        print(f"运行状态: {'运行中' if stats['running'] else '已停止'}")
        print(f"输入队列: {stats['input_queue_size']}")
        print(f"输出队列: {stats['output_queue_size']}")
        
        print("\n过滤器统计:")
        for f_stats in stats['filters']:
            print(f"\n  [{f_stats['name']}]")
            print(f"    状态: {'启用' if f_stats['enabled'] else '禁用'}")
            print(f"    处理帧数: {f_stats['processed_count']}")
            print(f"    错误次数: {f_stats['error_count']}")
            print(f"    平均耗时: {f_stats['average_time']:.2f}ms")
            print(f"    错误率: {f_stats['error_rate']:.2f}%")
        
        print("=" * 60)


# ==================== 性能监控器 ====================
class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, pipeline: Pipeline, report_interval: float = 10.0):
        """
        初始化性能监控器
        
        Args:
            pipeline: 要监控的管道
            report_interval: 报告间隔（秒）
        """
        self.pipeline = pipeline
        self.report_interval = report_interval
        self.running = False
        self.thread = None
        
        logger.info("性能监控器初始化")
    
    def start(self):
        """启动监控"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        logger.info("性能监控器已启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("性能监控器已停止")
    
    def _monitor(self):
        """监控主循环"""
        while self.running:
            time.sleep(self.report_interval)
            self.pipeline.print_statistics()


if __name__ == "__main__":
    # 测试管道核心模块
    print("管道核心模块测试\n")
    
    # 创建测试过滤器
    class TestFilter(Filter):
        def process(self, packet: DataPacket) -> Optional[DataPacket]:
            # 模拟处理
            time.sleep(0.01)
            packet.metadata[self.name] = "processed"
            return packet
    
    # 创建管道
    pipeline = Pipeline("TestPipeline")
    pipeline.add_filter(TestFilter("Filter1"))
    pipeline.add_filter(TestFilter("Filter2"))
    
    # 启动管道
    pipeline.start()
    
    # 发送测试数据
    for i in range(10):
        packet = pipeline.create_packet(frame_number=i)
        pipeline.put(packet)
    
    # 接收结果
    time.sleep(1)
    for i in range(10):
        result = pipeline.get()
        if result:
            print(f"收到结果: {result}")
    
    # 打印统计
    pipeline.print_statistics()
    
    # 停止管道
    pipeline.stop()
    
    print("\n测试完成")
