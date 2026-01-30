# -*- coding: utf-8 -*-
"""
实时监控面板
显示系统性能指标和运行状态

响应任务：任务 17.3 - 实现实时监控面板
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QTableWidget, QTableWidgetItem,
                             QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg
from collections import deque
from typing import Dict, Any
import time

from ui.event_bridge import get_qt_event_bridge


class PerformanceWidget(QWidget):
    """
    性能监控Widget
    
    功能：
    1. 实时FPS显示
    2. 节点执行时间统计
    3. 错误计数显示
    4. 性能曲线图
    """
    
    def __init__(self, parent=None):
        """初始化性能监控Widget"""
        super().__init__(parent)
        
        self.event_bridge = get_qt_event_bridge()
        
        # 数据存储
        self.node_metrics = {}
        self.fps_history = deque(maxlen=100)
        self.time_history = deque(maxlen=100)
        
        # 初始化UI
        self._init_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_displays)
        self.update_timer.start(1000)  # 每秒更新一次
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 系统概览
        overview_group = self._create_overview_group()
        layout.addWidget(overview_group)
        
        # 节点性能表格
        nodes_group = self._create_nodes_group()
        layout.addWidget(nodes_group)
        
        # 性能图表
        charts_group = self._create_charts_group()
        layout.addWidget(charts_group)
    
    def _create_overview_group(self) -> QGroupBox:
        """创建系统概览组"""
        group = QGroupBox("系统概览")
        layout = QGridLayout(group)
        
        # FPS显示
        layout.addWidget(QLabel("系统FPS:"), 0, 0)
        self.fps_label = QLabel("0.0")
        self.fps_label.setStyleSheet("font-size: 18px; font-weight: bold; color: green;")
        layout.addWidget(self.fps_label, 0, 1)
        
        # 运行状态
        layout.addWidget(QLabel("运行状态:"), 0, 2)
        self.status_label = QLabel("停止")
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
        layout.addWidget(self.status_label, 0, 3)
        
        # 总节点数
        layout.addWidget(QLabel("活跃节点:"), 1, 0)
        self.nodes_count_label = QLabel("0")
        layout.addWidget(self.nodes_count_label, 1, 1)
        
        # 总错误数
        layout.addWidget(QLabel("总错误数:"), 1, 2)
        self.errors_count_label = QLabel("0")
        self.errors_count_label.setStyleSheet("color: red;")
        layout.addWidget(self.errors_count_label, 1, 3)
        
        return group
    
    def _create_nodes_group(self) -> QGroupBox:
        """创建节点性能组"""
        group = QGroupBox("节点性能")
        layout = QVBoxLayout(group)
        
        # 节点性能表格
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(6)
        self.nodes_table.setHorizontalHeaderLabels([
            "节点ID", "执行次数", "平均耗时(ms)", "错误次数", "错误率(%)", "状态"
        ])
        
        # 设置表格样式
        self.nodes_table.setAlternatingRowColors(True)
        self.nodes_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.nodes_table)
        
        return group
    
    def _create_charts_group(self) -> QGroupBox:
        """创建图表组"""
        group = QGroupBox("性能图表")
        layout = QHBoxLayout(group)
        
        # FPS曲线图
        self.fps_plot = pg.PlotWidget(title="系统FPS")
        self.fps_plot.setLabel('left', 'FPS')
        self.fps_plot.setLabel('bottom', '时间(s)')
        self.fps_curve = self.fps_plot.plot(pen='g')
        layout.addWidget(self.fps_plot)
        
        # 执行时间曲线图
        self.time_plot = pg.PlotWidget(title="平均执行时间")
        self.time_plot.setLabel('left', '时间(ms)')
        self.time_plot.setLabel('bottom', '时间(s)')
        self.time_curves = {}  # node_id -> curve
        layout.addWidget(self.time_plot)
        
        return group
    
    def _connect_signals(self):
        """连接事件信号"""
        # 图事件
        self.event_bridge.graph_started.connect(self._on_graph_started)
        self.event_bridge.graph_stopped.connect(self._on_graph_stopped)
        
        # 节点事件
        self.event_bridge.node_completed.connect(self._on_node_completed)
        self.event_bridge.node_error.connect(self._on_node_error)
        
        # 性能事件
        self.event_bridge.performance_updated.connect(self._on_performance_updated)
        self.event_bridge.throughput_updated.connect(self._on_throughput_updated)
    
    def _on_graph_started(self, graph_name: str, node_count: int):
        """处理图开始事件"""
        self.status_label.setText("运行中")
        self.status_label.setStyleSheet("font-size: 14px; color: green;")
        self.nodes_count_label.setText(str(node_count))
    
    def _on_graph_stopped(self, graph_name: str):
        """处理图停止事件"""
        self.status_label.setText("已停止")
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
    
    def _on_node_completed(self, node_id: str, execution_time: float):
        """处理节点完成事件"""
        if node_id not in self.node_metrics:
            self.node_metrics[node_id] = {
                'execution_count': 0,
                'error_count': 0,
                'total_time': 0.0,
                'recent_times': deque(maxlen=10)
            }
        
        metrics = self.node_metrics[node_id]
        metrics['execution_count'] += 1
        metrics['total_time'] += execution_time
        metrics['recent_times'].append(execution_time * 1000)  # 转换为毫秒
    
    def _on_node_error(self, node_id: str, error_message: str):
        """处理节点错误事件"""
        if node_id not in self.node_metrics:
            self.node_metrics[node_id] = {
                'execution_count': 0,
                'error_count': 0,
                'total_time': 0.0,
                'recent_times': deque(maxlen=10)
            }
        
        self.node_metrics[node_id]['error_count'] += 1
    
    def _on_performance_updated(self, node_id: str, data: Dict[str, Any]):
        """处理性能更新事件"""
        # 更新节点指标
        if node_id not in self.node_metrics:
            self.node_metrics[node_id] = {
                'execution_count': 0,
                'error_count': 0,
                'total_time': 0.0,
                'recent_times': deque(maxlen=10)
            }
        
        metrics = self.node_metrics[node_id]
        metrics.update({
            'execution_count': data.get('execution_count', 0),
            'error_count': data.get('error_count', 0),
            'average_time': data.get('average_time', 0.0),
            'error_rate': data.get('error_rate', 0.0)
        })
    
    def _on_throughput_updated(self, graph_id: str, data: Dict[str, Any]):
        """处理吞吐量更新事件"""
        current_fps = data.get('current_fps', 0.0)
        
        # 更新FPS历史
        current_time = time.time()
        self.fps_history.append((current_time, current_fps))
        
        # 更新FPS显示
        self.fps_label.setText(f"{current_fps:.1f}")
    
    def _update_displays(self):
        """更新显示内容"""
        self._update_nodes_table()
        self._update_charts()
    
    def _update_nodes_table(self):
        """更新节点表格"""
        self.nodes_table.setRowCount(len(self.node_metrics))
        
        for row, (node_id, metrics) in enumerate(self.node_metrics.items()):
            # 节点ID
            self.nodes_table.setItem(row, 0, QTableWidgetItem(node_id))
            
            # 执行次数
            exec_count = metrics.get('execution_count', 0)
            self.nodes_table.setItem(row, 1, QTableWidgetItem(str(exec_count)))
            
            # 平均执行时间
            avg_time = metrics.get('average_time', 0.0) * 1000  # 转换为毫秒
            self.nodes_table.setItem(row, 2, QTableWidgetItem(f"{avg_time:.1f}"))
            
            # 错误次数
            error_count = metrics.get('error_count', 0)
            self.nodes_table.setItem(row, 3, QTableWidgetItem(str(error_count)))
            
            # 错误率
            error_rate = metrics.get('error_rate', 0.0) * 100
            self.nodes_table.setItem(row, 4, QTableWidgetItem(f"{error_rate:.1f}"))
            
            # 状态
            status = "运行中" if exec_count > 0 else "空闲"
            self.nodes_table.setItem(row, 5, QTableWidgetItem(status))
        
        # 调整列宽
        self.nodes_table.resizeColumnsToContents()
    
    def _update_charts(self):
        """更新图表"""
        # 更新FPS曲线
        if self.fps_history:
            times, fps_values = zip(*self.fps_history)
            base_time = times[0] if times else 0
            relative_times = [(t - base_time) for t in times]
            self.fps_curve.setData(relative_times, fps_values)
        
        # 更新执行时间曲线
        current_time = time.time()
        for node_id, metrics in self.node_metrics.items():
            recent_times = metrics.get('recent_times', [])
            if recent_times and node_id not in self.time_curves:
                # 为新节点创建曲线
                pen = pg.mkPen(color=pg.intColor(len(self.time_curves)))
                self.time_curves[node_id] = self.time_plot.plot(
                    pen=pen, name=node_id
                )
            
            if node_id in self.time_curves and recent_times:
                # 更新曲线数据
                x_data = list(range(len(recent_times)))
                self.time_curves[node_id].setData(x_data, list(recent_times))


class MonitoringPanel(QWidget):
    """
    监控面板主Widget
    整合所有监控功能
    """
    
    def __init__(self, parent=None):
        """初始化监控面板"""
        super().__init__(parent)
        
        self._init_ui()
        
        # 启动事件桥接
        self.event_bridge = get_qt_event_bridge()
        self.event_bridge.start()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 性能监控Widget
        self.performance_widget = PerformanceWidget()
        layout.addWidget(self.performance_widget)
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止事件桥接
        self.event_bridge.stop()
        super().closeEvent(event)
