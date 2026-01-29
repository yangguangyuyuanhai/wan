# -*- coding: utf-8 -*-
"""
异步管道核心模块
实现基于 asyncio 的管道-过滤器架构，支持多相机并发处理
"""

import sys
import os
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

# 添加service_new根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
service_new_root = os.path.dirname(current_dir)
if service_new_root not in sys.path:
    sys.path.insert(0, service_new_root)

from logger_config import get_logger

logger = get_logger("AsyncPipelineCore")


# ==================== 数据包定义 ====================
@dataclass
class DataPacket:
    """
    管道中传输的数据包
    包含图像数据和元数据
    """
    # 唯一标识
    packet_id: int
    
    # 相机标识
    camera_id: str = "camera_0"
    
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
                f"camera={self.camera_id}, "
                f"frame={self.frame_number}, "
                f"detections={len(self.detections)}, "
                f"time={self.get_total_processing_time():.2f}ms)")


# ==================== 异步过滤器基类 ====================
class AsyncFilter(ABC):
    """
    异步过滤器基类
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
        
        logger.info(f"[{self.name}] 异步过滤器初始化")
    
    @abstractmethod
    async def process(self, packet: DataPacket) -> Optional[DataPacket]:
        """
        异步处理数据包（抽象方法，子类必须实现）
        
        Args:
            packet: 输入数据包
            
        Returns:
            处理后的数据包，如果处理失败返回None
        """
        pass
    
    async def execute(self, packet: DataPacket) -> Optional[DataPacket]:
        """
        执行异步处理（包含性能监控和错误处理）
        
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
            
            # 调用子类实现的异步处理方法
            result = await self.process(packet)
            
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


