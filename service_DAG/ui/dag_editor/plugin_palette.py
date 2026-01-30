"""
可视化DAG编辑器 - 插件面板
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                             QListWidgetItem, QLabel, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal


class PluginPalette(QWidget):
    """插件面板"""
    
    plugin_selected = pyqtSignal(str, str)  # (plugin_type, plugin_name)
    
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        self.plugins = {}
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("可用插件")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索插件...")
        self.search_box.textChanged.connect(self.filter_plugins)
        layout.addWidget(self.search_box)
        
        # 插件列表
        self.plugin_list = QListWidget()
        self.plugin_list.itemDoubleClicked.connect(self.on_plugin_double_clicked)
        layout.addWidget(self.plugin_list)
        
        self.setLayout(layout)
        self.setMinimumWidth(200)
    
    def load_plugins(self, plugin_manager):
        """加载插件列表"""
        self.plugin_list.clear()
        self.plugins.clear()
        
        for plugin_type in plugin_manager.get_available_plugins():
            metadata = plugin_manager.get_plugin_metadata(plugin_type)
            
            # 创建列表项
            item = QListWidgetItem(metadata.get("name", plugin_type))
            item.setData(Qt.UserRole, plugin_type)
            item.setToolTip(metadata.get("description", ""))
            
            self.plugin_list.addItem(item)
            self.plugins[plugin_type] = metadata
    
    def filter_plugins(self, text: str):
        """过滤插件"""
        for i in range(self.plugin_list.count()):
            item = self.plugin_list.item(i)
            plugin_type = item.data(Qt.UserRole)
            plugin_name = item.text()
            
            # 检查是否匹配
            visible = (text.lower() in plugin_name.lower() or 
                      text.lower() in plugin_type.lower())
            item.setHidden(not visible)
    
    def on_plugin_double_clicked(self, item: QListWidgetItem):
        """插件双击事件"""
        plugin_type = item.data(Qt.UserRole)
        plugin_name = item.text()
        self.plugin_selected.emit(plugin_type, plugin_name)
