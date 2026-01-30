# -*- coding: utf-8 -*-
"""
节点基类和接口定义 (Node Base Class and Interface)
定义 DAG 节点的标准接口和数据结构

响应需求：需求 2（插件系统）
响应任务：任务 2.1 - 创建 INode 接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time


# ==================== 节点状态枚举 ====================

class NodeState(Enum):
    """
    节点状态枚举
    定义节点在生命周期中的各种状态
    """
    IDLE = "idle"                    # 空闲状态（初始化完成，未开始执行）
    RUNNING = "running"              # 运行中
    COMPLETED = "completed"          # 已完成
    ERROR = "error"                  # 错误状态
    STOPPED = "stopped"              # 已停止
    RESTARTING = "restarting"        # 重启中（用于 Restart 策略）


# ==================== 数据类定义 ====================

@dataclass
class NodeMetadata:
    """
    节点元数据
    描述节点的基本信息
    """
    name: str                        # 节点名称
    version: str                     # 版本号
    author: str                      # 作者
    description: str                 # 描述
    category: str                    # 类别（basic/algo/io/ui）
    tags: List[str] = field(default_factory=list)  # 标签


@dataclass
class ExecutionContext:
    """
    执行上下文
    传递给节点 run() 方法的上下文信息
    """
    node_id: str                     # 节点唯一标识
    inputs: Dict[str, Any]           # 输入数据（port_name -> data）
    global_context: Any              # 全局 Context 引用
    event_bus: Any                   # EventBus 引用
    execution_id: Optional[str] = None  # 执行ID（用于追踪）
    timestamp: float = field(default_factory=time.time)  # 时间戳


@dataclass
class NodeResult:
    """
    节点执行结果
    节点 run() 方法的返回值
    """
    success: bool                    # 是否成功
    outputs: Dict[str, Any]          # 输出数据（port_name -> data）
    error: Optional[str] = None      # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    execution_time: Optional[float] = None  # 执行时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'outputs': self.outputs,
            'error': self.error,
            'metadata': self.metadata,
            'execution_time': self.execution_time
        }


# ==================== 节点接口 ====================

class INode(ABC):
    """
    节点接口（所有插件必须实现）
    
    这是 DAG 系统中所有节点的基类
    定义了节点的标准接口和生命周期方法
    
    生命周期：
    1. __init__() - 创建节点实例
    2. initialize() - 初始化资源
    3. run() - 执行节点逻辑（可多次调用）
    4. cleanup() - 清理资源
    
    重启策略：
    当节点出错时，可以调用 cleanup() + initialize() 重启节点
    """
    
    # 插件元数据（类属性，子类必须覆盖）
    __plugin_metadata__ = {
        'type': 'base',
        'name': 'Base Node',
        'version': '1.0.0',
        'author': 'Unknown',
        'description': 'Base node interface',
        'category': 'basic',
        'dependencies': []  # 依赖的 Python 包列表
    }
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        初始化节点
        
        Args:
            node_id: 节点唯一标识
            config: 节点配置
        """
        self.node_id = node_id
        self.config = config
        self.enabled = True
        
        # 状态管理
        self._state = NodeState.IDLE
        self._state_lock = asyncio.Lock()
        
        # 统计信息
        self.execution_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        
        # 事件总线引用（在初始化时注入）
        self._event_bus = None
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    def get_metadata(self) -> NodeMetadata:
        """
        获取节点元数据
        
        Returns:
            NodeMetadata: 节点元数据
        """
        pass
    
    @abstractmethod
    def get_ports(self) -> Tuple[List['Port'], List['Port']]:
        """
        获取端口定义
        
        Returns:
            Tuple[List[Port], List[Port]]: (input_ports, output_ports)
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    async def run(self, context: ExecutionContext) -> NodeResult:
        """
        执行节点（核心逻辑）
        
        这是节点的主要执行方法，在流式执行模型中：
        - 从 context.inputs 读取输入数据
        - 执行处理逻辑
        - 返回 NodeResult 包含输出数据
        
        Args:
            context: 执行上下文
            
        Returns:
            NodeResult: 执行结果
        """
        pass
    
    # ==================== 生命周期方法 ====================
    
    async def initialize(self):
        """
        初始化节点资源
        
        在节点开始执行前调用，用于：
        - 加载模型
        - 建立连接
        - 分配资源
        
        用于 Restart 策略：cleanup() + initialize() 可重启节点
        """
        await self._set_state(NodeState.IDLE)
        self._publish_event('node.initialized', {
            'node_id': self.node_id,
            'metadata': self.get_metadata().__dict__
        })
    
    async def cleanup(self):
        """
        清理节点资源
        
        在节点停止时调用，用于：
        - 释放模型
        - 关闭连接
        - 释放资源
        """
        await self._set_state(NodeState.STOPPED)
        self._publish_event('node.cleaned_up', {
            'node_id': self.node_id
        })
    
    # ==================== 状态管理 ====================
    
    @property
    def state(self) -> NodeState:
        """获取当前状态"""
        return self._state
    
    async def _set_state(self, new_state: NodeState):
        """
        设置节点状态（内部方法）
        
        Args:
            new_state: 新状态
        """
        async with self._state_lock:
            old_state = self._state
            self._state = new_state
            
            # 发布状态变更事件
            self._publish_event('node.state_changed', {
                'node_id': self.node_id,
                'old_state': old_state.value,
                'new_state': new_state.value
            })
    
    # ==================== 数据处理钩子 ====================
    
    def input_data_processed_hook(self, input_port: str, data: Any):
        """
        输入数据处理完成钩子
        
        通知上游节点数据已处理完成，用于引用计数管理
        在写时复制（COW）机制中，当节点处理完数据后调用此方法
        
        Args:
            input_port: 输入端口名称
            data: 已处理的数据
        """
        self._publish_event('node.data_processed', {
            'node_id': self.node_id,
            'input_port': input_port,
            'data_id': id(data)
        })
    
    # ==================== 事件发布 ====================
    
    def set_event_bus(self, event_bus: Any):
        """
        设置事件总线引用
        
        Args:
            event_bus: EventBus 实例
        """
        self._event_bus = event_bus
    
    def _publish_event(self, topic: str, data: Dict[str, Any]):
        """
        发布事件（内部方法）
        
        Args:
            topic: 事件主题
            data: 事件数据
        """
        if self._event_bus is not None:
            self._event_bus.publish(topic, data, source=self.node_id)
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取节点统计信息
        
        Returns:
            Dict: 统计信息
        """
        avg_execution_time = (
            self.total_execution_time / self.execution_count
            if self.execution_count > 0 else 0.0
        )
        
        return {
            'node_id': self.node_id,
            'state': self._state.value,
            'execution_count': self.execution_count,
            'error_count': self.error_count,
            'total_execution_time': self.total_execution_time,
            'avg_execution_time': avg_execution_time,
            'error_rate': (
                self.error_count / self.execution_count
                if self.execution_count > 0 else 0.0
            )
        }
    
    # ==================== 辅助方法 ====================
    
    def __str__(self):
        metadata = self.get_metadata()
        return f"{metadata.name}({self.node_id})"
    
    def __repr__(self):
        return self.__str__()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("节点接口测试")
    print("=" * 60)
    
    # 创建一个简单的测试节点
    class TestNode(INode):
        """测试节点"""
        
        __plugin_metadata__ = {
            'type': 'test_node',
            'name': 'Test Node',
            'version': '1.0.0',
            'author': 'Test',
            'description': 'A simple test node',
            'category': 'basic'
        }
        
        def get_metadata(self) -> NodeMetadata:
            return NodeMetadata(
                name="Test Node",
                version="1.0.0",
                author="Test",
                description="A simple test node",
                category="basic"
            )
        
        def get_ports(self):
            # 简化：返回空列表
            return ([], [])
        
        def validate_config(self, config: Dict[str, Any]) -> bool:
            return True
        
        async def run(self, context: ExecutionContext) -> NodeResult:
            # 模拟处理
            await asyncio.sleep(0.1)
            
            return NodeResult(
                success=True,
                outputs={'result': 'test_output'},
                execution_time=0.1
            )
    
    # 测试节点
    async def test_node():
        print("\n1. 创建测试节点")
        print("-" * 60)
        node = TestNode(node_id="test_001", config={})
        print(f"节点: {node}")
        print(f"初始状态: {node.state}")
        
        print("\n2. 初始化节点")
        print("-" * 60)
        await node.initialize()
        print(f"初始化后状态: {node.state}")
        
        print("\n3. 执行节点")
        print("-" * 60)
        context = ExecutionContext(
            node_id="test_001",
            inputs={'input': 'test_data'},
            global_context=None,
            event_bus=None
        )
        result = await node.run(context)
        print(f"执行结果: success={result.success}, outputs={result.outputs}")
        
        print("\n4. 获取统计信息")
        print("-" * 60)
        node.execution_count = 10
        node.error_count = 2
        node.total_execution_time = 1.5
        stats = node.get_statistics()
        print(f"统计信息: {stats}")
        
        print("\n5. 清理节点")
        print("-" * 60)
        await node.cleanup()
        print(f"清理后状态: {node.state}")
    
    # 运行测试
    asyncio.run(test_node())
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