# ==================== 异步管道类 ====================
class AsyncPipeline:
    """
    异步管道类
    管理多个过滤器的异步执行流程
    支持多相机并发处理
    """
    
    def __init__(self, name: str = "AsyncPipeline", buffer_size: int = 100):
        """
        初始化异步管道
        
        Args:
            name: 管道名称
            buffer_size: 缓冲区大小
        """
        self.name = name
        self.filters: List[AsyncFilter] = []
        self.input_queue = asyncio.Queue(maxsize=buffer_size)
        self.output_queue = asyncio.Queue(maxsize=buffer_size)
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.packet_id_counter = 0
        self.worker_count = 4  # 并发工作协程数量
        
        logger.info(f"[{self.name}] 异步管道初始化，缓冲区大小: {buffer_size}, 工作协程: {self.worker_count}")
    
    def add_filter(self, filter_obj: AsyncFilter):
        """
        添加过滤器到管道
        
        Args:
            filter_obj: 过滤器对象
        """
        self.filters.append(filter_obj)
        logger.info(f"[{self.name}] 添加异步过滤器: {filter_obj.name}")
    
    def remove_filter(self, filter_name: str):
        """
        从管道移除过滤器
        
        Args:
            filter_name: 过滤器名称
        """
        self.filters = [f for f in self.filters if f.name != filter_name]
        logger.info(f"[{self.name}] 移除过滤器: {filter_name}")
    
    async def start(self):
        """启动异步管道"""
        if self.running:
            logger.warning(f"[{self.name}] 管道已在运行")
            return
        
        self.running = True
        
        # 启动多个工作协程
        for i in range(self.worker_count):
            task = asyncio.create_task(self._worker(i))
            self.tasks.append(task)
        
        logger.info(f"[{self.name}] 异步管道已启动，{self.worker_count} 个工作协程")
    
    async def stop(self):
        """停止异步管道"""
        if not self.running:
            return
        
        self.running = False
        
        # 等待所有任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            self.tasks.clear()
        
        logger.info(f"[{self.name}] 异步管道已停止")
    
    async def _worker(self, worker_id: int):
        """
        工作协程
        
        Args:
            worker_id: 工作协程ID
        """
        logger.info(f"[{self.name}] 工作协程 {worker_id} 启动")
        
        while self.running:
            try:
                # 从输入队列获取数据包（超时1秒）
                try:
                    packet = await asyncio.wait_for(
                        self.input_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 依次通过所有过滤器（异步）
                for filter_obj in self.filters:
                    if packet is None:
                        break
                    packet = await filter_obj.execute(packet)
                
                # 将结果放入输出队列
                if packet is not None:
                    try:
                        await asyncio.wait_for(
                            self.output_queue.put(packet),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"[{self.name}] 输出队列已满，丢弃数据包")
                
            except Exception as e:
                logger.exception(f"[{self.name}] 工作协程 {worker_id} 异常: {e}")
        
        logger.info(f"[{self.name}] 工作协程 {worker_id} 退出")
    
    async def put(self, packet: DataPacket, timeout: float = 1.0) -> bool:
        """
        向管道输入数据包（异步）
        
        Args:
            packet: 数据包
            timeout: 超时时间（秒）
            
        Returns:
            是否成功放入
        """
        try:
            await asyncio.wait_for(
                self.input_queue.put(packet),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] 输入队列已满")
            return False
    
    async def get(self, timeout: float = 1.0) -> Optional[DataPacket]:
        """
        从管道获取输出数据包（异步）
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            数据包，如果超时返回None
        """
        try:
            return await asyncio.wait_for(
                self.output_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None
    
    def create_packet(self, camera_id: str = "camera_0", **kwargs) -> DataPacket:
        """
        创建新的数据包
        
        Args:
            camera_id: 相机ID
            **kwargs: 数据包参数
            
        Returns:
            数据包对象
        """
        self.packet_id_counter += 1
        return DataPacket(
            packet_id=self.packet_id_counter,
            camera_id=camera_id,
            **kwargs
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取管道统计信息"""
        stats = {
            "name": self.name,
            "running": self.running,
            "input_queue_size": self.input_queue.qsize(),
            "output_queue_size": self.output_queue.qsize(),
            "worker_count": self.worker_count,
            "filters": [f.get_statistics() for f in self.filters]
        }
        return stats
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print(f"异步管道统计: {stats['name']}")
        print("=" * 60)
        print(f"运行状态: {'运行中' if stats['running'] else '已停止'}")
        print(f"输入队列: {stats['input_queue_size']}")
        print(f"输出队列: {stats['output_queue_size']}")
        print(f"工作协程: {stats['worker_count']}")
        
        print("\n过滤器统计:")
        for f_stats in stats['filters']:
            print(f"\n  [{f_stats['name']}]")
            print(f"    状态: {'启用' if f_stats['enabled'] else '禁用'}")
            print(f"    处理帧数: {f_stats['processed_count']}")
            print(f"    错误次数: {f_stats['error_count']}")
            print(f"    平均耗时: {f_stats['average_time']:.2f}ms")
            print(f"    错误率: {f_stats['error_rate']:.2f}%")
        
        print("=" * 60)


# ==================== 异步性能监控器 ====================
class AsyncPerformanceMonitor:
    """异步性能监控器"""
    
    def __init__(self, pipeline: AsyncPipeline, report_interval: float = 10.0):
        """
        初始化性能监控器
        
        Args:
            pipeline: 要监控的管道
            report_interval: 报告间隔（秒）
        """
        self.pipeline = pipeline
        self.report_interval = report_interval
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        logger.info("异步性能监控器初始化")
    
    async def start(self):
        """启动监控"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor())
        logger.info("异步性能监控器已启动")
    
    async def stop(self):
        """停止监控"""
        self.running = False
        if self.task:
            await self.task
        logger.info("异步性能监控器已停止")
    
    async def _monitor(self):
        """监控主循环"""
        while self.running:
            await asyncio.sleep(self.report_interval)
            self.pipeline.print_statistics()


if __name__ == "__main__":
    # 测试异步管道核心模块
    print("异步管道核心模块测试\n")
    
    # 创建测试过滤器
    class TestAsyncFilter(AsyncFilter):
        async def process(self, packet: DataPacket) -> Optional[DataPacket]:
            # 模拟异步处理
            await asyncio.sleep(0.01)
            packet.metadata[self.name] = "processed"
            return packet
    
    async def test_pipeline():
        # 创建管道
        pipeline = AsyncPipeline("TestPipeline")
        pipeline.add_filter(TestAsyncFilter("Filter1"))
        pipeline.add_filter(TestAsyncFilter("Filter2"))
        
        # 启动管道
        await pipeline.start()
        
        # 发送测试数据
        for i in range(10):
            packet = pipeline.create_packet(camera_id=f"camera_{i%2}", frame_number=i)
            await pipeline.put(packet)
        
        # 接收结果
        await asyncio.sleep(1)
        for i in range(10):
            result = await pipeline.get()
            if result:
                print(f"收到结果: {result}")
        
        # 打印统计
        pipeline.print_statistics()
        
        # 停止管道
        await pipeline.stop()
    
    # 运行测试
    asyncio.run(test_pipeline())
    
    print("\n测试完成")
