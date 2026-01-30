# -*- coding: utf-8 -*-
"""
日志订阅者
订阅事件总线事件并写入日志

响应任务：任务 16.3 - 实现日志订阅者
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from core.event_bus import get_event_bus


class LoggerSubscriber:
    """
    日志订阅者
    
    功能：
    1. 订阅所有日志相关事件
    2. 格式化日志消息
    3. 写入日志文件
    4. 支持日志级别过滤
    """
    
    def __init__(self, log_dir: str = "./logs", log_level: str = "INFO"):
        """
        初始化日志订阅者
        
        Args:
            log_dir: 日志目录
            log_level: 日志级别
        """
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.event_bus = get_event_bus()
        
        # 创建日志目录
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志记录器
        self._setup_loggers()
        
        # 订阅事件
        self._subscribe_events()
        
        # 运行状态
        self.running = False
    
    def _setup_loggers(self):
        """设置日志记录器"""
        # 系统日志
        self.system_logger = logging.getLogger('dag_system')
        self.system_logger.setLevel(self.log_level)
        
        # 性能日志
        self.performance_logger = logging.getLogger('dag_performance')
        self.performance_logger.setLevel(logging.INFO)
        
        # 错误日志
        self.error_logger = logging.getLogger('dag_error')
        self.error_logger.setLevel(logging.ERROR)
        
        # 创建文件处理器
        self._create_file_handlers()
    
    def _create_file_handlers(self):
        """创建文件处理器"""
        # 系统日志文件
        system_handler = logging.FileHandler(
            self.log_dir / 'system.log',
            encoding='utf-8'
        )
        system_handler.setLevel(self.log_level)
        system_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        system_handler.setFormatter(system_formatter)
        self.system_logger.addHandler(system_handler)
        
        # 性能日志文件
        perf_handler = logging.FileHandler(
            self.log_dir / 'performance.log',
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        )
        perf_handler.setFormatter(perf_formatter)
        self.performance_logger.addHandler(perf_handler)
        
        # 错误日志文件
        error_handler = logging.FileHandler(
            self.log_dir / 'error.log',
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - ERROR - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
    
    def _subscribe_events(self):
        """订阅相关事件"""
        # 系统事件
        self.event_bus.subscribe('graph.start', self._on_graph_start)
        self.event_bus.subscribe('graph.stop', self._on_graph_stop)
        self.event_bus.subscribe('node.start', self._on_node_start)
        self.event_bus.subscribe('node.complete', self._on_node_complete)
        
        # 错误事件
        self.event_bus.subscribe('node.error', self._on_node_error)
        self.event_bus.subscribe('node.exception', self._on_node_exception)
        self.event_bus.subscribe('graph.error', self._on_graph_error)
        
        # 性能事件
        self.event_bus.subscribe('node.performance', self._on_node_performance)
        self.event_bus.subscribe('graph.throughput', self._on_graph_throughput)
        self.event_bus.subscribe('graph.metrics', self._on_graph_metrics)
        
        # 数据事件
        self.event_bus.subscribe('data.branch', self._on_data_branch)
        self.event_bus.subscribe('queue.full', self._on_queue_full)
        
        # 插件事件
        self.event_bus.subscribe('plugin.loaded', self._on_plugin_loaded)
        self.event_bus.subscribe('plugin.error', self._on_plugin_error)
    
    def _on_graph_start(self, event_data: Dict[str, Any]):
        """处理图开始事件"""
        graph_name = event_data.get('graph_name', 'unknown')
        node_count = event_data.get('node_count', 0)
        
        self.system_logger.info(
            f"图执行开始: {graph_name}, 节点数量: {node_count}"
        )
    
    def _on_graph_stop(self, event_data: Dict[str, Any]):
        """处理图停止事件"""
        graph_name = event_data.get('graph_name', 'unknown')
        
        self.system_logger.info(f"图执行停止: {graph_name}")
    
    def _on_node_start(self, event_data: Dict[str, Any]):
        """处理节点开始事件"""
        node_id = event_data.get('node_id', 'unknown')
        packet_id = event_data.get('packet_id', 'unknown')
        
        if self.system_logger.isEnabledFor(logging.DEBUG):
            self.system_logger.debug(
                f"节点开始执行: {node_id}, 数据包: {packet_id}"
            )
    
    def _on_node_complete(self, event_data: Dict[str, Any]):
        """处理节点完成事件"""
        node_id = event_data.get('node_id', 'unknown')
        execution_time = event_data.get('execution_time', 0.0)
        
        if self.system_logger.isEnabledFor(logging.DEBUG):
            self.system_logger.debug(
                f"节点执行完成: {node_id}, 耗时: {execution_time:.3f}s"
            )
    
    def _on_node_error(self, event_data: Dict[str, Any]):
        """处理节点错误事件"""
        node_id = event_data.get('node_id', 'unknown')
        error = event_data.get('error', 'unknown error')
        packet_id = event_data.get('packet_id', 'unknown')
        
        self.error_logger.error(
            f"节点执行错误: {node_id}, 错误: {error}, 数据包: {packet_id}"
        )
    
    def _on_node_exception(self, event_data: Dict[str, Any]):
        """处理节点异常事件"""
        node_id = event_data.get('node_id', 'unknown')
        error = event_data.get('error', 'unknown exception')
        
        self.error_logger.error(
            f"节点异常: {node_id}, 异常: {error}"
        )
    
    def _on_graph_error(self, event_data: Dict[str, Any]):
        """处理图错误事件"""
        graph_id = event_data.get('graph_id', 'unknown')
        error = event_data.get('error', 'unknown error')
        
        self.error_logger.error(
            f"图执行错误: {graph_id}, 错误: {error}"
        )
    
    def _on_node_performance(self, event_data: Dict[str, Any]):
        """处理节点性能事件"""
        node_id = event_data.get('node_id', 'unknown')
        execution_count = event_data.get('execution_count', 0)
        error_rate = event_data.get('error_rate', 0.0)
        average_time = event_data.get('average_time', 0.0)
        
        self.performance_logger.info(
            f"节点性能: {node_id} | "
            f"执行次数: {execution_count} | "
            f"错误率: {error_rate:.2%} | "
            f"平均耗时: {average_time:.3f}s"
        )
    
    def _on_graph_throughput(self, event_data: Dict[str, Any]):
        """处理图吞吐量事件"""
        graph_id = event_data.get('graph_id', 'unknown')
        current_fps = event_data.get('current_fps', 0.0)
        success_rate = event_data.get('success_rate', 0.0)
        total_frames = event_data.get('total_frames', 0)
        
        self.performance_logger.info(
            f"图吞吐量: {graph_id} | "
            f"FPS: {current_fps:.1f} | "
            f"成功率: {success_rate:.2%} | "
            f"总帧数: {total_frames}"
        )
    
    def _on_graph_metrics(self, event_data: Dict[str, Any]):
        """处理图整体指标事件"""
        overall_fps = event_data.get('overall_fps', 0.0)
        overall_error_rate = event_data.get('overall_error_rate', 0.0)
        total_nodes = event_data.get('total_nodes', 0)
        
        self.performance_logger.info(
            f"系统整体指标 | "
            f"FPS: {overall_fps:.1f} | "
            f"错误率: {overall_error_rate:.2%} | "
            f"节点数: {total_nodes}"
        )
    
    def _on_data_branch(self, event_data: Dict[str, Any]):
        """处理数据分支事件"""
        node_id = event_data.get('node_id', 'unknown')
        branch_count = event_data.get('branch_count', 0)
        data_size = event_data.get('data_size', 0)
        
        if self.system_logger.isEnabledFor(logging.DEBUG):
            self.system_logger.debug(
                f"数据分支: {node_id}, 分支数: {branch_count}, 数据大小: {data_size}字节"
            )
    
    def _on_queue_full(self, event_data: Dict[str, Any]):
        """处理队列满事件"""
        node_id = event_data.get('node_id', 'unknown')
        size = event_data.get('size', 0)
        
        self.system_logger.warning(
            f"队列已满: {node_id}, 大小: {size}"
        )
    
    def _on_plugin_loaded(self, event_data: Dict[str, Any]):
        """处理插件加载事件"""
        plugin_type = event_data.get('plugin_type', 'unknown')
        plugin_name = event_data.get('plugin_name', 'unknown')
        
        self.system_logger.info(
            f"插件加载成功: {plugin_type} - {plugin_name}"
        )
    
    def _on_plugin_error(self, event_data: Dict[str, Any]):
        """处理插件错误事件"""
        plugin_type = event_data.get('plugin_type', 'unknown')
        error = event_data.get('error', 'unknown error')
        
        self.error_logger.error(
            f"插件加载失败: {plugin_type}, 错误: {error}"
        )
    
    def start(self):
        """启动日志订阅者"""
        if self.running:
            return
        
        self.running = True
        self.system_logger.info("日志订阅者已启动")
    
    def stop(self):
        """停止日志订阅者"""
        if not self.running:
            return
        
        self.running = False
        self.system_logger.info("日志订阅者已停止")
        
        # 关闭所有处理器
        for logger in [self.system_logger, self.performance_logger, self.error_logger]:
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


# 全局实例
_logger_subscriber = LoggerSubscriber()


def get_logger_subscriber() -> LoggerSubscriber:
    """获取日志订阅者实例"""
    return _logger_subscriber
