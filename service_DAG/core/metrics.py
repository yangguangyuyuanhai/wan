# -*- coding: utf-8 -*-
"""
性能指标收集器
实现系统性能监控和可观察性

响应任务：任务 16.1 - 实现性能指标收集
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque
import threading

from core.event_bus import get_event_bus


@dataclass
class NodeMetrics:
    """节点性能指标"""
    node_id: str
    execution_count: int = 0
    error_count: int = 0
    total_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def add_execution(self, execution_time: float, success: bool = True):
        """添加执行记录"""
        self.execution_count += 1
        if not success:
            self.error_count += 1
            return
            
        self.total_execution_time += execution_time
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        self.recent_times.append(execution_time)
    
    def get_average_time(self) -> float:
        """获取平均执行时间"""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / (self.execution_count - self.error_count)
    
    def get_recent_average(self) -> float:
        """获取最近的平均执行时间"""
        if not self.recent_times:
            return 0.0
        return sum(self.recent_times) / len(self.recent_times)
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.execution_count == 0:
            return 0.0
        return self.error_count / self.execution_count


@dataclass
class GraphMetrics:
    """图性能指标"""
    graph_id: str
    start_time: float = 0.0
    total_frames: int = 0
    successful_frames: int = 0
    error_frames: int = 0
    recent_fps: deque = field(default_factory=lambda: deque(maxlen=30))
    last_frame_time: float = 0.0
    
    def add_frame(self, success: bool = True):
        """添加帧记录"""
        current_time = time.time()
        self.total_frames += 1
        
        if success:
            self.successful_frames += 1
        else:
            self.error_frames += 1
        
        # 计算FPS
        if self.last_frame_time > 0:
            frame_interval = current_time - self.last_frame_time
            if frame_interval > 0:
                fps = 1.0 / frame_interval
                self.recent_fps.append(fps)
        
        self.last_frame_time = current_time
    
    def get_current_fps(self) -> float:
        """获取当前FPS"""
        if not self.recent_fps:
            return 0.0
        return sum(self.recent_fps) / len(self.recent_fps)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_frames == 0:
            return 0.0
        return self.successful_frames / self.total_frames


class MetricsCollector:
    """
    性能指标收集器
    
    功能：
    1. 收集节点执行指标
    2. 收集图整体指标
    3. 计算移动平均值
    4. 发布性能事件
    """
    
    def __init__(self):
        """初始化指标收集器"""
        self.event_bus = get_event_bus()
        
        # 指标存储
        self.node_metrics: Dict[str, NodeMetrics] = {}
        self.graph_metrics: Dict[str, GraphMetrics] = {}
        
        # 发布控制
        self.last_publish_time = 0.0
        self.publish_interval = 1.0  # 每秒发布一次
        
        # 运行状态
        self.running = False
        self.publish_task: Optional[asyncio.Task] = None
        
        # 订阅事件
        self._subscribe_events()
    
    def _subscribe_events(self):
        """订阅相关事件"""
        self.event_bus.subscribe('node.start', self._on_node_start)
        self.event_bus.subscribe('node.complete', self._on_node_complete)
        self.event_bus.subscribe('node.error', self._on_node_error)
        self.event_bus.subscribe('graph.start', self._on_graph_start)
        self.event_bus.subscribe('graph.frame_complete', self._on_frame_complete)
    
    def _on_node_start(self, event_data: Dict[str, Any]):
        """处理节点开始事件"""
        node_id = event_data.get('node_id')
        if node_id and node_id not in self.node_metrics:
            self.node_metrics[node_id] = NodeMetrics(node_id=node_id)
    
    def _on_node_complete(self, event_data: Dict[str, Any]):
        """处理节点完成事件"""
        node_id = event_data.get('node_id')
        execution_time = event_data.get('execution_time', 0.0)
        
        if node_id in self.node_metrics:
            self.node_metrics[node_id].add_execution(execution_time, success=True)
    
    def _on_node_error(self, event_data: Dict[str, Any]):
        """处理节点错误事件"""
        node_id = event_data.get('node_id')
        
        if node_id in self.node_metrics:
            self.node_metrics[node_id].add_execution(0.0, success=False)
    
    def _on_graph_start(self, event_data: Dict[str, Any]):
        """处理图开始事件"""
        graph_id = event_data.get('graph_name', 'default')
        if graph_id not in self.graph_metrics:
            self.graph_metrics[graph_id] = GraphMetrics(
                graph_id=graph_id,
                start_time=time.time()
            )
    
    def _on_frame_complete(self, event_data: Dict[str, Any]):
        """处理帧完成事件"""
        graph_id = event_data.get('graph_id', 'default')
        success = event_data.get('success', True)
        
        if graph_id in self.graph_metrics:
            self.graph_metrics[graph_id].add_frame(success)
    
    async def start(self):
        """启动指标收集"""
        if self.running:
            return
        
        self.running = True
        self.publish_task = asyncio.create_task(self._publish_loop())
    
    async def stop(self):
        """停止指标收集"""
        self.running = False
        if self.publish_task:
            self.publish_task.cancel()
            try:
                await self.publish_task
            except asyncio.CancelledError:
                pass
    
    async def _publish_loop(self):
        """定期发布指标"""
        while self.running:
            try:
                await asyncio.sleep(self.publish_interval)
                await self._publish_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"指标发布异常: {e}")
    
    async def _publish_metrics(self):
        """发布性能指标"""
        current_time = time.time()
        
        # 发布节点性能事件
        for node_id, metrics in self.node_metrics.items():
            self.event_bus.publish('node.performance', {
                'node_id': node_id,
                'execution_count': metrics.execution_count,
                'error_count': metrics.error_count,
                'error_rate': metrics.get_error_rate(),
                'average_time': metrics.get_average_time(),
                'recent_average': metrics.get_recent_average(),
                'min_time': metrics.min_execution_time if metrics.min_execution_time != float('inf') else 0.0,
                'max_time': metrics.max_execution_time,
                'timestamp': current_time
            })
        
        # 发布图整体指标
        for graph_id, metrics in self.graph_metrics.items():
            self.event_bus.publish('graph.throughput', {
                'graph_id': graph_id,
                'total_frames': metrics.total_frames,
                'successful_frames': metrics.successful_frames,
                'error_frames': metrics.error_frames,
                'success_rate': metrics.get_success_rate(),
                'current_fps': metrics.get_current_fps(),
                'uptime': current_time - metrics.start_time,
                'timestamp': current_time
            })
        
        # 发布聚合指标
        self.event_bus.publish('graph.metrics', {
            'total_nodes': len(self.node_metrics),
            'total_graphs': len(self.graph_metrics),
            'overall_fps': self._calculate_overall_fps(),
            'overall_error_rate': self._calculate_overall_error_rate(),
            'timestamp': current_time
        })
    
    def _calculate_overall_fps(self) -> float:
        """计算整体FPS"""
        if not self.graph_metrics:
            return 0.0
        
        total_fps = sum(metrics.get_current_fps() for metrics in self.graph_metrics.values())
        return total_fps / len(self.graph_metrics)
    
    def _calculate_overall_error_rate(self) -> float:
        """计算整体错误率"""
        if not self.node_metrics:
            return 0.0
        
        total_executions = sum(metrics.execution_count for metrics in self.node_metrics.values())
        total_errors = sum(metrics.error_count for metrics in self.node_metrics.values())
        
        if total_executions == 0:
            return 0.0
        
        return total_errors / total_executions
    
    def get_node_metrics(self, node_id: str) -> Optional[NodeMetrics]:
        """获取节点指标"""
        return self.node_metrics.get(node_id)
    
    def get_graph_metrics(self, graph_id: str) -> Optional[GraphMetrics]:
        """获取图指标"""
        return self.graph_metrics.get(graph_id)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            'nodes': {
                node_id: {
                    'execution_count': metrics.execution_count,
                    'error_count': metrics.error_count,
                    'error_rate': metrics.get_error_rate(),
                    'average_time': metrics.get_average_time(),
                    'recent_average': metrics.get_recent_average()
                }
                for node_id, metrics in self.node_metrics.items()
            },
            'graphs': {
                graph_id: {
                    'total_frames': metrics.total_frames,
                    'success_rate': metrics.get_success_rate(),
                    'current_fps': metrics.get_current_fps(),
                    'uptime': time.time() - metrics.start_time
                }
                for graph_id, metrics in self.graph_metrics.items()
            },
            'overall': {
                'fps': self._calculate_overall_fps(),
                'error_rate': self._calculate_overall_error_rate(),
                'total_nodes': len(self.node_metrics),
                'total_graphs': len(self.graph_metrics)
            }
        }


# 全局实例
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    return _metrics_collector
