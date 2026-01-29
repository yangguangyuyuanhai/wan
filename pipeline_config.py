# -*- coding: utf-8 -*-
"""
管道配置模块
定义整个系统的配置参数
"""

import os
from enum import Enum


class PipelineMode(Enum):
    """管道运行模式"""
    DEVELOPMENT = "development"  # 开发模式：详细日志，实时显示
    PRODUCTION = "production"    # 生产模式：精简日志，高性能
    DEBUG = "debug"              # 调试模式：最详细日志，单步调试


class ServiceConfig:
    """微服务配置基类"""
    
    def __init__(self, name, enabled=True):
        self.name = name
        self.enabled = enabled


# ==================== 相机服务配置 ====================
class CameraServiceConfig(ServiceConfig):
    """相机采集服务配置"""
    
    def __init__(self):
        super().__init__("CameraService", enabled=True)
        
        # 相机参数
        self.exposure_time = 10000      # 曝光时间（微秒）
        self.gain = 10.0                # 增益（dB）
        self.frame_rate = 30.0          # 帧率（fps）
        self.trigger_mode = False       # 触发模式
        
        # 采集参数
        self.max_frames = 0             # 最大帧数（0=无限）
        self.grab_timeout = 1000        # 采集超时（毫秒）
        self.buffer_size = 10           # 图像缓冲区大小
        
        # 设备选择
        self.auto_select_device = True  # 自动选择第一个设备
        self.device_index = 0           # 设备索引
        self.device_serial = ""         # 设备序列号（为空则不过滤）
        
        # 性能优化
        self.enable_packet_size_optimization = True  # GigE包大小优化


# ==================== 预处理服务配置 ====================
class PreprocessServiceConfig(ServiceConfig):
    """图像预处理服务配置"""
    
    def __init__(self):
        super().__init__("PreprocessService", enabled=True)
        
        # 图像转换
        self.convert_to_bgr = True      # 转换为BGR格式
        self.resize_enabled = False     # 是否调整大小
        self.resize_width = 640         # 调整后宽度
        self.resize_height = 480        # 调整后高度
        
        # 图像增强
        self.denoise_enabled = False    # 降噪
        self.denoise_strength = 5       # 降噪强度
        self.sharpen_enabled = False    # 锐化
        self.sharpen_strength = 1.0     # 锐化强度
        
        # 颜色校正
        self.auto_white_balance = False # 自动白平衡
        self.brightness_adjust = 0      # 亮度调整（-100~100）
        self.contrast_adjust = 0        # 对比度调整（-100~100）


# ==================== YOLO检测服务配置 ====================
class YOLOServiceConfig(ServiceConfig):
    """YOLO目标检测服务配置"""
    
    def __init__(self):
        super().__init__("YOLOService", enabled=True)
        
        # 模型配置
        self.model_path = "./models/yolov8n.pt"  # 模型路径
        self.model_type = "yolov8"               # 模型类型（yolov5/yolov8）
        self.device = "cpu"                      # 运行设备（cpu/cuda/mps）
        
        # 检测参数
        self.confidence_threshold = 0.5          # 置信度阈值
        self.iou_threshold = 0.45                # NMS IOU阈值
        self.max_detections = 100                # 最大检测数量
        
        # 类别过滤
        self.target_classes = []                 # 目标类别（空=全部）
        self.ignore_classes = []                 # 忽略类别
        
        # 性能优化
        self.batch_size = 1                      # 批处理大小
        self.half_precision = False              # 半精度推理（FP16）
        self.use_tensorrt = False                # 使用TensorRT加速


# ==================== OpenCV处理服务配置 ====================
class OpenCVServiceConfig(ServiceConfig):
    """OpenCV图像处理服务配置"""
    
    def __init__(self):
        super().__init__("OpenCVService", enabled=True)
        
        # 边缘检测
        self.edge_detection_enabled = False
        self.canny_threshold1 = 50
        self.canny_threshold2 = 150
        
        # 轮廓检测
        self.contour_detection_enabled = False
        self.contour_min_area = 100
        self.contour_max_area = 10000
        
        # 形态学操作
        self.morphology_enabled = False
        self.morphology_operation = "open"  # open/close/gradient
        self.morphology_kernel_size = 5
        
        # 特征提取
        self.feature_extraction_enabled = False
        self.feature_type = "orb"  # orb/sift/surf


# ==================== 显示服务配置 ====================
class DisplayServiceConfig(ServiceConfig):
    """图像显示服务配置"""
    
    def __init__(self):
        super().__init__("DisplayService", enabled=True)
        
        # 显示窗口
        self.window_name = "Vision Pipeline"
        self.window_width = 1280
        self.window_height = 720
        self.fullscreen = False
        
        # 显示内容
        self.show_original = True       # 显示原始图像
        self.show_processed = True      # 显示处理后图像
        self.show_detections = True     # 显示检测结果
        
        # 信息叠加
        self.show_fps = True            # 显示FPS
        self.show_timestamp = True      # 显示时间戳
        self.show_frame_count = True    # 显示帧计数
        self.show_detection_info = True # 显示检测信息
        
        # 性能
        self.display_fps_limit = 30     # 显示帧率限制


# ==================== 存储服务配置 ====================
class StorageServiceConfig(ServiceConfig):
    """数据存储服务配置"""
    
    def __init__(self):
        super().__init__("StorageService", enabled=False)
        
        # 图像保存
        self.save_images = True
        self.save_path = "./output/images"
        self.save_format = "jpg"        # jpg/png/bmp
        self.jpeg_quality = 90
        
        # 保存策略
        self.save_all_frames = False    # 保存所有帧
        self.save_interval = 100        # 保存间隔（帧）
        self.save_on_detection = True   # 检测到目标时保存
        
        # 数据记录
        self.save_detections = True     # 保存检测结果
        self.detection_log_path = "./output/detections.json"
        
        # 视频录制
        self.record_video = False
        self.video_path = "./output/video.mp4"
        self.video_fps = 30
        self.video_codec = "mp4v"


