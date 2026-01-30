# -*- coding: utf-8 -*-
"""
Qt事件桥接器
连接EventBus和Qt信号系统，实现跨线程安全通信

响应任务：任务 17.1 - 创建 Qt 事件桥接
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtWidgets import QApplication
from typing import Dict, Any, Callable
import time

from core.event_bus import get_event_bus
from core.async_event_bus import get_async_event_bus


class QtEventBridge(QObject):
    """
    Qt事件桥接器
    
    功能：
    1. 将EventBus事件转换为Qt信号
    2. 跨线程安全通信
    3. UI降频控制
    4. 事件过滤和聚合
    """
    
    # Qt信号定义
    node_started = pyqtSignal(str, str)  # node_id, packet_id
    node_completed = pyqtSignal(str, float)  # node_id, execution_time
    node_error = pyqtSignal(str, str)  # node_id, error_message
    
    graph_started = pyqtSignal(str, int)  # graph_name, node_count
    graph_stopped = pyqtSignal(str)  # graph_name
    
    performance_updated = pyqtSignal(str, dict)  # node_id, metrics
    throughput_updated = pyqtSignal(str, dict)  # graph_id, metrics
    
    queue_status_changed = pyqtSignal(str, int)  # node_id, queue_size
    
    def __init__(self, parent=None):
        """初始化Qt事件桥接器"""
        super().__init__(parent)
        
        self.event_bus = get_event_bus()
        self.async_event_bus = get_async_event_bus()
        
        # UI更新控制
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self._process_ui_updates)
        self.ui_update_interval = 33  # 30 FPS (1000ms / 30 = 33ms)
        
        # 事件缓存（用于降频）
        self.cached_events = {}
        self.last_update_time = {}
        
        # 订阅事件
        self._subscribe_events()
        
    def _subscribe_events(self):
        """订阅EventBus事件"""
        # 节点事件
        self.event_bus.subscribe('node.start', self._on_node_start)
        self.event_bus.subscribe('node.complete', self._on_node_complete)
        self.event_bus.subscribe('node.error', self._on_node_error)
        
        # 图事件
        self.event_bus.subscribe('graph.start', self._on_graph_start)
        self.event_bus.subscribe('graph.stop', self._on_graph_stop)
        
        # 性能事件（需要降频）
        self.event_bus.subscribe('node.performance', self._on_performance_update)
        self.event_bus.subscribe('graph.throughput', self._on_throughput_update)
        
        # 队列事件
        self.event_bus.subscribe('queue.full', self._on_queue_status)
        self.event_bus.subscribe('queue.empty', self._on_queue_status)
    
    def start(self):
        """启动事件桥接"""
        self.ui_update_timer.start(self.ui_update_interval)
    
    def stop(self):
        """停止事件桥接"""
        self.ui_update_timer.stop()
    
    def _on_node_start(self, event_data: Dict[str, Any]):
        """处理节点开始事件"""
        node_id = event_data.get('node_id', '')
        packet_id = event_data.get('packet_id', '')
        
        # 直接发射信号（不需要降频）
        self.node_started.emit(node_id, packet_id)
    
    def _on_node_complete(self, event_data: Dict[str, Any]):
        """处理节点完成事件"""
        node_id = event_data.get('node_id', '')
        execution_time = event_data.get('execution_time', 0.0)
        
        self.node_completed.emit(node_id, execution_time)
    
    def _on_node_error(self, event_data: Dict[str, Any]):
        """处理节点错误事件"""
        node_id = event_data.get('node_id', '')
        error = event_data.get('error', '')
        
        self.node_error.emit(node_id, error)
    
    def _on_graph_start(self, event_data: Dict[str, Any]):
        """处理图开始事件"""
        graph_name = event_data.get('graph_name', '')
        node_count = event_data.get('node_count', 0)
        
        self.graph_started.emit(graph_name, node_count)
    
    def _on_graph_stop(self, event_data: Dict[str, Any]):
        """处理图停止事件"""
        graph_name = event_data.get('graph_name', '')
        
        self.graph_stopped.emit(graph_name)
    
    def _on_performance_update(self, event_data: Dict[str, Any]):
        """处理性能更新事件（需要降频）"""
        node_id = event_data.get('node_id', '')
        
        # 缓存事件数据
        self.cached_events[f'perf_{node_id}'] = {
            'type': 'performance',
            'node_id': node_id,
            'data': event_data
        }
    
    def _on_throughput_update(self, event_data: Dict[str, Any]):
        """处理吞吐量更新事件（需要降频）"""
        graph_id = event_data.get('graph_id', '')
        
        # 缓存事件数据
        self.cached_events[f'throughput_{graph_id}'] = {
            'type': 'throughput',
            'graph_id': graph_id,
            'data': event_data
        }
    
    def _on_queue_status(self, event_data: Dict[str, Any]):
        """处理队列状态事件"""
        node_id = event_data.get('node_id', '')
        size = event_data.get('size', 0)
        
        self.queue_status_changed.emit(node_id, size)
    
    def _process_ui_updates(self):
        """处理UI更新（30 FPS降频）"""
        current_time = time.time()
        
        # 处理缓存的事件
        for event_key, event_info in list(self.cached_events.items()):
            event_type = event_info['type']
            
            if event_type == 'performance':
                node_id = event_info['node_id']
                data = event_info['data']
                
                # 发射性能更新信号
                self.performance_updated.emit(node_id, data)
                
            elif event_type == 'throughput':
                graph_id = event_info['graph_id']
                data = event_info['data']
                
                # 发射吞吐量更新信号
                self.throughput_updated.emit(graph_id, data)
        
        # 清空缓存
        self.cached_events.clear()
    
    def set_ui_fps(self, fps: int):
        """设置UI更新频率"""
        if fps <= 0:
            fps = 1
        elif fps > 60:
            fps = 60
            
        self.ui_update_interval = int(1000 / fps)
        
        if self.ui_update_timer.isActive():
            self.ui_update_timer.stop()
            self.ui_update_timer.start(self.ui_update_interval)


# 全局实例
_qt_event_bridge = None


def get_qt_event_bridge() -> QtEventBridge:
    """获取Qt事件桥接器实例"""
    global _qt_event_bridge
    if _qt_event_bridge is None:
        _qt_event_bridge = QtEventBridge()
    return _qt_event_bridge
