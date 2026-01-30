# -*- coding: utf-8 -*-
"""
主程序 - 上帝类
整个系统的入口点，负责加载和运行所有模块
"""

import sys
import argparse
from pipeline_config import PipelineConfig, PresetConfigs, get_config, set_config
from scheduler import PipelineScheduler
from logger_config import get_logger

logger = get_logger("Main")


class VisionSystem:
    """
    视觉系统上帝类
    负责整个系统的生命周期管理
    """
    
    def __init__(self):
        """初始化视觉系统"""
        self.scheduler = None
        self.config = None
        
        logger.info("=" * 60)
        logger.info("工业视觉系统")
        logger.info("=" * 60)
    
    def load_config(self, mode='development'):
        """
        加载配置
        
        Args:
            mode: 运行模式 (development/production/debug)
        """
        logger.info(f"加载配置: {mode} 模式")
        
        if mode == 'development':
            self.config = PresetConfigs.development()
        elif mode == 'production':
            self.config = PresetConfigs.production()
        elif mode == 'debug':
            self.config = PresetConfigs.debug()
        else:
            logger.warning(f"未知模式 '{mode}'，使用默认配置")
            self.config = PipelineConfig()
        
        # 设置全局配置
        set_config(self.config)
        
        logger.info("配置加载完成")
    
    def customize_config(self, **kwargs):
        """
        自定义配置
        
        Args:
            **kwargs: 配置参数
        """
        logger.info("应用自定义配置...")
        
        # 相机参数
        if 'exposure_time' in kwargs:
            self.config.camera_service.exposure_time = kwargs['exposure_time']
            logger.info(f"  曝光时间: {kwargs['exposure_time']} μs")
        
        if 'gain' in kwargs:
            self.config.camera_service.gain = kwargs['gain']
            logger.info(f"  增益: {kwargs['gain']} dB")
        
        if 'frame_rate' in kwargs:
            self.config.camera_service.frame_rate = kwargs['frame_rate']
            logger.info(f"  帧率: {kwargs['frame_rate']} fps")
        
        # YOLO参数
        if 'yolo_model' in kwargs:
            self.config.yolo_service.model_path = kwargs['yolo_model']
            logger.info(f"  YOLO模型: {kwargs['yolo_model']}")
        
        if 'confidence' in kwargs:
            self.config.yolo_service.confidence_threshold = kwargs['confidence']
            logger.info(f"  置信度阈值: {kwargs['confidence']}")
        
        # 显示参数
        if 'no_display' in kwargs and kwargs['no_display']:
            self.config.display_service.enabled = False
            logger.info("  禁用显示")
        
        # 存储参数
        if 'save_images' in kwargs and kwargs['save_images']:
            self.config.storage_service.enabled = True
            self.config.storage_service.save_images = True
            logger.info("  启用图像保存")
    
    def initialize(self):
        """初始化系统"""
        logger.info("初始化系统...")
        
        # 创建调度器
        self.scheduler = PipelineScheduler(self.config)
        
        # 初始化管道
        if not self.scheduler.initialize():
            logger.error("系统初始化失败")
            return False
        
        logger.info("系统初始化成功")
        return True
    
    def start(self):
        """启动系统"""
        logger.info("启动系统...")
        
        if not self.scheduler.start():
            logger.error("系统启动失败")
            return False
        
        logger.info("系统启动成功")
        return True
    
    def run(self):
        """运行系统（阻塞）"""
        logger.info("系统运行中...")
        
        try:
            # 运行调度器
            self.scheduler.run()
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        except Exception as e:
            logger.exception(f"运行异常: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止系统"""
        logger.info("停止系统...")
        
        if self.scheduler:
            self.scheduler.stop()
        
        logger.info("系统已停止")
        logger.info("=" * 60)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='工业视觉系统 - 管道-过滤器架构',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 开发模式（默认）
  python main.py
  
  # 生产模式
  python main.py --mode production
  
  # 调试模式
  python main.py --mode debug
  
  # 自定义参数
  python main.py --exposure 15000 --gain 12.0 --confidence 0.6
  
  # 禁用显示
  python main.py --no-display
  
  # 启用图像保存
  python main.py --save-images
        """
    )
    
    # 运行模式
    parser.add_argument(
        '--mode',
        choices=['development', 'production', 'debug'],
        default='development',
        help='运行模式 (默认: development)'
    )
    
    # 相机参数
    parser.add_argument('--exposure', type=float, help='曝光时间（微秒）')
    parser.add_argument('--gain', type=float, help='增益（dB）')
    parser.add_argument('--frame-rate', type=float, help='帧率（fps）')
    
    # YOLO参数
    parser.add_argument('--yolo-model', type=str, help='YOLO模型路径')
    parser.add_argument('--confidence', type=float, help='置信度阈值')
    
    # 显示参数
    parser.add_argument('--no-display', action='store_true', help='禁用显示')
    
    # 存储参数
    parser.add_argument('--save-images', action='store_true', help='启用图像保存')
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 创建视觉系统
    system = VisionSystem()
    
    # 加载配置
    system.load_config(mode=args.mode)
    
    # 应用自定义配置
    custom_config = {}
    if args.exposure:
        custom_config['exposure_time'] = args.exposure
    if args.gain:
        custom_config['gain'] = args.gain
    if args.frame_rate:
        custom_config['frame_rate'] = args.frame_rate
    if args.yolo_model:
        custom_config['yolo_model'] = args.yolo_model
    if args.confidence:
        custom_config['confidence'] = args.confidence
    if args.no_display:
        custom_config['no_display'] = True
    if args.save_images:
        custom_config['save_images'] = True
    
    if custom_config:
        system.customize_config(**custom_config)
    
    # 初始化系统
    if not system.initialize():
        logger.error("初始化失败，退出")
        sys.exit(1)
    
    # 运行系统
    system.run()
    
    logger.info("程序退出")


if __name__ == "__main__":
    main()