# ==================== 日志配置 ====================
class LoggingConfig:
    """日志配置"""
    
    # 日志目录
    LOG_DIR = "./logs"
    
    # 日志级别
    CONSOLE_LEVEL = "INFO"
    FILE_LEVEL = "DEBUG"
    
    # 日志文件
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    DAILY_BACKUP_DAYS = 30
    
    # 性能日志
    ENABLE_PERFORMANCE_LOG = True
    PERFORMANCE_LOG_INTERVAL = 100  # 每N帧记录一次


# ==================== 管道配置 ====================
class PipelineConfig:
    """管道总配置"""
    
    def __init__(self):
        # 运行模式
        self.mode = PipelineMode.DEVELOPMENT
        
        # 微服务配置
        self.camera_service = CameraServiceConfig()
        self.preprocess_service = PreprocessServiceConfig()
        self.yolo_service = YOLOServiceConfig()
        self.opencv_service = OpenCVServiceConfig()
        self.display_service = DisplayServiceConfig()
        self.storage_service = StorageServiceConfig()
        
        # 日志配置
        self.logging = LoggingConfig()
        
        # 管道参数
        self.pipeline_buffer_size = 10      # 管道缓冲区大小
        self.max_processing_time = 1000     # 最大处理时间（毫秒）
        self.enable_async_processing = True # 异步处理
        
        # 性能监控
        self.enable_performance_monitor = True
        self.performance_report_interval = 10  # 性能报告间隔（秒）
    
    def validate(self):
        """验证配置有效性"""
        errors = []
        
        # 验证相机配置
        if self.camera_service.enabled:
            if self.camera_service.exposure_time <= 0:
                errors.append("曝光时间必须大于0")
            if self.camera_service.gain < 0:
                errors.append("增益不能为负数")
        
        # 验证YOLO配置
        if self.yolo_service.enabled:
            if not os.path.exists(self.yolo_service.model_path):
                errors.append(f"YOLO模型文件不存在: {self.yolo_service.model_path}")
            if not 0 < self.yolo_service.confidence_threshold < 1:
                errors.append("置信度阈值必须在0-1之间")
        
        # 验证存储配置
        if self.storage_service.enabled:
            if self.storage_service.save_images:
                os.makedirs(self.storage_service.save_path, exist_ok=True)
        
        if errors:
            raise ValueError("配置验证失败:\n" + "\n".join(errors))
        
        return True
    
    def print_config(self):
        """打印配置信息"""
        print("=" * 60)
        print("管道配置信息")
        print("=" * 60)
        print(f"\n运行模式: {self.mode.value}")
        
        print("\n【启用的服务】")
        services = [
            ("相机采集", self.camera_service),
            ("图像预处理", self.preprocess_service),
            ("YOLO检测", self.yolo_service),
            ("OpenCV处理", self.opencv_service),
            ("图像显示", self.display_service),
            ("数据存储", self.storage_service),
        ]
        
        for name, service in services:
            status = "✓ 启用" if service.enabled else "✗ 禁用"
            print(f"  {name}: {status}")
        
        if self.camera_service.enabled:
            print("\n【相机参数】")
            print(f"  曝光时间: {self.camera_service.exposure_time} μs")
            print(f"  增益: {self.camera_service.gain} dB")
            print(f"  帧率: {self.camera_service.frame_rate} fps")
        
        if self.yolo_service.enabled:
            print("\n【YOLO参数】")
            print(f"  模型: {self.yolo_service.model_path}")
            print(f"  设备: {self.yolo_service.device}")
            print(f"  置信度: {self.yolo_service.confidence_threshold}")
        
        print("=" * 60)


# ==================== 预设配置 ====================
class PresetConfigs:
    """预设配置"""
    
    @staticmethod
    def development():
        """开发模式配置"""
        config = PipelineConfig()
        config.mode = PipelineMode.DEVELOPMENT
        config.logging.CONSOLE_LEVEL = "DEBUG"
        config.display_service.enabled = True
        config.storage_service.enabled = False
        return config
    
    @staticmethod
    def production():
        """生产模式配置"""
        config = PipelineConfig()
        config.mode = PipelineMode.PRODUCTION
        config.logging.CONSOLE_LEVEL = "WARNING"
        config.display_service.enabled = False
        config.storage_service.enabled = True
        config.storage_service.save_on_detection = True
        return config
    
    @staticmethod
    def debug():
        """调试模式配置"""
        config = PipelineConfig()
        config.mode = PipelineMode.DEBUG
        config.logging.CONSOLE_LEVEL = "DEBUG"
        config.logging.FILE_LEVEL = "DEBUG"
        config.camera_service.max_frames = 100
        config.enable_performance_monitor = True
        return config


# ==================== 全局配置实例 ====================
# 默认使用开发模式
global_config = PresetConfigs.development()


def get_config():
    """获取全局配置"""
    return global_config


def set_config(config):
    """设置全局配置"""
    global global_config
    global_config = config


if __name__ == "__main__":
    # 测试配置模块
    print("配置模块测试\n")
    
    # 测试开发模式
    config = PresetConfigs.development()
    config.print_config()
    
    try:
        config.validate()
        print("\n✓ 配置验证通过")
    except ValueError as e:
        print(f"\n✗ 配置验证失败: {e}")
