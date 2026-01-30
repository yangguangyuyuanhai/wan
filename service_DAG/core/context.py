# -*- coding: utf-8 -*-
"""
上下文管理器
管理全局共享资源和执行上下文
"""

import threading
from typing import Any, Dict, Optional
from contextlib import contextmanager
from .event_bus import EventBus, global_event_bus
from .exceptions import ResourceException, ResourceNotFoundError


class GlobalContext:
    """
    全局上下文
    存放全局共享资源（配置、连接池、线程池等）
    """
    
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._event_bus: EventBus = global_event_bus
    
    def set_resource(self, name: str, resource: Any):
        """
        设置资源
        
        Args:
            name: 资源名称
            resource: 资源对象
        """
        with self._lock:
            self._resources[name] = resource
    
    def get_resource(self, name: str, default: Any = None) -> Any:
        """
        获取资源
        
        Args:
            name: 资源名称
            default: 默认值
            
        Returns:
            资源对象
        """
        with self._lock:
            return self._resources.get(name, default)
    
    def has_resource(self, name: str) -> bool:
        """
        检查资源是否存在
        
        Args:
            name: 资源名称
            
        Returns:
            是否存在
        """
        with self._lock:
            return name in self._resources
    
    def remove_resource(self, name: str):
        """
        移除资源
        
        Args:
            name: 资源名称
        """
        with self._lock:
            if name in self._resources:
                del self._resources[name]
    
    def clear_resources(self):
        """清空所有资源"""
        with self._lock:
            self._resources.clear()
    
    def get_event_bus(self) -> EventBus:
        """获取事件总线"""
        return self._event_bus
    
    def set_event_bus(self, event_bus: EventBus):
        """设置事件总线"""
        self._event_bus = event_bus
    
    def list_resources(self) -> list:
        """列出所有资源名称"""
        with self._lock:
            return list(self._resources.keys())


class ExecutionContext:
    """
    执行上下文
    每次 DAG 执行时创建，包含执行相关的临时数据
    支持上下文管理器协议，确保资源自动清理
    """
    
    def __init__(self, global_context: GlobalContext, execution_id: str = ""):
        """
        初始化执行上下文
        
        Args:
            global_context: 全局上下文
            execution_id: 执行ID
        """
        self.global_context = global_context
        self.execution_id = execution_id
        
        # 执行数据（节点间传递的数据）
        self._data: Dict[str, Any] = {}
        
        # 临时资源（执行结束后需要清理）
        self._temp_resources: Dict[str, Any] = {}
        
        # 调试信息
        self._debug_mode = False
        self._breakpoints: set = set()
        self._intermediate_results: Dict[str, Any] = {}
        
        # 锁
        self._lock = threading.RLock()
    
    # ==================== 数据管理 ====================
    
    def set_data(self, key: str, value: Any):
        """
        设置数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        with self._lock:
            self._data[key] = value
            
            # 调试模式：保存中间结果
            if self._debug_mode:
                self._intermediate_results[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        获取数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            数据值
        """
        with self._lock:
            return self._data.get(key, default)
    
    def has_data(self, key: str) -> bool:
        """
        检查数据是否存在
        
        Args:
            key: 数据键
            
        Returns:
            是否存在
        """
        with self._lock:
            return key in self._data
    
    def remove_data(self, key: str):
        """
        移除数据
        
        Args:
            key: 数据键
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
    
    # ==================== 临时资源管理 ====================
    
    def register_temp_resource(self, name: str, resource: Any, cleanup_func: Optional[callable] = None):
        """
        注册临时资源
        
        Args:
            name: 资源名称
            resource: 资源对象
            cleanup_func: 清理函数（可选）
        """
        with self._lock:
            self._temp_resources[name] = {
                'resource': resource,
                'cleanup': cleanup_func
            }
    
    def get_temp_resource(self, name: str) -> Any:
        """
        获取临时资源
        
        Args:
            name: 资源名称
            
        Returns:
            资源对象
            
        Raises:
            ResourceNotFoundError: 资源不存在
        """
        with self._lock:
            if name not in self._temp_resources:
                raise ResourceNotFoundError(f"临时资源不存在: {name}")
            return self._temp_resources[name]['resource']
    
    def cleanup_temp_resources(self):
        """清理所有临时资源"""
        with self._lock:
            for name, info in self._temp_resources.items():
                try:
                    if info['cleanup']:
                        info['cleanup'](info['resource'])
                except Exception as e:
                    print(f"清理资源 {name} 失败: {e}")
            
            self._temp_resources.clear()
    
    # ==================== 调试支持 ====================
    
    def enable_debug_mode(self):
        """启用调试模式"""
        self._debug_mode = True
    
    def disable_debug_mode(self):
        """禁用调试模式"""
        self._debug_mode = False
    
    def is_debug_mode(self) -> bool:
        """是否为调试模式"""
        return self._debug_mode
    
    def add_breakpoint(self, node_id: str):
        """
        添加断点
        
        Args:
            node_id: 节点ID
        """
        self._breakpoints.add(node_id)
    
    def remove_breakpoint(self, node_id: str):
        """
        移除断点
        
        Args:
            node_id: 节点ID
        """
        self._breakpoints.discard(node_id)
    
    def has_breakpoint(self, node_id: str) -> bool:
        """
        检查是否有断点
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否有断点
        """
        return node_id in self._breakpoints
    
    def get_intermediate_result(self, node_id: str) -> Any:
        """
        获取中间结果（调试用）
        
        Args:
            node_id: 节点ID
            
        Returns:
            中间结果
        """
        return self._intermediate_results.get(node_id)
    
    def list_intermediate_results(self) -> Dict[str, Any]:
        """列出所有中间结果"""
        return self._intermediate_results.copy()
    
    # ==================== 上下文管理器协议 ====================
    
    def __enter__(self):
        """进入上下文"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，自动清理资源"""
        self.cleanup_temp_resources()
        return False  # 不抑制异常
    
    # ==================== 便捷方法 ====================
    
    def get_event_bus(self) -> EventBus:
        """获取事件总线"""
        return self.global_context.get_event_bus()
    
    def get_global_resource(self, name: str, default: Any = None) -> Any:
        """
        获取全局资源
        
        Args:
            name: 资源名称
            default: 默认值
            
        Returns:
            资源对象
        """
        return self.global_context.get_resource(name, default)


