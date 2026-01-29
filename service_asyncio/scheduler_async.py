# -*- coding: utf-8 -*-
"""
异步调度器模块
负责管理和调度整个异步管道系统
支持多相机并发处理
"""

import sys
import os
import asyncio

# 添加service_new根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
service_new_root = os.path.dirname(current_dir)
if service_new_root not in sys.path:
    sys.path.insert(0, service_new_root)

from pipeline_core_async import AsyncPipeline, AsyncPerformanceMonitor
from pipeline_config import get_config
from camera_service_async import MultiCameraManager
from services_async import *
from logger_config import get_logger

logger = get_logger("AsyncScheduler")


class AsyncPipelineScheduler:
    """
    异步管道调度器
    负责初始化、启动、停止整个异步管道系统
    支持多相机并发处理
    """
    
    def __init__(self, config=None):
        """
        初始化调度器
        
        Args:
            config: PipelineConfig配置对象
        """
        self.config = config if config else get_config()
        self.pipeline = None
        self.camera_manager = None
        self.performance_monitor = None
        self.running = False
        
        logger.info("=" * 60)
        logger.info("异步管道调度器初始化")
        logger.info("=" * 60)
    
    def initialize(self):
        """初始化管道和所有服务"""
        try:
            logger.info("开始初始化异步管道系统...")
            
            # 验证配置
            self.config.validate()
            self.config.print_config()
            
            # 创建异步管道
            self.pipeline = AsyncPipeline(
                name="AsyncVisionPipeline",
                buffer_size=self.config.pipeline_buffer_size
            )
            
            # 初始化多相机管理器
            if self.config.camera_service.enabled:
                self.camera_manager = MultiCameraManager(self.config.camera_service)
                logger.info("✓ 多相机管理器初始化完成")
            
            # 添加预处理服务
            if self.config.preprocess_service.enabled:
                preprocess = AsyncPreprocessService(self.config.preprocess_service)
                self.pipeline.add_filter(preprocess)
                logger.info("✓ 异步预处理服务已添加")
            
            # 添加YOLO检测服务
            if self.config.yolo_service.enabled:
                yolo = AsyncYOLOService(self.config.yolo_service)
                self.pipeline.add_filter(yolo)
                logger.info("✓ 异步YOLO服务已添加")
            
            # 添加OpenCV处理服务
            if self.config.opencv_service.enabled:
                opencv = AsyncOpenCVService(self.config.opencv_service)
                self.pipeline.add_filter(opencv)
                logger.info("✓ 异步OpenCV服务已添加")
            
            # 添加显示服务
            if self.config.display_service.enabled:
                display = AsyncDisplayService(self.config.display_service)
                self.pipeline.add_filter(display)
                logger.info("✓ 异步显示服务已添加")
            
            # 添加存储服务
            if self.config.storage_service.enabled:
                storage = AsyncStorageService(self.config.storage_service)
                self.pipeline.add_filter(storage)
                logger.info("✓ 异步存储服务已添加")
            
            # 创建性能监控器
            if self.config.enable_performance_monitor:
                self.performance_monitor = AsyncPerformanceMonitor(
                    self.pipeline,
                    self.config.performance_report_interval
                )
                logger.info("✓ 异步性能监控器已创建")
            
            logger.info("异步管道系统初始化完成")
            return True
            
        except Exception as e:
            logger.exception(f"初始化失败: {e}")
            return False
    
    async def start(self):
        """启动异步管道系统"""
        try:
            if self.running:
                logger.warning("系统已在运行")
                return False
            
            logger.info("=" * 60)
            logger.info("启动异步管道系统")
            logger.info("=" * 60)
            
            # 启动相机
            if self.camera_manager:
                # 枚举设备
                device_count = self.camera_manager.enumerate_devices()
                if device_count == 0:
                    logger.error("未找到相机设备")
                    return False
                
                # 打开所有设备
                if not self.camera_manager.open_all_cameras():
                    logger.error("打开相机失败")
                    return False
                
                # 开始采集
                if not self.camera_manager.start_all_cameras():
                    logger.error("开始采集失败")
                    return False
            
            # 启动管道
            await self.pipeline.start()
            
            # 启动性能监控
            if self.performance_monitor:
                await self.performance_monitor.start()
            
            self.running = True
            
            logger.info("异步管道系统启动成功")
            logger.info("按 Ctrl+C 停止系统")
            
            return True
            
        except Exception as e:
            logger.exception(f"启动失败: {e}")
            return False
    
    async def _camera_loop(self):
        """相机采集循环（异步）"""
        logger.info("异步相机采集循环启动")
        
        frame_count = 0
        max_frames = self.config.camera_service.max_frames
        
        while self.running:
            try:
                # 从所有相机并发采集图像
                packets = await self.camera_manager.grab_from_all_cameras()
                
                # 将所有数据包送入管道
                for packet in packets:
                    if packet:
                        await self.pipeline.put(packet, timeout=0.1)
                        frame_count += 1
                
                # 检查最大帧数
                if max_frames > 0 and frame_count >= max_frames:
                    logger.info(f"已达到最大帧数 {max_frames}")
                    self.running = False
                    break
                
                # 短暂休眠，避免CPU占用过高
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.exception(f"采集循环异常: {e}")
        
        logger.info("异步相机采集循环退出")
    
    async def stop(self):
        """停止异步管道系统"""
        try:
            if not self.running:
                return
            
            logger.info("=" * 60)
            logger.info("停止异步管道系统")
            logger.info("=" * 60)
            
            # 停止采集循环
            self.running = False
            
            # 停止性能监控
            if self.performance_monitor:
                await self.performance_monitor.stop()
            
            # 停止管道
            if self.pipeline:
                await self.pipeline.stop()
            
            # 停止相机
            if self.camera_manager:
                self.camera_manager.stop_all_cameras()
                self.camera_manager.close_all_cameras()
            
            # 打印最终统计
            if self.pipeline:
                self.pipeline.print_statistics()
            
            logger.info("异步管道系统已停止")
            
        except Exception as e:
            logger.exception(f"停止异常: {e}")
    
    async def run(self):
        """运行异步管道系统"""
        if not self.initialize():
            logger.error("初始化失败，退出")
            return
        
        if not await self.start():
            logger.error("启动失败，退出")
            return
        
        try:
            # 运行相机采集循环
            await self._camera_loop()
        except KeyboardInterrupt:
            logger.info("收到中断信号 (Ctrl+C)")
        except Exception as e:
            logger.exception(f"运行异常: {e}")
        finally:
            await self.stop()


if __name__ == "__main__":
    # 测试异步调度器
    from pipeline_config import PresetConfigs
    
    # 使用开发模式配置
    config = PresetConfigs.development()
    
    # 创建调度器
    scheduler = AsyncPipelineScheduler(config)
    
    # 运行
    asyncio.run(scheduler.run())
