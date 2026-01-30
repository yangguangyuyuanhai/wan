"""
单元测试 - 流式执行器
测试流式执行引擎的核心功能
"""
import pytest
import asyncio
from service_DAG.engine.streaming_executor import StreamingExecutor
from service_DAG.engine.graph import Graph
from service_DAG.engine.node import INode, NodeResult, ExecutionContext
from service_DAG.core.event_bus import EventBus


class ProducerNode(INode):
    """生产者节点"""
    __plugin_metadata__ = {"type": "producer"}
    
    def __init__(self, node_id, config):
        super().__init__(node_id, config)
        self.count = 0
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        self.count += 1
        await asyncio.sleep(0.01)
        return NodeResult(success=True, outputs={"data": self.count})


class ConsumerNode(INode):
    """消费者节点"""
    __plugin_metadata__ = {"type": "consumer"}
    
    def __init__(self, node_id, config):
        super().__init__(node_id, config)
        self.received = []
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        data = context.inputs.get("data")
        self.received.append(data)
        return NodeResult(success=True, outputs={})


class TestStreamingExecutor:
    """流式执行器测试"""
    
    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """测试基本执行流程"""
        graph = Graph()
        producer = ProducerNode("producer", {})
        consumer = ConsumerNode("consumer", {})
        
        graph.add_node(producer)
        graph.add_node(consumer)
        graph.add_connection("producer", "data", "consumer", "data")
        
        event_bus = EventBus()
        executor = StreamingExecutor(graph, event_bus)
        
        # 启动执行器
        await executor.start()
        
        # 运行一段时间
        await asyncio.sleep(0.5)
        
        # 停止执行器
        await executor.stop()
        
        # 验证消费者收到数据
        assert len(consumer.received) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        class ErrorNode(INode):
            __plugin_metadata__ = {"type": "error"}
            
            async def run(self, context: ExecutionContext) -> NodeResult:
                return NodeResult(success=False, error="Test error")
        
        graph = Graph()
        error_node = ErrorNode("error", {})
        graph.add_node(error_node)
        
        event_bus = EventBus()
        executor = StreamingExecutor(graph, event_bus, error_strategy="skip")
        
        await executor.start()
        await asyncio.sleep(0.1)
        await executor.stop()
        
        # 应该能正常停止，不会崩溃
        assert True
    
    @pytest.mark.asyncio
    async def test_parallel_branches(self):
        """测试并行分支"""
        graph = Graph()
        producer = ProducerNode("producer", {})
        consumer1 = ConsumerNode("consumer1", {})
        consumer2 = ConsumerNode("consumer2", {})
        
        graph.add_node(producer)
        graph.add_node(consumer1)
        graph.add_node(consumer2)
        graph.add_connection("producer", "data", "consumer1", "data")
        graph.add_connection("producer", "data", "consumer2", "data")
        
        event_bus = EventBus()
        executor = StreamingExecutor(graph, event_bus)
        
        await executor.start()
        await asyncio.sleep(0.5)
        await executor.stop()
        
        # 两个消费者都应该收到数据
        assert len(consumer1.received) > 0
        assert len(consumer2.received) > 0
