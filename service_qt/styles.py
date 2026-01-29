# -*- coding: utf-8 -*-
"""
QSS样式表 - 海康威视风格
深色主题 + 蓝色强调色
"""


def get_hikvision_style():
    """
    获取海康威视风格的QSS样式
    
    配色方案:
    - 主背景: #1E1E1E (深灰)
    - 次背景: #2D2D2D (中灰)
    - 边框: #3E3E3E (浅灰)
    - 主色调: #00D9FF (青蓝色)
    - 强调色: #0099CC (深蓝)
    - 文字: #E0E0E0 (浅灰白)
    - 成功: #00CC66 (绿色)
    - 警告: #FFA500 (橙色)
    - 错误: #FF4444 (红色)
    """
    
    return """
/* ==================== 全局样式 ==================== */
QWidget {
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #1E1E1E;
}

/* ==================== 面板样式 ==================== */
QFrame#leftPanel, QFrame#rightPanel {
    background-color: #2D2D2D;
    border-right: 1px solid #3E3E3E;
}

QFrame#centerPanel {
    background-color: #1E1E1E;
}

/* ==================== 标题样式 ==================== */
QLabel#panelTitle {
    color: #00D9FF;
    font-size: 16px;
    font-weight: bold;
    padding: 5px;
    border-bottom: 2px solid #00D9FF;
    margin-bottom: 10px;
}

QLabel#fpsLabel {
    color: #00CC66;
    font-size: 14px;
    font-weight: bold;
    padding: 5px 10px;
    background-color: #2D2D2D;
    border: 1px solid #3E3E3E;
    border-radius: 3px;
}

QLabel#statValue {
    color: #00D9FF;
    font-size: 14px;
    font-weight: bold;
}

/* ==================== 分组框样式 ==================== */
QGroupBox {
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #00D9FF;
    background-color: #2D2D2D;
}

QGroupBox#controlGroup, QGroupBox#paramGroup {
    background-color: #252525;
}

/* ==================== 按钮样式 ==================== */
QPushButton {
    background-color: #3E3E3E;
    color: #E0E0E0;
    border: 1px solid #4E4E4E;
    border-radius: 4px;
    padding: 8px 15px;
    font-weight: bold;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #4E4E4E;
    border: 1px solid #00D9FF;
}

QPushButton:pressed {
    background-color: #2E2E2E;
}

QPushButton:disabled {
    background-color: #2A2A2A;
    color: #666666;
    border: 1px solid #333333;
}

/* 启动按钮 */
QPushButton#startButton {
    background-color: #00CC66;
    color: #FFFFFF;
    border: 1px solid #00DD77;
}

QPushButton#startButton:hover {
    background-color: #00DD77;
    border: 1px solid #00EE88;
}

QPushButton#startButton:pressed {
    background-color: #00AA55;
}

/* 停止按钮 */
QPushButton#stopButton {
    background-color: #FF4444;
    color: #FFFFFF;
    border: 1px solid #FF5555;
}

QPushButton#stopButton:hover {
    background-color: #FF5555;
    border: 1px solid #FF6666;
}

QPushButton#stopButton:pressed {
    background-color: #DD3333;
}

/* 普通按钮 */
QPushButton#normalButton {
    background-color: #0099CC;
    color: #FFFFFF;
    border: 1px solid #00AADD;
}

QPushButton#normalButton:hover {
    background-color: #00AADD;
    border: 1px solid #00D9FF;
}

QPushButton#normalButton:pressed {
    background-color: #0088BB;
}

/* ==================== 输入控件样式 ==================== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    border-radius: 3px;
    padding: 5px;
    min-height: 25px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #00D9FF;
}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {
    background-color: #252525;
    color: #666666;
}

/* 下拉框 */
QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #00D9FF;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #00D9FF;
    selection-background-color: #0099CC;
    selection-color: #FFFFFF;
}

/* 数字输入框按钮 */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #3E3E3E;
    border: 1px solid #4E4E4E;
    border-radius: 2px;
    width: 16px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #4E4E4E;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #3E3E3E;
    border: 1px solid #4E4E4E;
    border-radius: 2px;
    width: 16px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #4E4E4E;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #00D9FF;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #00D9FF;
}

/* ==================== 复选框样式 ==================== */
QCheckBox {
    spacing: 8px;
    color: #E0E0E0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3E3E3E;
    border-radius: 3px;
    background-color: #2D2D2D;
}

QCheckBox::indicator:hover {
    border: 2px solid #00D9FF;
}

QCheckBox::indicator:checked {
    background-color: #00D9FF;
    border: 2px solid #00D9FF;
    image: none;
}

QCheckBox::indicator:checked::after {
    content: "✓";
    color: #FFFFFF;
}

/* ==================== 标签页样式 ==================== */
QTabWidget::pane {
    border: 1px solid #3E3E3E;
    background-color: #2D2D2D;
    border-radius: 3px;
}

QTabBar::tab {
    background-color: #2D2D2D;
    color: #999999;
    border: 1px solid #3E3E3E;
    border-bottom: none;
    padding: 8px 15px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #0099CC;
    color: #FFFFFF;
    border-bottom: 2px solid #00D9FF;
}

QTabBar::tab:hover:!selected {
    background-color: #3E3E3E;
    color: #E0E0E0;
}

/* ==================== 表格样式 ==================== */
QTableWidget {
    background-color: #2D2D2D;
    alternate-background-color: #252525;
    gridline-color: #3E3E3E;
    border: 1px solid #3E3E3E;
    border-radius: 3px;
}

QTableWidget::item {
    color: #E0E0E0;
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #0099CC;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #3E3E3E;
    color: #00D9FF;
    padding: 8px;
    border: none;
    border-right: 1px solid #2D2D2D;
    border-bottom: 1px solid #2D2D2D;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #4E4E4E;
}

/* ==================== 文本框样式 ==================== */
QTextEdit {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    border-radius: 3px;
    padding: 5px;
}

QTextEdit#logText {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}

QTextEdit#statusText {
    font-size: 12px;
}

/* ==================== 滚动条样式 ==================== */
QScrollBar:vertical {
    background-color: #2D2D2D;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #4E4E4E;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5E5E5E;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2D2D2D;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #4E4E4E;
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5E5E5E;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ==================== 进度条样式 ==================== */
QProgressBar {
    background-color: #2D2D2D;
    border: 1px solid #3E3E3E;
    border-radius: 3px;
    text-align: center;
    color: #E0E0E0;
    height: 20px;
}

QProgressBar::chunk {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #0099CC,
        stop:1 #00D9FF
    );
    border-radius: 2px;
}

/* ==================== 图像显示区域 ==================== */
QLabel#imageDisplay {
    background-color: #1A1A1A;
    border: 2px solid #3E3E3E;
    border-radius: 5px;
    color: #666666;
    font-size: 16px;
}

/* ==================== 分割器样式 ==================== */
QSplitter::handle {
    background-color: #3E3E3E;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #00D9FF;
}

/* ==================== 状态栏样式 ==================== */
QStatusBar {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border-top: 1px solid #3E3E3E;
}

QStatusBar::item {
    border: none;
}

/* ==================== 工具提示样式 ==================== */
QToolTip {
    background-color: #3E3E3E;
    color: #E0E0E0;
    border: 1px solid #00D9FF;
    border-radius: 3px;
    padding: 5px;
}

/* ==================== 菜单样式 ==================== */
QMenuBar {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border-bottom: 1px solid #3E3E3E;
}

QMenuBar::item {
    padding: 5px 10px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #0099CC;
    color: #FFFFFF;
}

QMenu {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
}

QMenu::item {
    padding: 5px 25px 5px 10px;
}

QMenu::item:selected {
    background-color: #0099CC;
    color: #FFFFFF;
}

QMenu::separator {
    height: 1px;
    background-color: #3E3E3E;
    margin: 5px 0;
}
"""


def get_svg_icons():
    """
    获取SVG图标定义
    返回常用图标的SVG代码
    """
    
    icons = {
        # 播放图标
        "play": """
        <svg viewBox="0 0 24 24" fill="#00CC66">
            <path d="M8 5v14l11-7z"/>
        </svg>
        """,
        
        # 停止图标
        "stop": """
        <svg viewBox="0 0 24 24" fill="#FF4444">
            <rect x="6" y="6" width="12" height="12"/>
        </svg>
        """,
        
        # 相机图标
        "camera": """
        <svg viewBox="0 0 24 24" fill="#00D9FF">
            <path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/>
        </svg>
        """,
        
        # 设置图标
        "settings": """
        <svg viewBox="0 0 24 24" fill="#00D9FF">
            <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
        </svg>
        """,
        
        # 保存图标
        "save": """
        <svg viewBox="0 0 24 24" fill="#00D9FF">
            <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/>
        </svg>
        """,
        
        # 检测图标
        "detect": """
        <svg viewBox="0 0 24 24" fill="#00D9FF">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
        """
    }
    
    return icons
