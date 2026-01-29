# Qt GUI测试文件索引

本目录包含Qt图形界面版本的所有测试文件。

## 📚 测试文件列表

### 导入测试
- **test_qt.py** - Qt模块导入测试
  - 测试PyQt5是否正确安装
  - 测试Qt GUI模块导入
  - 验证依赖完整性

### GUI启动测试
- **test_gui_startup.py** - GUI启动测试
  - 测试主窗口创建
  - 测试界面初始化
  - 测试启动流程

## 🧪 测试说明

### test_qt.py
测试Qt相关模块的导入功能：
- PyQt5核心模块
- 自定义控件模块
- 对话框模块
- 样式模块
- 主窗口模块

### test_gui_startup.py
测试GUI启动流程：
- QApplication创建
- 主窗口初始化
- 界面组件加载
- 启动画面显示

## 🚀 运行测试

### 方法1：直接运行Python脚本
```bash
cd tests_qt

# 导入测试
python test_qt.py

# 启动测试
python test_gui_startup.py
```

### 方法2：使用pytest
```bash
cd tests_qt

# 运行所有测试
pytest

# 运行特定测试
pytest test_qt.py
pytest test_gui_startup.py

# 显示详细输出
pytest -v
```

### 方法3：使用批处理文件（待创建）
```bash
测试Qt版本.bat
```

## 📊 测试覆盖

### 已覆盖的功能
- ✅ PyQt5导入测试
- ✅ 主窗口创建测试
- ✅ 基本启动流程测试

### 待添加的测试
- ⏳ 界面交互测试
- ⏳ 控件功能测试
- ⏳ 对话框测试
- ⏳ 参数配置测试
- ⏳ 图像显示测试
- ⏳ 性能监控测试

## 📂 相关目录

- **Qt代码**: ../service_qt/
- **核心测试**: ../tests_core/
- **Qt文档**: ../docs_qt/

## 🔧 测试环境要求

### 必需依赖
- Python 3.7+
- PyQt5
- pytest
- pytest-qt（Qt测试支持）

### 安装测试依赖
```bash
pip install pytest pytest-qt
```

## 📝 Qt测试最佳实践

### 使用pytest-qt
```python
import pytest
from PyQt5.QtWidgets import QApplication

def test_main_window(qtbot):
    """测试主窗口"""
    from main_window import MainWindow
    
    # 创建窗口
    window = MainWindow()
    qtbot.addWidget(window)
    
    # 显示窗口
    window.show()
    
    # 验证窗口标题
    assert window.windowTitle() == "工业视觉系统"
```

### 测试按钮点击
```python
def test_button_click(qtbot):
    """测试按钮点击"""
    from PyQt5.QtWidgets import QPushButton
    
    button = QPushButton("测试")
    qtbot.addWidget(button)
    
    # 模拟点击
    with qtbot.waitSignal(button.clicked):
        button.click()
```

### 测试对话框
```python
def test_dialog(qtbot, monkeypatch):
    """测试对话框"""
    from PyQt5.QtWidgets import QMessageBox
    
    # 模拟用户点击OK
    monkeypatch.setattr(QMessageBox, 'exec_', lambda *args: QMessageBox.Ok)
    
    # 显示对话框
    result = QMessageBox.information(None, "测试", "测试消息")
    assert result == QMessageBox.Ok
```

## 📝 计划添加的测试

### 界面交互测试
- **test_camera_controls.py** - 相机控制测试
  - 测试相机参数设置
  - 测试采集控制
  - 测试参数保存

- **test_display_widget.py** - 显示控件测试
  - 测试图像显示
  - 测试缩放功能
  - 测试标注显示

- **test_config_dialog.py** - 配置对话框测试
  - 测试参数配置
  - 测试配置保存
  - 测试配置加载

### 功能测试
- **test_pipeline_integration.py** - 管道集成测试
  - 测试GUI与管道集成
  - 测试实时处理
  - 测试结果显示

- **test_performance_monitor.py** - 性能监控测试
  - 测试性能数据采集
  - 测试图表显示
  - 测试统计信息

## 📝 测试模板

### Qt控件测试模板
```python
# -*- coding: utf-8 -*-
"""
Qt控件测试
"""

import pytest
from PyQt5.QtWidgets import QWidget

def test_widget_creation(qtbot):
    """测试控件创建"""
    widget = QWidget()
    qtbot.addWidget(widget)
    
    # 验证控件
    assert widget is not None
    assert widget.isVisible() == False
    
    # 显示控件
    widget.show()
    assert widget.isVisible() == True
```

### Qt信号测试模板
```python
def test_signal_emission(qtbot):
    """测试信号发射"""
    from PyQt5.QtCore import QObject, pyqtSignal
    
    class TestObject(QObject):
        signal = pyqtSignal(str)
    
    obj = TestObject()
    
    # 等待信号
    with qtbot.waitSignal(obj.signal, timeout=1000) as blocker:
        obj.signal.emit("test")
    
    # 验证信号参数
    assert blocker.args == ["test"]
```

## 📝 文档维护

- 所有Qt GUI测试文件都应放在此目录
- 测试应覆盖主要界面功能
- 测试应使用pytest-qt框架
- 测试应包含清晰的注释
- 测试应定期运行和更新
