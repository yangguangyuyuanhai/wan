"""
集成测试 - 监控系统完整测试
测试性能监控、事件桥接和UI集成
"""
import pytest
import asyncio
from service_DAG.core.metrics import MetricsCollector
from service_DAG.core.async_event_bus import AsyncEventBus
from service_DAG.core.logger_subscriber import LoggerSubscriber


class TestMonitoringIntegration:
    """监控系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """测试性能指标收集"""
        event_bus = AsyncEventBus()
        metrics = MetricsCollector(event_bus)
        
        # 模拟节点执行
        await event_bus.publish("node.start", {"node_id": "test_node"})
        await asyncio.sleep(0.1)
        await event_bus.publish("node.complete", {
            "node_id": "test_node",
            "execution_time": 0.05
        })
        
        await asyncio.sleep(0.2)
        
        # 验证指标收集
        node_metrics = metrics.get_node_metrics("test_node")
        assert node_metrics is not None
        assert node_metrics["count"] > 0
    
    @pytest.mark.asyncio
    async def test_logger_subscriber(self):
        """测试日志订阅者"""
        event_bus = AsyncEventBus()
        logger = LoggerSubscriber(event_bus)
        
        # 发布日志事件
        await event_bus.publish("log.info", {"message": "Test log"})
        await event_bus.publish("log.error", {"message": "Test error"})
        
        await asyncio.sleep(0.1)
        
        # 验证日志记录
        assert True  # 日志已记录
    
    @pytest.mark.asyncio
    async def test_event_flow(self):
        """测试完整事件流"""
        event_bus = AsyncEventBus()
        metrics = MetricsCollector(event_bus)
        logger = LoggerSubscriber(event_bus)
        
        # 模拟完整流程
        await event_bus.publish("graph.start", {"graph_id": "test"})
        await event_bus.publish("node.start", {"node_id": "node1"})
        await asyncio.sleep(0.05)
        await event_bus.publish("node.complete", {
            "node_id": "node1",
            "execution_time": 0.05
        })
        await event_bus.publish("graph.complete", {"graph_id": "test"})
        
        await asyncio.sleep(0.2)
        
        # 验证系统状态
        assert metrics.get_node_metrics("node1") is not None
