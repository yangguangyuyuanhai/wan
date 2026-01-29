# -*- coding: utf-8 -*-
"""
Qt模块测试脚本
"""

import sys
import os

# 添加service_new根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
service_new_root = os.path.dirname(current_dir)
if service_new_root not in sys.path:
    sys.path.insert(0, service_new_root)

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("Qt模块导入测试")
    print("=" * 60)
    
    results = []
    
    # 测试PyQt5
    print("\n【PyQt5】")
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPixmap
        print("✓ PyQt5基础模块")
        results.append(True)
    except Exception as e:
        print(f"✗ PyQt5基础模块: {e}")
        results.append(False)
    
    # 测试样式模块
    print("\n【样式模块】")
    try:
        from styles import get_hikvision_style, get_svg_icons
        style = get_hikvision_style()
        icons = get_svg_icons()
        print(f"✓ styles.py (样式长度: {len(style)} 字符, 图标数: {len(icons)})")
        results.append(True)
    except Exception as e:
        print(f"✗ styles.py: {e}")
        results.append(False)
    
    # 测试控件模块
    print("\n【控件模块】")
    try:
        from widgets import (ImageDisplayWidget, StatusIndicator, 
                            PerformanceChart, CameraListWidget, 
                            DetectionResultWidget)
        print("✓ widgets.py (5个自定义控件)")
        results.append(True)
    except Exception as e:
        print(f"✗ widgets.py: {e}")
        results.append(False)
    
    # 测试对话框模块
    print("\n【对话框模块】")
    try:
        from dialogs import AboutDialog, ConfigDialog, CameraSelectDialog
        print("✓ dialogs.py (3个对话框)")
        results.append(True)
    except Exception as e:
        print(f"✗ dialogs.py: {e}")
        results.append(False)
    
    # 测试主窗口
    print("\n【主窗口】")
    try:
        from main_window import MainWindow, VisionWorkerThread
        print("✓ main_window.py")
        results.append(True)
    except Exception as e:
        print(f"✗ main_window.py: {e}")
        results.append(False)
    
    # 测试后端依赖
    print("\n【后端依赖】")
    try:
        from pipeline_config import PipelineConfig, PresetConfigs
        from scheduler import PipelineScheduler
        from logger_config import get_logger
        print("✓ 后端模块依赖")
        results.append(True)
    except Exception as e:
        print(f"✗ 后端模块依赖: {e}")
        results.append(False)
    
    # 统计结果
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有Qt模块测试通过！")
        return 0
    else:
        print(f"✗ {total - passed} 个模块测试失败")
        return 1

def test_window_creation():
    """测试窗口创建（不显示）"""
    print("\n" + "=" * 60)
    print("窗口创建测试")
    print("=" * 60)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from main_window import MainWindow
        
        # 创建应用（不显示）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        print("✓ 主窗口创建成功")
        
        # 检查窗口属性
        print(f"  窗口标题: {window.windowTitle()}")
        print(f"  窗口大小: {window.width()}x{window.height()}")
        print(f"  配置模式: {window.config.mode.value}")
        
        return 0
        
    except Exception as e:
        print(f"✗ 窗口创建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    result1 = test_imports()
    result2 = test_window_creation()
    
    print("\n" + "=" * 60)
    if result1 == 0 and result2 == 0:
        print("✓ 所有测试通过！Qt界面可以正常运行")
    else:
        print("✗ 部分测试失败，请检查错误信息")
    print("=" * 60)
    
    sys.exit(max(result1, result2))
