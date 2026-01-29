# -*- coding: utf-8 -*-
"""
Qt GUI启动脚本
"""

import sys
import os

# 添加service_new根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
service_new_root = os.path.dirname(current_dir)
if service_new_root not in sys.path:
    sys.path.insert(0, service_new_root)

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from main_window import MainWindow
from logger_config import get_logger

logger = get_logger("QtGUI")


class SplashScreen(QSplashScreen):
    """启动画面"""
    
    def __init__(self):
        # 创建启动画面图像
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor(30, 30, 30))
        
        # 绘制启动画面内容
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制标题
        painter.setPen(QColor(0, 217, 255))
        painter.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "工业视觉系统")
        
        # 绘制副标题
        painter.setPen(QColor(224, 224, 224))
        painter.setFont(QFont("Microsoft YaHei", 14))
        painter.drawText(50, 250, "MVS Vision System")
        
        # 绘制版本信息
        painter.setFont(QFont("Microsoft YaHei", 10))
        painter.drawText(50, 280, "Version 1.0.0")
        
        # 绘制加载提示
        painter.setPen(QColor(0, 153, 204))
        painter.setFont(QFont("Microsoft YaHei", 12))
        painter.drawText(50, 350, "正在加载...")
        
        painter.end()
        
        # 初始化父类
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)


def main():
    """主函数"""
    try:
        # 创建应用
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # 设置应用信息
        app.setApplicationName("工业视觉系统")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("MVS")
        
        # 显示启动画面
        splash = SplashScreen()
        splash.show()
        app.processEvents()
        
        # 模拟加载过程
        def update_splash(message):
            splash.showMessage(
                message,
                Qt.AlignBottom | Qt.AlignCenter,
                QColor(0, 217, 255)
            )
            app.processEvents()
        
        update_splash("初始化系统...")
        QTimer.singleShot(500, lambda: update_splash("加载配置..."))
        QTimer.singleShot(1000, lambda: update_splash("加载模块..."))
        QTimer.singleShot(1500, lambda: update_splash("准备就绪"))
        
        # 创建主窗口
        window = MainWindow()
        
        # 2秒后关闭启动画面并显示主窗口
        QTimer.singleShot(2000, splash.close)
        QTimer.singleShot(2000, window.show)
        
        logger.info("Qt GUI启动成功")
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.exception(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
