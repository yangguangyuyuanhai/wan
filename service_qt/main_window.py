# -*- coding: utf-8 -*-
"""
Qt主窗口
工业视觉系统GUI - 海康威视风格
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QSplitter,
                             QGroupBox, QGridLayout, QTextEdit, QComboBox, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtSvg import QSvgWidget
import numpy as np
import cv2

# 添加service_new根目录到路径
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
service_new_root = os.path.dirname(current_dir)
if service_new_root not in sys.path:
    sys.path.insert(0, service_new_root)

from pipeline_config import PipelineConfig, PresetConfigs
from scheduler import PipelineScheduler
from logger_config import get_logger

logger = get_logger("QtGUI")


class VisionWorkerThread(QThread):
    """视觉处理工作线程"""
    
    frame_ready = pyqtSignal(np.ndarray, dict)  # 图像和检测结果
    status_update = pyqtSignal(str)  # 状态更新
    error_occurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.scheduler = None
        self.running = False
    
    def run(self):
        """运行线程"""
        try:
            self.status_update.emit("正在初始化系统...")
            self.scheduler = PipelineScheduler(self.config)
            
            if not self.scheduler.initialize():
                self.error_occurred.emit("系统初始化失败")
                return
            
            if not self.scheduler.start():
                self.error_occurred.emit("系统启动失败")
                return
            
            self.running = True
            self.status_update.emit("系统运行中")
            
            # 主循环
            while self.running:
                # 这里可以从管道获取处理结果
                # 暂时使用定时器在主线程更新
                self.msleep(100)
                
        except Exception as e:
            logger.exception(f"工作线程异常: {e}")
            self.error_occurred.emit(f"运行异常: {str(e)}")
    
    def stop(self):
        """停止线程"""
        self.running = False
        if self.scheduler:
            self.scheduler.stop()
        self.wait()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.config = PresetConfigs.development()
        self.worker_thread = None
        self.is_running = False
        
        self.init_ui()
        self.apply_stylesheet()
        
        # 定时器用于更新UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        logger.info("Qt主窗口初始化完成")
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("工业视觉系统 - MVS Vision System")
        self.setGeometry(100, 100, 1600, 900)
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧控制面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 中间显示区域
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # 右侧信息面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 2)  # 左侧
        splitter.setStretchFactor(1, 5)  # 中间
        splitter.setStretchFactor(2, 2)  # 右侧
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_left_panel(self):
        """创建左侧控制面板"""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("控制面板")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        
        # 系统控制组
        control_group = self.create_control_group()
        layout.addWidget(control_group)
        
        # 相机参数组
        camera_group = self.create_camera_group()
        layout.addWidget(camera_group)
        
        # 检测参数组
        detection_group = self.create_detection_group()
        layout.addWidget(detection_group)
        
        layout.addStretch()
        
        return panel
    
    def create_control_group(self):
        """创建系统控制组"""
        group = QGroupBox("系统控制")
        group.setObjectName("controlGroup")
        layout = QVBoxLayout(group)
        
        # 运行模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel("运行模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["开发模式", "生产模式", "调试模式"])
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # 启动/停止按钮
        self.start_btn = QPushButton("启动系统")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self.start_system)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止系统")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_system)
        layout.addWidget(self.stop_btn)
        
        # 截图按钮
        self.snapshot_btn = QPushButton("截图保存")
        self.snapshot_btn.setObjectName("normalButton")
        self.snapshot_btn.setEnabled(False)
        layout.addWidget(self.snapshot_btn)
        
        return group
    
    def create_camera_group(self):
        """创建相机参数组"""
        group = QGroupBox("相机参数")
        group.setObjectName("paramGroup")
        layout = QGridLayout(group)
        
        # 曝光时间
        layout.addWidget(QLabel("曝光时间(μs):"), 0, 0)
        self.exposure_spin = QSpinBox()
        self.exposure_spin.setRange(100, 100000)
        self.exposure_spin.setValue(10000)
        self.exposure_spin.setSingleStep(1000)
        layout.addWidget(self.exposure_spin, 0, 1)
        
        # 增益
        layout.addWidget(QLabel("增益(dB):"), 1, 0)
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0, 24)
        self.gain_spin.setValue(10.0)
        self.gain_spin.setSingleStep(0.5)
        layout.addWidget(self.gain_spin, 1, 1)
        
        # 帧率
        layout.addWidget(QLabel("帧率(fps):"), 2, 0)
        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30.0)
        self.fps_spin.setSingleStep(1.0)
        layout.addWidget(self.fps_spin, 2, 1)
        
        # 应用按钮
        apply_btn = QPushButton("应用参数")
        apply_btn.setObjectName("normalButton")
        apply_btn.clicked.connect(self.apply_camera_params)
        layout.addWidget(apply_btn, 3, 0, 1, 2)
        
        return group
    
    def create_detection_group(self):
        """创建检测参数组"""
        group = QGroupBox("检测参数")
        group.setObjectName("paramGroup")
        layout = QGridLayout(group)
        
        # 启用YOLO
        self.yolo_check = QCheckBox("启用YOLO检测")
        self.yolo_check.setChecked(True)
        layout.addWidget(self.yolo_check, 0, 0, 1, 2)
        
        # 置信度阈值
        layout.addWidget(QLabel("置信度:"), 1, 0)
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setValue(0.5)
        self.confidence_spin.setSingleStep(0.05)
        layout.addWidget(self.confidence_spin, 1, 1)
        
        # IOU阈值
        layout.addWidget(QLabel("IOU阈值:"), 2, 0)
        self.iou_spin = QDoubleSpinBox()
        self.iou_spin.setRange(0.1, 1.0)
        self.iou_spin.setValue(0.45)
        self.iou_spin.setSingleStep(0.05)
        layout.addWidget(self.iou_spin, 2, 1)
        
        return group
    
    def create_center_panel(self):
        """创建中间显示面板"""
        panel = QFrame()
        panel.setObjectName("centerPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel("实时图像")
        title.setObjectName("panelTitle")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # FPS显示
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setObjectName("fpsLabel")
        title_layout.addWidget(self.fps_label)
        
        layout.addLayout(title_layout)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setObjectName("imageDisplay")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setScaledContents(False)
        self.image_label.setText("等待图像...")
        layout.addWidget(self.image_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def create_right_panel(self):
        """创建右侧信息面板"""
        panel = QFrame()
        panel.setObjectName("rightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签页
        tab_widget = QTabWidget()
        tab_widget.setObjectName("infoTabs")
        
        # 检测结果标签页
        detection_tab = self.create_detection_tab()
        tab_widget.addTab(detection_tab, "检测结果")
        
        # 统计信息标签页
        stats_tab = self.create_stats_tab()
        tab_widget.addTab(stats_tab, "统计信息")
        
        # 日志标签页
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "系统日志")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def create_detection_tab(self):
        """创建检测结果标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 检测结果表格
        self.detection_table = QTableWidget()
        self.detection_table.setObjectName("detectionTable")
        self.detection_table.setColumnCount(4)
        self.detection_table.setHorizontalHeaderLabels(["类别", "置信度", "位置X", "位置Y"])
        self.detection_table.horizontalHeader().setStretchLastSection(True)
        self.detection_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.detection_table)
        
        # 检测统计
        stats_layout = QGridLayout()
        stats_layout.addWidget(QLabel("检测数量:"), 0, 0)
        self.det_count_label = QLabel("0")
        self.det_count_label.setObjectName("statValue")
        stats_layout.addWidget(self.det_count_label, 0, 1)
        
        stats_layout.addWidget(QLabel("平均置信度:"), 1, 0)
        self.avg_conf_label = QLabel("0.00")
        self.avg_conf_label.setObjectName("statValue")
        stats_layout.addWidget(self.avg_conf_label, 1, 1)
        
        layout.addLayout(stats_layout)
        
        return widget
    
    def create_stats_tab(self):
        """创建统计信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 性能统计
        perf_group = QGroupBox("性能统计")
        perf_layout = QGridLayout(perf_group)
        
        perf_layout.addWidget(QLabel("处理帧数:"), 0, 0)
        self.frame_count_label = QLabel("0")
        self.frame_count_label.setObjectName("statValue")
        perf_layout.addWidget(self.frame_count_label, 0, 1)
        
        perf_layout.addWidget(QLabel("平均耗时:"), 1, 0)
        self.avg_time_label = QLabel("0.0 ms")
        self.avg_time_label.setObjectName("statValue")
        perf_layout.addWidget(self.avg_time_label, 1, 1)
        
        perf_layout.addWidget(QLabel("错误次数:"), 2, 0)
        self.error_count_label = QLabel("0")
        self.error_count_label.setObjectName("statValue")
        perf_layout.addWidget(self.error_count_label, 2, 1)
        
        layout.addWidget(perf_group)
        
        # 服务状态
        service_group = QGroupBox("服务状态")
        service_layout = QVBoxLayout(service_group)
        
        self.service_status_text = QTextEdit()
        self.service_status_text.setObjectName("statusText")
        self.service_status_text.setReadOnly(True)
        self.service_status_text.setMaximumHeight(200)
        service_layout.addWidget(self.service_status_text)
        
        layout.addWidget(service_group)
        layout.addStretch()
        
        return widget
    
    def create_log_tab(self):
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 清除按钮
        clear_btn = QPushButton("清除日志")
        clear_btn.setObjectName("normalButton")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)
        
        return widget
    
    def apply_stylesheet(self):
        """应用样式表 - 海康威视风格"""
        from styles import get_hikvision_style
        self.setStyleSheet(get_hikvision_style())
    
    def start_system(self):
        """启动系统"""
        try:
            self.log_message("正在启动系统...")
            
            # 更新配置
            self.update_config_from_ui()
            
            # 创建工作线程
            self.worker_thread = VisionWorkerThread(self.config)
            self.worker_thread.status_update.connect(self.on_status_update)
            self.worker_thread.error_occurred.connect(self.on_error)
            self.worker_thread.start()
            
            # 更新UI状态
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.snapshot_btn.setEnabled(True)
            self.is_running = True
            
            # 启动更新定时器
            self.update_timer.start(33)  # 约30fps
            
            self.log_message("系统启动成功")
            
        except Exception as e:
            logger.exception(f"启动系统异常: {e}")
            self.log_message(f"启动失败: {str(e)}", "error")
    
    def stop_system(self):
        """停止系统"""
        try:
            self.log_message("正在停止系统...")
            
            # 停止定时器
            self.update_timer.stop()
            
            # 停止工作线程
            if self.worker_thread:
                self.worker_thread.stop()
                self.worker_thread = None
            
            # 更新UI状态
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.snapshot_btn.setEnabled(False)
            self.is_running = False
            
            self.log_message("系统已停止")
            self.statusBar().showMessage("已停止")
            
        except Exception as e:
            logger.exception(f"停止系统异常: {e}")
            self.log_message(f"停止失败: {str(e)}", "error")
    
    def update_config_from_ui(self):
        """从UI更新配置"""
        # 相机参数
        self.config.camera_service.exposure_time = self.exposure_spin.value()
        self.config.camera_service.gain = self.gain_spin.value()
        self.config.camera_service.frame_rate = self.fps_spin.value()
        
        # 检测参数
        self.config.yolo_service.enabled = self.yolo_check.isChecked()
        self.config.yolo_service.confidence_threshold = self.confidence_spin.value()
        self.config.yolo_service.iou_threshold = self.iou_spin.value()
    
    def apply_camera_params(self):
        """应用相机参数"""
        self.log_message("应用相机参数...")
        # TODO: 实现运行时参数更新
    
    def update_display(self):
        """更新显示"""
        # TODO: 从管道获取最新图像和检测结果
        # 这里暂时使用模拟数据
        pass
    
    def on_status_update(self, message):
        """状态更新回调"""
        self.statusBar().showMessage(message)
        self.log_message(message)
    
    def on_error(self, error_msg):
        """错误回调"""
        self.log_message(error_msg, "error")
        self.stop_system()
    
    def log_message(self, message, level="info"):
        """记录日志消息"""
        color = {
            "info": "#00D9FF",
            "warning": "#FFA500",
            "error": "#FF4444"
        }.get(level, "#00D9FF")
        
        self.log_text.append(f'<span style="color: {color};">[{level.upper()}] {message}</span>')
        logger.info(message)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.is_running:
            self.stop_system()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
