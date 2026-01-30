#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt界面集成测试脚本
测试事件桥接、UI更新响应和降频机制

响应任务：任务 17.4 - 添加 UI 集成测试
"""

import sys
import asyncio
import time
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer, QThread, pyqtSignal

from ui.event_bridge import get_qt_event_bridge
from ui.monitoring_panel import MonitoringPanel
from core.event_bus import get_event_bus
from core.async_event_bus import get_async_event_bus


class EventSimulator(QThread):
    """事件模拟器线程"""
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.event_bus = get_event_bus()
        
    def start_simulation(self):
        """开始模拟"""
        self.running = True
        self.start()
        
    def stop_simulation(self):
        """停止模拟"""
        self.running = False
        self.wait()
    
    def run(self):
        """运行模拟"""
        frame_count = 0
        
        # 模拟图开始
        self.event_bus.publish('graph.start', {
            'graph_name': 'test_pipeline',
            'node_count': 4
        })
        
        while self.running:
            frame_count += 1
            
            # 模拟节点执行
            test_nodes = ['camera_source', 'yolo_detector', 'opencv_processor', 'display']
            
            for node_id in test_nodes:
                # 节点开始
                self.event_bus.publish('node.start', {
                    'node_id': node_id,
                    'packet_id': f'frame_{frame_count}'
                })
                
                # 模拟执行时间
                execution_time = random.uniform(0.01, 0.1)
                self.msleep(int(execution_time * 1000))
                
                # 节点完成或错误
                if random.random() > 0.05:  # 95% 成功率
                    self.event_bus.publish('node.complete', {
                        'node_id': node_id,
                        'packet_id': f'frame_{frame_count}',
                        'execution_time': execution_time
                    })
                else:
                    self.event_bus.publish('node.error', {
                        'node_id': node_id,
                        'packet_id': f'frame_{frame_count}',
                        'error': 'simulated error'
                    })
                
                # 发布性能事件
                self.event_bus.publish('node.performance', {
                    'node_id': node_id,
                    'execution_count': frame_count,
                    'error_count': max(0, frame_count // 20),
                    'error_rate': 0.05,
                    'average_time': execution_time,
                    'recent_average': execution_time
                })
            
            # 发布吞吐量事件
            current_fps = random.uniform(25.0, 30.0)
            self.event_bus.publish('graph.throughput', {
                'graph_id': 'test_pipeline',
                'total_frames': frame_count,
                'successful_frames': int(frame_count * 0.95),
                'error_frames': frame_count - int(frame_count * 0.95),
                'success_rate': 0.95,
                'current_fps': current_fps,
                'uptime': frame_count * 0.033
            })
            
            # 模拟帧间隔
            self.msleep(33)  # 约30 FPS
        
        # 模拟图停止
        self.event_bus.publish('graph.stop', {
            'graph_name': 'test_pipeline'
        })


class UITestWindow(QMainWindow):
    """UI测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt界面集成测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 事件模拟器
        self.simulator = EventSimulator()
        
        # 初始化UI
        self._init_ui()
        
        # 测试结果
        self.test_results = {}
        
        # 测试计时器
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self._run_tests)
        
    def _init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 控制按钮
        self.start_button = QPushButton("开始模拟")
        self.start_button.clicked.connect(self._start_simulation)
        layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止模拟")
        self.stop_button.clicked.connect(self._stop_simulation)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        self.test_button = QPushButton("运行测试")
        self.test_button.clicked.connect(self._start_tests)
        layout.addWidget(self.test_button)
        
        # 监控面板
        self.monitoring_panel = MonitoringPanel()
        layout.addWidget(self.monitoring_panel)
        
    def _start_simulation(self):
        """开始模拟"""
        self.simulator.start_simulation()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
    def _stop_simulation(self):
        """停止模拟"""
        self.simulator.stop_simulation()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def _start_tests(self):
        """开始测试"""
        print("开始UI集成测试...")
        
        # 启动测试定时器
        self.test_start_time = time.time()
        self.test_timer.start(5000)  # 5秒后运行测试
        
        # 开始模拟
        self._start_simulation()
        
    def _run_tests(self):
        """运行测试"""
        self.test_timer.stop()
        
        print("运行测试检查...")
        
        # 测试1: 事件桥接功能
        self._test_event_bridge()
        
        # 测试2: UI更新响应
        self._test_ui_updates()
        
        # 测试3: 降频机制
        self._test_throttling()
        
        # 停止模拟
        self._stop_simulation()
        
        # 输出测试结果
        self._print_test_results()
        
    def _test_event_bridge(self):
        """测试事件桥接功能"""
        try:
            event_bridge = get_qt_event_bridge()
            
            # 检查信号连接
            signal_count = 0
            
            # 检查各种信号是否存在
            signals = [
                'node_started', 'node_completed', 'node_error',
                'graph_started', 'graph_stopped',
                'performance_updated', 'throughput_updated'
            ]
            
            for signal_name in signals:
                if hasattr(event_bridge, signal_name):
                    signal_count += 1
            
            if signal_count == len(signals):
                self.test_results['event_bridge'] = "成功"
            else:
                self.test_results['event_bridge'] = f"部分成功: {signal_count}/{len(signals)}"
                
        except Exception as e:
            self.test_results['event_bridge'] = f"异常: {e}"
    
    def _test_ui_updates(self):
        """测试UI更新响应"""
        try:
            # 检查监控面板是否有数据
            performance_widget = self.monitoring_panel.performance_widget
            
            # 检查节点指标
            node_count = len(performance_widget.node_metrics)
            
            # 检查FPS历史
            fps_count = len(performance_widget.fps_history)
            
            # 检查表格行数
            table_rows = performance_widget.nodes_table.rowCount()
            
            if node_count > 0 and fps_count > 0 and table_rows > 0:
                self.test_results['ui_updates'] = "成功"
            else:
                self.test_results['ui_updates'] = f"数据不足: nodes={node_count}, fps={fps_count}, rows={table_rows}"
                
        except Exception as e:
            self.test_results['ui_updates'] = f"异常: {e}"
    
    def _test_throttling(self):
        """测试降频机制"""
        try:
            event_bridge = get_qt_event_bridge()
            
            # 检查UI更新间隔
            update_interval = event_bridge.ui_update_interval
            expected_interval = 33  # 30 FPS
            
            if abs(update_interval - expected_interval) <= 5:  # 允许5ms误差
                self.test_results['throttling'] = "成功"
            else:
                self.test_results['throttling'] = f"间隔不正确: {update_interval}ms (期望{expected_interval}ms)"
                
        except Exception as e:
            self.test_results['throttling'] = f"异常: {e}"
    
    def _print_test_results(self):
        """输出测试结果"""
        print("\n" + "=" * 60)
        print("Qt界面集成测试结果")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✓" if "成功" in result else "✗"
            print(f"{status} {test_name}: {result}")
        
        # 统计
        success_count = sum(1 for result in self.test_results.values() if "成功" in result)
        total_count = len(self.test_results)
        
        print(f"\n总体结果: {success_count}/{total_count} 项测试通过")
        
        if success_count == total_count:
            print("🎉 Qt界面集成测试全部通过！")
        else:
            print("⚠️  部分测试未通过，请检查上述结果")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.simulator.isRunning():
            self.simulator.stop_simulation()
        super().closeEvent(event)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = UITestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
