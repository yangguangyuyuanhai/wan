# -*- coding: utf-8 -*-
"""
对话框模块
包含各种配置和信息对话框
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QGroupBox,
                             QGridLayout, QFileDialog, QMessageBox, QTabWidget,
                             QWidget, QComboBox, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class AboutDialog(QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("工业视觉系统")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        title.setStyleSheet("color: #00D9FF;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 版本信息
        version = QLabel("Version 1.0.0")
        version.setFont(QFont("Microsoft YaHei", 12))
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        # 描述
        desc = QTextEdit()
        desc.setReadOnly(True)
        desc.setMaximumHeight(150)
        desc.setHtml("""
        <p style='color: #E0E0E0;'>
        <b>工业视觉系统</b>是一个基于Pipeline-Filter架构的专业视觉处理平台。
        </p>
        <p style='color: #E0E0E0;'>
        <b>主要特性：</b><br>
        • 多相机并发采集<br>
        • YOLO目标检测<br>
        • OpenCV图像处理<br>
        • 实时性能监控<br>
        • 微服务架构
        </p>
        """)
        layout.addWidget(desc)
        
        # 版权信息
        copyright_label = QLabel("© 2025 MVS Vision System")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("normalButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class ConfigDialog(QDialog):
    """配置对话框"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("系统配置")
        self.setMinimumSize(700, 600)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 相机配置标签页
        camera_tab = self.create_camera_tab()
        tab_widget.addTab(camera_tab, "相机配置")
        
        # YOLO配置标签页
        yolo_tab = self.create_yolo_tab()
        tab_widget.addTab(yolo_tab, "YOLO配置")
        
        # 显示配置标签页
        display_tab = self.create_display_tab()
        tab_widget.addTab(display_tab, "显示配置")
        
        # 存储配置标签页
        storage_tab = self.create_storage_tab()
        tab_widget.addTab(storage_tab, "存储配置")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_camera_tab(self):
        """创建相机配置标签页"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        row = 0
        
        # 曝光时间
        layout.addWidget(QLabel("曝光时间 (μs):"), row, 0)
        self.exposure_spin = QSpinBox()
        self.exposure_spin.setRange(100, 100000)
        self.exposure_spin.setValue(self.config.camera_service.exposure_time)
        layout.addWidget(self.exposure_spin, row, 1)
        row += 1
        
        # 增益
        layout.addWidget(QLabel("增益 (dB):"), row, 0)
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0, 24)
        self.gain_spin.setValue(self.config.camera_service.gain)
        layout.addWidget(self.gain_spin, row, 1)
        row += 1
        
        # 帧率
        layout.addWidget(QLabel("帧率 (fps):"), row, 0)
        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(self.config.camera_service.frame_rate)
        layout.addWidget(self.fps_spin, row, 1)
        row += 1
        
        # 触发模式
        self.trigger_check = QCheckBox("触发模式")
        self.trigger_check.setChecked(self.config.camera_service.trigger_mode)
        layout.addWidget(self.trigger_check, row, 0, 1, 2)
        row += 1
        
        # 最大帧数
        layout.addWidget(QLabel("最大帧数 (0=无限):"), row, 0)
        self.max_frames_spin = QSpinBox()
        self.max_frames_spin.setRange(0, 1000000)
        self.max_frames_spin.setValue(self.config.camera_service.max_frames)
        layout.addWidget(self.max_frames_spin, row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        
        return widget
    
    def create_yolo_tab(self):
        """创建YOLO配置标签页"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        row = 0
        
        # 启用YOLO
        self.yolo_enable_check = QCheckBox("启用YOLO检测")
        self.yolo_enable_check.setChecked(self.config.yolo_service.enabled)
        layout.addWidget(self.yolo_enable_check, row, 0, 1, 2)
        row += 1
        
        # 模型路径
        layout.addWidget(QLabel("模型路径:"), row, 0)
        model_layout = QHBoxLayout()
        self.model_path_edit = QLineEdit(self.config.yolo_service.model_path)
        model_layout.addWidget(self.model_path_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_model)
        model_layout.addWidget(browse_btn)
        layout.addLayout(model_layout, row, 1)
        row += 1
        
        # 设备
        layout.addWidget(QLabel("运行设备:"), row, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda", "mps"])
        self.device_combo.setCurrentText(self.config.yolo_service.device)
        layout.addWidget(self.device_combo, row, 1)
        row += 1
        
        # 置信度阈值
        layout.addWidget(QLabel("置信度阈值:"), row, 0)
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        self.confidence_spin.setValue(self.config.yolo_service.confidence_threshold)
        layout.addWidget(self.confidence_spin, row, 1)
        row += 1
        
        # IOU阈值
        layout.addWidget(QLabel("IOU阈值:"), row, 0)
        self.iou_spin = QDoubleSpinBox()
        self.iou_spin.setRange(0.1, 1.0)
        self.iou_spin.setSingleStep(0.05)
        self.iou_spin.setValue(self.config.yolo_service.iou_threshold)
        layout.addWidget(self.iou_spin, row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        
        return widget
    
    def create_display_tab(self):
        """创建显示配置标签页"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        row = 0
        
        # 启用显示
        self.display_enable_check = QCheckBox("启用图像显示")
        self.display_enable_check.setChecked(self.config.display_service.enabled)
        layout.addWidget(self.display_enable_check, row, 0, 1, 2)
        row += 1
        
        # 显示FPS
        self.show_fps_check = QCheckBox("显示FPS")
        self.show_fps_check.setChecked(self.config.display_service.show_fps)
        layout.addWidget(self.show_fps_check, row, 0, 1, 2)
        row += 1
        
        # 显示检测结果
        self.show_det_check = QCheckBox("显示检测结果")
        self.show_det_check.setChecked(self.config.display_service.show_detections)
        layout.addWidget(self.show_det_check, row, 0, 1, 2)
        row += 1
        
        # 显示帧率限制
        layout.addWidget(QLabel("显示帧率限制:"), row, 0)
        self.display_fps_spin = QSpinBox()
        self.display_fps_spin.setRange(1, 120)
        self.display_fps_spin.setValue(self.config.display_service.display_fps_limit)
        layout.addWidget(self.display_fps_spin, row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        
        return widget
    
    def create_storage_tab(self):
        """创建存储配置标签页"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        row = 0
        
        # 启用存储
        self.storage_enable_check = QCheckBox("启用数据存储")
        self.storage_enable_check.setChecked(self.config.storage_service.enabled)
        layout.addWidget(self.storage_enable_check, row, 0, 1, 2)
        row += 1
        
        # 保存图像
        self.save_images_check = QCheckBox("保存图像")
        self.save_images_check.setChecked(self.config.storage_service.save_images)
        layout.addWidget(self.save_images_check, row, 0, 1, 2)
        row += 1
        
        # 保存路径
        layout.addWidget(QLabel("保存路径:"), row, 0)
        path_layout = QHBoxLayout()
        self.save_path_edit = QLineEdit(self.config.storage_service.save_path)
        path_layout.addWidget(self.save_path_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_save_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout, row, 1)
        row += 1
        
        # 保存格式
        layout.addWidget(QLabel("保存格式:"), row, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["jpg", "png", "bmp"])
        self.format_combo.setCurrentText(self.config.storage_service.save_format)
        layout.addWidget(self.format_combo, row, 1)
        row += 1
        
        # 检测时保存
        self.save_on_det_check = QCheckBox("检测到目标时保存")
        self.save_on_det_check.setChecked(self.config.storage_service.save_on_detection)
        layout.addWidget(self.save_on_det_check, row, 0, 1, 2)
        row += 1
        
        layout.setRowStretch(row, 1)
        
        return widget
    
    def browse_model(self):
        """浏览模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择YOLO模型",
            "",
            "模型文件 (*.pt *.onnx);;所有文件 (*.*)"
        )
        if file_path:
            self.model_path_edit.setText(file_path)
    
    def browse_save_path(self):
        """浏览保存路径"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            ""
        )
        if dir_path:
            self.save_path_edit.setText(dir_path)
    
    def get_config(self):
        """获取配置"""
        # 更新相机配置
        self.config.camera_service.exposure_time = self.exposure_spin.value()
        self.config.camera_service.gain = self.gain_spin.value()
        self.config.camera_service.frame_rate = self.fps_spin.value()
        self.config.camera_service.trigger_mode = self.trigger_check.isChecked()
        self.config.camera_service.max_frames = self.max_frames_spin.value()
        
        # 更新YOLO配置
        self.config.yolo_service.enabled = self.yolo_enable_check.isChecked()
        self.config.yolo_service.model_path = self.model_path_edit.text()
        self.config.yolo_service.device = self.device_combo.currentText()
        self.config.yolo_service.confidence_threshold = self.confidence_spin.value()
        self.config.yolo_service.iou_threshold = self.iou_spin.value()
        
        # 更新显示配置
        self.config.display_service.enabled = self.display_enable_check.isChecked()
        self.config.display_service.show_fps = self.show_fps_check.isChecked()
        self.config.display_service.show_detections = self.show_det_check.isChecked()
        self.config.display_service.display_fps_limit = self.display_fps_spin.value()
        
        # 更新存储配置
        self.config.storage_service.enabled = self.storage_enable_check.isChecked()
        self.config.storage_service.save_images = self.save_images_check.isChecked()
        self.config.storage_service.save_path = self.save_path_edit.text()
        self.config.storage_service.save_format = self.format_combo.currentText()
        self.config.storage_service.save_on_detection = self.save_on_det_check.isChecked()
        
        return self.config


class CameraSelectDialog(QDialog):
    """相机选择对话框"""
    
    def __init__(self, camera_list, parent=None):
        super().__init__(parent)
        self.camera_list = camera_list
        self.selected_index = -1
        self.setWindowTitle("选择相机")
        self.setMinimumSize(400, 300)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 提示
        label = QLabel(f"找到 {len(self.camera_list)} 个相机设备，请选择:")
        layout.addWidget(label)
        
        # 相机列表
        # TODO: 添加相机列表显示
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
