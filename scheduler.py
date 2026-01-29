# -*- coding: utf-8 -*-
"""
调度器模块
负责管理和调度整个管道系统
"""

import time
import threading
from pipeline_core import Pipeline, PerformanceMonitor
from pipeline_config import get_config
from services import *
from logger_config import get_logger

logger = get_logger("Scheduler")


class PipelineScheduler:
    """
    管道调度器
    负责初始化、启动、停止整个管道系统
    """
    
    def __init__(self, config=None):
        """
        初始化调度器
        
        Args:
            config: PipelineConfig配置对象
        """
        self.config = config if config else get_config()
        self.pipeline = None
        self.camera_service = None
        self.performance_monitor = None
        self.running = False
        self.camera_thread = None
        
        logger.info("=" * 60)
        logger.info("管道调度器初始化")
        logger.info("=" * 60)
    
    def initialize(self):
        """初始化管道和所有服务"""
        try:
            logger.info("开始初始化管道系统...")
            
            # 验证配置
            self.config.validate()
            self.config.print_config()
            
            # 创建管道
            self.pipeline = Pipeline(
                name="VisionPipeline",
                buffer_size=self.config.pipeline_buffer_size
            )
            
            # 初始化相机服务（作为数据源，不加入管道）
            if self.config.camera_service.enabled:
                self.camera_service = CameraService(self.config.camera_service)
                logger.info("✓ 相机服务初始化完成")
            
            # 添加预处理服务
            if self.config.preprocess_service.enabled:
                preprocess = PreprocessService(self.config.preprocess_service)
                self.pipeline.add_filter(preprocess)
                logger.info("✓ 预处理服务已添加")
            
            # 添加YOLO检测服务
            if self.config.yolo_service.enabled:
                yolo = YOLOService(self.config.yolo_service)
                self.pipeline.add_filter(yolo)
                logger.info("✓ YOLO服务已添加")
            
            # 添加OpenCV处理服务
            if self.config.opencv_service.enabled:
                opencv = OpenCVService(self.config.opencv_service)
                self.pipeline.add_filter(opencv)
                logger.info("✓ OpenCV服务已添加")
            
            # 添加显示服务
            if self.config.display_service.enabled:
                display = DisplayService(self.config.display_service)
                self.pipeline.add_filter(display)
                logger.info("✓ 显示服务已添加")
            
            # 添加存储服务
            if self.config.storage_service.enabled:
                storage = StorageService(self.config.storage_service)
                self.pipeline.add_filter(storage)
                logger.info("✓ 存储服务已添加")
            
            # 创建性能监控器
            if self.config.enable_performance_monitor:
                self.performance_monitor = PerformanceMonitor(
                    self.pipeline,
                    self.config.performance_report_interval
                )
                logger.info("✓ 性能监控器已创建")
            
            logger.info("管道系统初始化完成")
            return True
            
        except Exception as e:
            logger.exception(f"初始化失败: {e}")
            return False
    
    def start(self):
        """启动管道系统"""
        try:
            if self.running:
                logger.warning("系统已在运行")
                return False
            
            logger.info("=" * 60)
            logger.info("启动管道系统")
            logger.info("=" * 60)
            
            # 启动相机
            if self.camera_service:
                # 枚举设备
                device_count = self.camera_service.enumerate_devices()
                if device_count == 0:
                    logger.error("未找到相机设备")
                    return False
                
                # 打开设备
                device_index = self.config.camera_service.device_index
                if not self.camera_service.open_device(device_index):
                    logger.error("打开相机失败")
                    return False
                
                # 开始采集
                if not self.camera_service.start_grabbing():
                    logger.error("开始采集失败")
                    return False
            
            # 启动管道
            self.pipeline.start()
            
            # 启动性能监控
            if self.performance_monitor:
                self.performance_monitor.start()
            
            # 启动相机采集线程
            self.running = True
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()
            
            logger.info("管道系统启动成功")
            logger.info("按 Ctrl+C 停止系统")
            
            return True
            
        except Exception as e:
            logger.exception(f"启动失败: {e}")
            return False
    
    def _camera_loop(self):
        """相机采集循环"""
        logger.info("相机采集线程启动")
        
        while self.running:
            try:
                # 从相机采集图像
                packet = self.camera_service.process(None)
                
                if packet:
                    # 将数据包送入管道
                    if not self.pipeline.put(packet, timeout=0.1):
                        logger.warning("管道输入队列已满，丢弃帧")
                    
                    # 从管道获取处理结果
                    result = self.pipeline.get(timeout=0.01)
                    if result and result.metadata.get('user_exit'):
                        logger.info("收到用户退出信号")
                        self.running = False
                        break
                
                # 检查最大帧数
                max_frames = self.config.camera_service.max_frames
                if max_frames > 0 and self.camera_service.frame_count >= max_frames:
                    logger.info(f"已达到最大帧数 {max_frames}")
                    self.running = False
                    break
                
            except Exception as e:
                logger.exception(f"采集循环异常: {e}")
        
        logger.info("相机采集线程退出")
    
    def stop(self):
        """停止管道系统"""
        try:
            if not self.running:
                return
            
            logger.info("=" * 60)
            logger.info("停止管道系统")
            logger.info("=" * 60)
            
            # 停止采集循环
            self.running = False
            if self.camera_thread:
                self.camera_thread.join(timeout=5)
            
            # 停止性能监控
            if self.performance_monitor:
                self.performance_monitor.stop()
            
            # 停止管道
            if self.pipeline:
                self.pipeline.stop()
            
            # 停止相机
            if self.camera_service:
                self.camera_service.stop_grabbing()
                self.camera_service.close_device()
            
            # 打印最终统计
            if self.pipeline:
                self.pipeline.print_statistics()
            
            logger.info("管道系统已停止")
            
        except Exception as e:
            logger.exception(f"停止异常: {e}")
    
    def run(self):
        """运行管道系统（阻塞）"""
        if not self.initialize():
            logger.error("初始化失败，退出")
            return
        
        if not self.start():
            logger.error("启动失败，退出")
            return
        
        try:
            # 等待用户中断
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("收到中断信号 (Ctrl+C)")
        finally:
            self.stop()


if __name__ == "__main__":
    # 测试调度器
    from pipeline_config import PresetConfigs
    
    # 使用开发模式配置
    config = PresetConfigs.development()
    
    # 创建调度器
    scheduler = PipelineScheduler(config)
    
    # 运行
    scheduler.run()
