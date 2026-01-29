# -*- coding: utf-8 -*-
"""
GUI启动测试脚本
测试GUI是否能正常启动（不显示窗口）
"""

import sys
import os

# 添加service_new根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
service_new_root = os.path.dirname(current_dir)
if service_new_root not in sys.path:
    sys.path.insert(0, service_new_root)

def test_gui_startup():
    """测试GUI启动"""
    print("=" * 60)
    print("GUI启动测试")
    print("=" * 60)
    
    try:
        print("\n[1/5] 导入PyQt5...")
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt, QTimer
        from PyQt5.QtGui import QPixmap, QColor, QFont
        print("✓ PyQt5导入成功")
        
        print("\n[2/5] 导入主窗口...")
        from main_window import MainWindow
        print("✓ 主窗口导入成功")
        
        print("\n[3/5] 创建应用...")
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        app.setStyle('Fusion')
        print("✓ 应用创建成功")
        
        print("\n[4/5] 创建主窗口...")
        window = MainWindow()
        print("✓ 主窗口创建成功")
        print(f"  窗口标题: {window.windowTitle()}")
        print(f"  窗口大小: {window.width()}x{window.height()}")
        
        print("\n[5/5] 测试启动画面...")
        from PyQt5.QtWidgets import QSplashScreen
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor(30, 30, 30))
        splash = QSplashScreen(pixmap)
        print("✓ 启动画面创建成功")
        
        print("\n" + "=" * 60)
        print("✓ GUI启动测试通过！")
        print("=" * 60)
        print("\n提示: 实际启动时会显示窗口")
        print("运行: python run_gui.py")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_gui_startup())
