"""
可视化DAG编辑器 - 主窗口
"""
import json
import sys
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QMenuBar, QAction, QFileDialog, QMessageBox,
                             QToolBar, QStatusBar, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.plugin_manager import PluginManager
from .canvas import GraphCanvas
from .plugin_palette import PluginPalette
from .config_panel import NodeConfigPanel


class DAGEditorWindow(QMainWindow):
    """DAG编辑器主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.plugin_manager = PluginManager()
        self.current_file = None
        self.node_configs = {}
        self.node_counter = 0
        
        self.init_ui()
        self.load_plugins()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("DAG 可视化编辑器")
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建主布局
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # 左侧：插件面板
        self.plugin_palette = PluginPalette()
        self.plugin_palette.plugin_selected.connect(self.on_plugin_selected)
        
        # 中间：画布
        self.canvas = GraphCanvas()
        
        # 右侧：配置面板
        self.config_panel = NodeConfigPanel()
        self.config_panel.config_changed.connect(self.on_config_changed)
        
        # 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.plugin_palette)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.config_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        clear_action = QAction("清空画布", self)
        clear_action.triggered.connect(self.clear_canvas)
        edit_menu.addAction(clear_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("重置缩放", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 新建
        new_action = QAction("新建", self)
        new_action.triggered.connect(self.new_file)
        toolbar.addAction(new_action)
        
        # 打开
        open_action = QAction("打开", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        # 保存
        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 验证
        validate_action = QAction("验证图", self)
        validate_action.triggered.connect(self.validate_graph)
        toolbar.addAction(validate_action)
    
    def load_plugins(self):
        """加载插件"""
        plugins_dir = Path(__file__).parent.parent.parent / "plugins"
        if plugins_dir.exists():
            self.plugin_manager.discover_plugins(str(plugins_dir))
            self.plugin_palette.load_plugins(self.plugin_manager)
            self.statusBar.showMessage(
                f"已加载 {len(self.plugin_manager.get_available_plugins())} 个插件"
            )
    
    def on_plugin_selected(self, plugin_type: str, plugin_name: str):
        """插件被选中"""
        # 生成节点ID
        self.node_counter += 1
        node_id = f"{plugin_type}_{self.node_counter}"
        
        # 添加节点到画布
        self.canvas.add_node(node_id, plugin_type, 100, 100)
        
        # 初始化配置
        self.node_configs[node_id] = {}
        
        self.statusBar.showMessage(f"已添加节点: {node_id}")
    
    def on_config_changed(self, node_id: str, config: dict):
        """配置变更"""
        self.node_configs[node_id] = config
        self.statusBar.showMessage(f"已更新节点配置: {node_id}")
    
    def new_file(self):
        """新建文件"""
        reply = QMessageBox.question(
            self, "新建", "确定要新建文件吗？未保存的更改将丢失。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.canvas.clear()
            self.node_configs.clear()
            self.node_counter = 0
            self.current_file = None
            self.statusBar.showMessage("已新建文件")
    
    def open_file(self):
        """打开文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "打开配置文件", "", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载图数据
                self.canvas.load_graph_data(data)
                
                # 加载配置
                self.node_configs = data.get("node_configs", {})
                
                self.current_file = filename
                self.statusBar.showMessage(f"已打开: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开文件失败: {e}")
    
    def save_file(self):
        """保存文件"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """另存为"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "JSON Files (*.json)"
        )
        
        if filename:
            self._save_to_file(filename)
            self.current_file = filename
    
    def _save_to_file(self, filename: str):
        """保存到文件"""
        try:
            # 获取图数据
            graph_data = self.canvas.get_graph_data()
            
            # 添加配置
            graph_data["node_configs"] = self.node_configs
            
            # 保存
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            
            self.statusBar.showMessage(f"已保存: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败: {e}")
    
    def clear_canvas(self):
        """清空画布"""
        reply = QMessageBox.question(
            self, "清空", "确定要清空画布吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.canvas.clear()
            self.node_configs.clear()
            self.statusBar.showMessage("已清空画布")
    
    def validate_graph(self):
        """验证图"""
        graph_data = self.canvas.get_graph_data()
        
        # 简单验证
        node_count = len(graph_data["nodes"])
        conn_count = len(graph_data["connections"])
        
        # 检查循环
        has_cycle = self._check_cycle(graph_data)
        
        if has_cycle:
            QMessageBox.warning(self, "验证", "图中存在循环！")
        else:
            QMessageBox.information(
                self, "验证",
                f"图验证通过！\n节点数: {node_count}\n连接数: {conn_count}"
            )
    
    def _check_cycle(self, graph_data: dict) -> bool:
        """检查循环（简化版）"""
        # TODO: 实现完整的循环检测
        return False
    
    def zoom_in(self):
        """放大"""
        self.canvas.scale(1.2, 1.2)
    
    def zoom_out(self):
        """缩小"""
        self.canvas.scale(0.8, 0.8)
    
    def reset_zoom(self):
        """重置缩放"""
        self.canvas.resetTransform()
    
    def show_about(self):
        """显示关于"""
        QMessageBox.about(
            self, "关于",
            "DAG 可视化编辑器 v1.0\n\n"
            "用于创建和编辑DAG流水线配置\n\n"
            "开发: Kiro AI Assistant"
        )


def main():
    """主函数"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = DAGEditorWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
