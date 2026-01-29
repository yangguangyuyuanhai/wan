# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志管理功能
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime


class CameraLogger:
    """相机应用日志管理器"""
    
    def __init__(self, 
                 name="CameraApp",
                 log_dir="./logs",
                 console_level=logging.INFO,
                 file_level=logging.DEBUG,
                 max_bytes=10*1024*1024,  # 10MB
                 backup_count=5):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志文件目录
            console_level: 控制台日志级别
            file_level: 文件日志级别
            max_bytes: 单个日志文件最大大小
            backup_count: 保留的日志文件数量
        """
        self.name = name
        self.log_dir = log_dir
        self.logger = None
        
        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 初始化日志器
        self._setup_logger(console_level, file_level, max_bytes, backup_count)
    
    def _setup_logger(self, console_level, file_level, max_bytes, backup_count):
        """配置日志器"""
        # 创建logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)  # 设置最低级别
        
        # 避免重复添加handler
        if self.logger.handlers:
            return
        
        # 定义日志格式
        detailed_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 1. 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # 2. 详细日志文件（按大小轮转）
        detail_log_file = os.path.join(self.log_dir, f"{self.name}_detail.log")
        detail_handler = RotatingFileHandler(
            detail_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        detail_handler.setLevel(file_level)
        detail_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(detail_handler)
        
        # 3. 错误日志文件（只记录ERROR及以上）
        error_log_file = os.path.join(self.log_dir, f"{self.name}_error.log")
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # 4. 按日期轮转的日志文件
        daily_log_file = os.path.join(self.log_dir, f"{self.name}_daily.log")
        daily_handler = TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 保留30天
            encoding='utf-8'
        )
        daily_handler.setLevel(file_level)
        daily_handler.setFormatter(detailed_formatter)
        daily_handler.suffix = "%Y%m%d"
        self.logger.addHandler(daily_handler)
    
    def get_logger(self):
        """获取logger实例"""
        return self.logger
    
    def debug(self, msg, *args, **kwargs):
        """调试信息"""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """一般信息"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """警告信息"""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """错误信息"""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """严重错误"""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        """异常信息（自动包含堆栈跟踪）"""
        self.logger.exception(msg, *args, **kwargs)
    
    def log_camera_event(self, event_type, details):
        """记录相机事件"""
        self.logger.info(f"[CAMERA_EVENT] {event_type}: {details}")
    
    def log_frame_info(self, frame_num, width, height, pixel_format):
        """记录帧信息"""
        self.logger.debug(
            f"[FRAME] #{frame_num} - {width}x{height} - Format:0x{pixel_format:x}"
        )
    
    def log_performance(self, operation, duration_ms):
        """记录性能信息"""
        self.logger.info(f"[PERFORMANCE] {operation}: {duration_ms:.2f}ms")
    
    def log_sdk_error(self, function_name, error_code):
        """记录SDK错误"""
        self.logger.error(
            f"[SDK_ERROR] {function_name} failed with code: 0x{error_code:x}"
        )


# 创建全局日志器实例
_global_logger = None

def get_logger(name="CameraApp", **kwargs):
    """
    获取全局日志器实例
    
    Args:
        name: 日志器名称
        **kwargs: 其他配置参数
    
    Returns:
        CameraLogger实例
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = CameraLogger(name, **kwargs)
    return _global_logger


# 便捷函数
def debug(msg, *args, **kwargs):
    """调试日志"""
    get_logger().debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    """信息日志"""
    get_logger().info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    """警告日志"""
    get_logger().warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    """错误日志"""
    get_logger().error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    """严重错误日志"""
    get_logger().critical(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    """异常日志"""
    get_logger().exception(msg, *args, **kwargs)


if __name__ == "__main__":
    # 测试日志模块
    logger = get_logger("TestApp")
    
    logger.info("=" * 50)
    logger.info("日志模块测试")
    logger.info("=" * 50)
    
    logger.debug("这是调试信息")
    logger.info("这是一般信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误")
    
    logger.log_camera_event("DEVICE_OPENED", "Camera-001")
    logger.log_frame_info(1, 1920, 1080, 0x01080001)
    logger.log_performance("ImageProcessing", 15.5)
    logger.log_sdk_error("MV_CC_OpenDevice", 0x80000001)
    
    try:
        raise ValueError("测试异常")
    except Exception as e:
        logger.exception("捕获到异常")
    
    print("\n日志文件已保存到 ./logs/ 目录")
