# -*- coding: utf-8 -*-
"""
流式执行器 (Streaming Executor)
基于 asyncio.Queue 实现的流水线并发执行引擎

响应需求：需求 3（DAG引擎）、需求 5（数据传输性能）
响应任务：任务 4 - 实现流水线执行器
响应建议：change_plus.md - 直接实现流式模型，废弃批处理
"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import time
import copy

from .graph import Graph, Connection
from .node import INode, ExecutionContext, NodeResult, NodeState
from core.event_bus import get_event_bus
from core.exceptions import NodeExecutionError


# ==================== 执行状态 ====================

@dataclass
class ExecutionState:
    """
    执行状态
    跟踪图执行过程中的状态信息
    """
    node_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # node_id -> {port -> data}
    node_status: Dict[str, str] = field(default_factory=dict)  # node_id -> status
    start_time: float = 0
    end_time: float = 0
    total_frames_processed: int = 0
    
    def get_duration(self) -> float:
        """获取执行时长"""
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time


@dataclass
class DataPacket:
    """
    数据包
    在节点间传递的数据容器，支持引用计数
    """
    data: Dict[str, Any]             # 端口数据（port_name -> value）
    packet_id: str                   # 数据包ID
    timestamp: float = field(default_factory=time.time)  # 时间戳
    ref_count: int = 1               # 引用计数（用于 COW）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def increment_ref(self):
        """增加引用计数"""
        self.ref_count += 1
    
    def decrement_ref(self):
        """减少引用计数"""
        self.ref_count -= 1
        return self.ref_count
    
    def copy_data(self) -> 'DataPacket':
        """复制数据包（深拷贝）"""
        return DataPacket(
            data=copy.deepcopy(self.data),
            packet_id=f"{self.packet_id}_copy",
            timestamp=self.timestamp,
            ref_count=1,
            metadata=self.metadata.copy()
        )


# ==================== 流式执行器 ====================

class StreamingExecutor:
    """
    流式执行器
    
    基于 asyncio.Queue 实现的流水线并发执行引擎
    每个节点有独立的输入队列，长期运行的任务循环
    
    核心特性：
    1. 流水线并发：所有节点并行运行
    2. 背压机制：队列满时自动阻塞上游
    3. 引用计数：支持写时复制（COW）
    4. 错误处理：支持多种错误策略
    """
    
    def __init__(self, graph: Graph, global_context: Any, queue_size: int = 10):
        """
        初始化流式执行器
        
        Args:
            graph: DAG 图
            global_context: 全局上下文
            queue_size: 队列最大长度（实现背压）
        """
        self.graph = graph
        self.global_context = global_context
        self.queue_size = queue_size
        self.event_bus = get_event_bus()
        
        # 配置
        self.error_strategy = global_context.get_config('error_strategy', 'circuit-break')
        self.max_retries = global_context.get_config('max_retries', 3)
        
        # 队列网络
        self.node_queues: Dict[str, asyncio.Queue] = {}  # node_id -> input_queue
        
        # 任务管理
        self.node_tasks: Dict[str, asyncio.Task] = {}  # node_id -> task
        self.running = False
        self.stop_event = asyncio.Event()
        
        # 统计信息
        self.state = ExecutionState()
        self.queue_stats: Dict[str, Dict[str, int]] = {}  # node_id -> {put_count, get_count}
    
    # ==================== 初始化 ====================
    
    def _create_node_queues(self):
        """
        创建节点队列网络
        根据图结构为每个节点创建输入队列
        """
        for node_id in self.graph.list_nodes():
            self.node_queues[node_id] = asyncio.Queue(maxsize=self.queue_size)
            self.queue_stats[node_id] = {'put_count': 0, 'get_count': 0, 'current_size': 0}
            self.state.node_status[node_id] = 'pending'
    
    # ==================== 节点任务循环 ====================
    
    async def _node_task(self, node_id: str):
        """
        节点任务循环
        
        这是每个节点的主循环，长期运行：
        1. 从输入队列读取数据（或对于源节点，直接执行）
        2. 调用节点的 run() 方法
        3. 将输出推送到下游节点的队列
        4. 处理停止信号
        
        Args:
            node_id: 节点ID
        """
        node = self.graph.get_node(node_id)
        if node is None:
            return
        
        input_queue = self.node_queues[node_id]
        
        # 设置事件总线
        node.set_event_bus(self.event_bus)
        
        # 初始化节点
        try:
            await node.initialize()
        except Exception as e:
            self.event_bus.publish('node.init_error', {
                'node_id': node_id,
                'error': str(e)
            })
            return
        
        # 检查是否为源节点（无输入端口）
        input_ports, _ = node.get_ports()
        is_source_node = len(input_ports) == 0
        
        # 主循环
        packet_counter = 0
        while self.running:
            try:
                packet = None
                
                if is_source_node:
                    # 源节点：不需要从队列读取，直接执行
                    # 检查停止信号
                    if self.stop_event.is_set():
                        break
                    
                    # 创建空数据包（源节点不需要输入）
                    packet_counter += 1
                    packet = DataPacket(
                        data={},
                        packet_id=f"{node_id}_packet_{packet_counter}",
                        ref_count=1
                    )
                    
                    # 添加小延迟以避免CPU占用过高
                    await asyncio.sleep(0.001)
                else:
                    # 非源节点：从队列读取数据（带超时，以便检查停止信号）
                    try:
                        packet = await asyncio.wait_for(input_queue.get(), timeout=0.1)
                        self.queue_stats[node_id]['get_count'] += 1
                        self.queue_stats[node_id]['current_size'] = input_queue.qsize()
                    except asyncio.TimeoutError:
                        # 超时，检查是否需要停止
                        if self.stop_event.is_set():
                            break
                        continue
                    
                    # 检查停止信号
                    if packet is None:  # None 表示停止信号
                        break
                
                # 更新节点状态
                self.state.node_status[node_id] = 'running'
                
                # 发布节点开始事件
                self.event_bus.publish('node.start', {
                    'node_id': node_id,
                    'packet_id': packet.packet_id
                })
                
                # 创建执行上下文
                context = ExecutionContext(
                    node_id=node_id,
                    inputs=packet.data,
                    global_context=self.global_context,
                    event_bus=self.event_bus,
                    execution_id=packet.packet_id
                )
                
                # 执行节点（带重试）
                result = await self._execute_node_with_retry(node, context)
                
                if result.success:
                    # 保存输出
                    self.state.node_outputs[node_id] = result.outputs
                    self.state.node_status[node_id] = 'completed'
                    
                    # 推送输出到下游节点
                    await self._push_outputs_to_downstream(node_id, result.outputs, packet.packet_id)
                    
                    # 发布节点完成事件
                    self.event_bus.publish('node.complete', {
                        'node_id': node_id,
                        'packet_id': packet.packet_id,
                        'execution_time': result.execution_time
                    })
                    
                    # 更新统计
                    node.execution_count += 1
                    if result.execution_time:
                        node.total_execution_time += result.execution_time
                else:
                    # 处理错误
                    await self._handle_node_error(node_id, result.error, packet)
                
                # 减少引用计数
                if packet:
                    packet.decrement_ref()
                
            except Exception as e:
                # 未预期的异常
                self.event_bus.publish('node.exception', {
                    'node_id': node_id,
                    'error': str(e)
                })
                
                if self.error_strategy == 'circuit-break':
                    self.running = False
                    break
        
        # 清理节点
        try:
            await node.cleanup()
        except Exception as e:
            self.event_bus.publish('node.cleanup_error', {
                'node_id': node_id,
                'error': str(e)
            })
    
    async def _execute_node_with_retry(self, node: INode, context: ExecutionContext) -> NodeResult:
        """
        执行节点（带重试）
        
        Args:
            node: 节点实例
            context: 执行上下文
            
        Returns:
            NodeResult: 执行结果
        """
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                result = await node.run(context)
                result.execution_time = time.time() - start_time
                
                if result.success:
                    return result
                else:
                    if attempt < self.max_retries - 1 and self.error_strategy == 'retry':
                        await asyncio.sleep(0.1 * (attempt + 1))  # 指数退避
                        continue
                    return result
                    
            except Exception as e:
                if attempt < self.max_retries - 1 and self.error_strategy == 'retry':
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    return NodeResult(
                        success=False,
                        outputs={},
                        error=str(e)
                    )
        
        return NodeResult(success=False, outputs={}, error="Max retries exceeded")
    
    async def _handle_node_error(self, node_id: str, error: str, packet: DataPacket):
        """
        处理节点错误
        
        Args:
            node_id: 节点ID
            error: 错误信息
            packet: 数据包
        """
        node = self.graph.get_node(node_id)
        if node:
            node.error_count += 1
        
        self.state.node_status[node_id] = 'error'
        
        # 发布错误事件
        self.event_bus.publish('node.error', {
            'node_id': node_id,
            'error': error,
            'packet_id': packet.packet_id
        })
        
        # 根据错误策略处理
        if self.error_strategy == 'circuit-break':
            self.running = False
            self.stop_event.set()
        elif self.error_strategy == 'restart':
            # 重启节点
            await self._restart_node(node_id)
    
    async def _restart_node(self, node_id: str):
        """
        重启节点
        
        Args:
            node_id: 节点ID
        """
        node = self.graph.get_node(node_id)
        if node is None:
            return
        
        self.event_bus.publish('node.restarting', {'node_id': node_id})
        
        try:
            # 清理
            await node.cleanup()
            
            # 重新初始化
            await node.initialize()
            
            self.state.node_status[node_id] = 'running'
            
            self.event_bus.publish('node.restarted', {'node_id': node_id})
        except Exception as e:
            self.event_bus.publish('node.restart_failed', {
                'node_id': node_id,
                'error': str(e)
            })
    
    # ==================== 数据推送 ====================
    
    async def _push_outputs_to_downstream(self, node_id: str, outputs: Dict[str, Any], packet_id: str):
        """
        推送输出到下游节点
        
        实现写时复制（COW）：
        - 如果输出连接到单个下游节点，直接传递引用
        - 如果输出连接到多个下游节点，复制数据
        
        Args:
            node_id: 节点ID
            outputs: 输出数据
            packet_id: 数据包ID
        """
        # 获取从此节点出发的所有连接
        connections = self.graph.get_connections_from(node_id)
        
        # 按输出端口分组连接
        port_connections: Dict[str, List[Connection]] = {}
        for conn in connections:
            if conn.from_port not in port_connections:
                port_connections[conn.from_port] = []
            port_connections[conn.from_port].append(conn)
        
        # 推送每个输出端口的数据
        for port_name, port_conns in port_connections.items():
            if port_name not in outputs:
                continue
            
            data = outputs[port_name]
            
            # 检查是否需要分支（多个下游节点）
            if len(port_conns) > 1:
                # 分支：需要复制数据（COW）
                self.event_bus.publish('data.branch', {
                    'node_id': node_id,
                    'port': port_name,
                    'branch_count': len(port_conns)
                })
                
                for i, conn in enumerate(port_conns):
                    # 为每个分支创建数据副本
                    if i == 0:
                        # 第一个分支使用原始数据
                        branch_data = data
                    else:
                        # 其他分支复制数据
                        branch_data = copy.deepcopy(data)
                    
                    # 创建数据包
                    packet = DataPacket(
                        data={conn.to_port: branch_data},
                        packet_id=f"{packet_id}_branch_{i}",
                        ref_count=1
                    )
                    
                    # 推送到下游队列
                    await self._push_to_queue(conn.to_node, packet)
            else:
                # 单个下游节点：直接传递引用（零拷贝）
                conn = port_conns[0]
                packet = DataPacket(
                    data={conn.to_port: data},
                    packet_id=packet_id,
                    ref_count=1
                )
                
                await self._push_to_queue(conn.to_node, packet)
    
    async def _push_to_queue(self, node_id: str, packet: DataPacket):
        """
        推送数据包到节点队列
        
        Args:
            node_id: 节点ID
            packet: 数据包
        """
        if node_id not in self.node_queues:
            return
        
        queue = self.node_queues[node_id]
        
        # 推送到队列（如果队列满，会自动阻塞，实现背压）
        await queue.put(packet)
        
        self.queue_stats[node_id]['put_count'] += 1
        self.queue_stats[node_id]['current_size'] = queue.qsize()
        
        # 发布队列状态事件
        if queue.full():
            self.event_bus.publish('queue.full', {
                'node_id': node_id,
                'size': queue.qsize()
            })
    
    # ==================== 生命周期管理 ====================
    
    async def start(self):
        """
        启动执行器
        
        启动所有节点的任务循环
        """
        if self.running:
            return
        
        self.running = True
        self.stop_event.clear()
        self.state.start_time = time.time()
        
        # 创建队列网络
        self._create_node_queues()
        
        # 发布启动事件
        self.event_bus.publish('graph.start', {
            'graph_name': self.graph.definition.name,
            'node_count': len(self.graph.list_nodes())
        })
        
        # 为每个节点创建任务
        for node_id in self.graph.list_nodes():
            task = asyncio.create_task(self._node_task(node_id))
            self.node_tasks[node_id] = task
        
        print(f"[StreamingExecutor] 已启动 {len(self.node_tasks)} 个节点任务")
    
    async def stop(self):
        """
        停止执行器
        
        优雅地停止所有节点任务
        """
        if not self.running:
            return
        
        print("[StreamingExecutor] 正在停止...")
        
        self.running = False
        self.stop_event.set()
        
        # 向所有队列发送停止信号
        for node_id, queue in self.node_queues.items():
            await queue.put(None)  # None 作为停止信号
        
        # 等待所有任务完成
        if self.node_tasks:
            await asyncio.gather(*self.node_tasks.values(), return_exceptions=True)
        
        self.state.end_time = time.time()
        
        # 发布停止事件
        self.event_bus.publish('graph.stop', {
            'graph_name': self.graph.definition.name,
            'duration': self.state.get_duration(),
            'frames_processed': self.state.total_frames_processed
        })
        
        print(f"[StreamingExecutor] 已停止，运行时长: {self.state.get_duration():.2f}秒")
    
    async def feed_source_data(self, source_node_id: str, data: Dict[str, Any]):
        """
        向源节点喂入数据
        
        用于启动数据流
        
        Args:
            source_node_id: 源节点ID
            data: 输入数据
        """
        if source_node_id not in self.node_queues:
            return
        
        packet = DataPacket(
            data=data,
            packet_id=f"packet_{self.state.total_frames_processed}",
            ref_count=1
        )
        
        await self._push_to_queue(source_node_id, packet)
        self.state.total_frames_processed += 1
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取执行器统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'running': self.running,
            'duration': self.state.get_duration(),
            'frames_processed': self.state.total_frames_processed,
            'node_status': self.state.node_status,
            'queue_stats': self.queue_stats,
            'node_statistics': {
                node_id: node.get_statistics()
                for node_id, node in self.graph.nodes.items()
            }
        }


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("流式执行器测试")
    print("=" * 60)
    
    # 这里需要完整的测试环境，包括图定义和节点实现
    # 实际测试将在集成测试中进行
    
    print("\n流式执行器已实现")
    print("请参考集成测试进行完整测试")
    print("\n" + "=" * 60)
