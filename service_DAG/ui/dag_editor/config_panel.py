"""
可视化DAG编辑器 - 节点配置面板
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel, 
                             QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                             QComboBox, QPushButton, QScrollArea, QGroupBox)
from PyQt5.QtCore import pyqtSignal


class NodeConfigPanel(QWidget):
    """节点配置面板"""
    
    config_changed = pyqtSignal(str, dict)  # (node_id, config)
    
    def __init__(self):
        super().__init__()
        
        self.current_node_id = None
        self.config_widgets = {}
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题
        self.title_label = QLabel("节点配置")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 配置表单容器
        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        self.form_widget.setLayout(self.form_layout)
        
        scroll.setWidget(self.form_widget)
        layout.addWidget(scroll)
        
        # 应用按钮
        self.apply_button = QPushButton("应用配置")
        self.apply_button.clicked.connect(self.apply_config)
        layout.addWidget(self.apply_button)
        
        self.setLayout(layout)
        self.setMinimumWidth(250)
    
    def load_node_config(self, node_id: str, node_type: str, config: dict):
        """加载节点配置"""
        self.current_node_id = node_id
        self.title_label.setText(f"节点配置: {node_id}")
        
        # 清空现有配置
        self.clear_config()
        
        # 根据节点类型加载配置项
        self.load_config_schema(node_type, config)
    
    def clear_config(self):
        """清空配置"""
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.config_widgets.clear()
    
    def load_config_schema(self, node_type: str, config: dict):
        """加载配置模式"""
        # 通用配置项
        common_configs = {
            "enabled": ("启用", "bool", True),
            "timeout": ("超时(秒)", "int", 30),
        }
        
        # 节点特定配置
        node_configs = {
            "camera_hik": {
                "exposure_time": ("曝光时间", "int", 10000),
                "gain": ("增益", "float", 10.0),
                "frame_rate": ("帧率", "float", 30.0),
            },
            "yolo_v8": {
                "model_path": ("模型路径", "str", "./models/yolov8n.pt"),
                "confidence_threshold": ("置信度阈值", "float", 0.5),
                "device": ("设备", "choice", ["cpu", "cuda"]),
            },
            "display": {
                "window_name": ("窗口名称", "str", "Display"),
                "show_fps": ("显示FPS", "bool", True),
            }
        }
        
        # 合并配置
        configs = {}
        configs.update(common_configs)
        if node_type in node_configs:
            configs.update(node_configs[node_type])
        
        # 创建配置控件
        for key, (label, type_, default) in configs.items():
            value = config.get(key, default)
            widget = self.create_config_widget(type_, value)
            
            self.form_layout.addRow(label, widget)
            self.config_widgets[key] = (widget, type_)
    
    def create_config_widget(self, type_: str, value):
        """创建配置控件"""
        if type_ == "str":
            widget = QLineEdit(str(value))
            return widget
        
        elif type_ == "int":
            widget = QSpinBox()
            widget.setRange(0, 1000000)
            widget.setValue(int(value))
            return widget
        
        elif type_ == "float":
            widget = QDoubleSpinBox()
            widget.setRange(0.0, 10000.0)
            widget.setValue(float(value))
            return widget
        
        elif type_ == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            return widget
        
        elif type_ == "choice":
            widget = QComboBox()
            if isinstance(value, list):
                widget.addItems(value)
            return widget
        
        else:
            return QLineEdit(str(value))
    
    def apply_config(self):
        """应用配置"""
        if not self.current_node_id:
            return
        
        config = {}
        for key, (widget, type_) in self.config_widgets.items():
            if type_ == "str":
                config[key] = widget.text()
            elif type_ == "int":
                config[key] = widget.value()
            elif type_ == "float":
                config[key] = widget.value()
            elif type_ == "bool":
                config[key] = widget.isChecked()
            elif type_ == "choice":
                config[key] = widget.currentText()
        
        self.config_changed.emit(self.current_node_id, config)