# ==================== 全局上下文实例 ====================

global_context = GlobalContext()


@contextmanager
def create_execution_context(execution_id: str = ""):
    """
    创建执行上下文（上下文管理器）
    
    Args:
        execution_id: 执行ID
        
    Yields:
        ExecutionContext: 执行上下文
        
    Example:
        with create_execution_context("exec_001") as ctx:
            ctx.set_data("image", img)
            # ... 执行操作 ...
        # 自动清理资源
    """
    ctx = ExecutionContext(global_context, execution_id)
    try:
        yield ctx
    finally:
        ctx.cleanup_temp_resources()


if __name__ == "__main__":
    # 测试上下文管理器
    print("上下文管理器测试\n")
    
    # 测试全局上下文
    print("1. 全局上下文测试")
    global_ctx = GlobalContext()
    global_ctx.set_resource("config", {"key": "value"})
    global_ctx.set_resource("thread_pool", "ThreadPool实例")
    
    print(f"资源列表: {global_ctx.list_resources()}")
    print(f"获取配置: {global_ctx.get_resource('config')}")
    
    # 测试执行上下文
    print("\n2. 执行上下文测试")
    with create_execution_context("test_001") as exec_ctx:
        # 设置数据
        exec_ctx.set_data("image", "图像数据")
        exec_ctx.set_data("result", "处理结果")
        
        print(f"获取数据: {exec_ctx.get_data('image')}")
        
        # 注册临时资源
        def cleanup_file(f):
            print(f"清理文件: {f}")
        
        exec_ctx.register_temp_resource("temp_file", "temp.txt", cleanup_file)
        
        # 调试模式
        exec_ctx.enable_debug_mode()
        exec_ctx.add_breakpoint("node_1")
        print(f"调试模式: {exec_ctx.is_debug_mode()}")
        print(f"有断点: {exec_ctx.has_breakpoint('node_1')}")
    
    print("\n3. 资源自动清理完成")
    
    print("\n测试完成")
