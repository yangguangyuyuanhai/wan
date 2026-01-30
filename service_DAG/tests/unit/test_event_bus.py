"""
单元测试 - 事件总线模块
测试同步和异步事件总线的功能
"""
import pytest
import asyncio
from service_DAG.core.event_bus import EventBus
from service_DAG.core.async_event_bus import AsyncEventBus


class TestEventBus:
    """同步事件总线测试"""
    
    def test_subscribe_and_publish(self):
        """测试订阅和发布"""
        bus = EventBus()
        received = []
        
        def handler(data):
            received.append(data)
        
        bus.subscribe("test.event", handler)
        bus.publish("test.event", {"value": 42})
        
        assert len(received) == 1
        assert received[0]["value"] == 42
    
    def test_multiple_subscribers(self):
        """测试多个订阅者"""
        bus = EventBus()
        received1 = []
        received2 = []
        
        bus.subscribe("test.event", lambda d: received1.append(d))
        bus.subscribe("test.event", lambda d: received2.append(d))
        bus.publish("test.event", {"value": 1})
        
        assert len(received1) == 1
        assert len(received2) == 1
    
    def test_unsubscribe(self):
        """测试取消订阅"""
        bus = EventBus()
        received = []
        
        def handler(data):
            received.append(data)
        
        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        bus.publish("test.event", {"value": 1})
        
        assert len(received) == 0
    
    def test_wildcard_subscription(self):
        """测试通配符订阅"""
        bus = EventBus()
        received = []
        
        bus.subscribe("node.*", lambda d: received.append(d))
        bus.publish("node.start", {"id": "1"})
        bus.publish("node.complete", {"id": "2"})
        bus.publish("graph.start", {"id": "3"})
        
        assert len(received) == 2


class TestAsyncEventBus:
    """异步事件总线测试"""
    
    @pytest.mark.asyncio
    async def test_async_subscribe_and_publish(self):
        """测试异步订阅和发布"""
        bus = AsyncEventBus()
        received = []
        
        async def handler(data):
            received.append(data)
        
        bus.subscribe("test.event", handler)
        await bus.publish("test.event", {"value": 42})
        await asyncio.sleep(0.1)  # 等待异步处理
        
        assert len(received) == 1
        assert received[0]["value"] == 42
    
    @pytest.mark.asyncio
    async def test_event_throttling(self):
        """测试事件节流"""
        bus = AsyncEventBus()
        received = []
        
        async def handler(data):
            received.append(data)
        
        bus.subscribe("test.event", handler, throttle_ms=100)
        
        # 快速发布多个事件
        for i in range(10):
            await bus.publish("test.event", {"value": i})
        
        await asyncio.sleep(0.2)
        
        # 由于节流，应该只收到部分事件
        assert len(received) < 10
    
    @pytest.mark.asyncio
    async def test_async_multiple_subscribers(self):
        """测试多个异步订阅者"""
        bus = AsyncEventBus()
        received1 = []
        received2 = []
        
        async def handler1(data):
            received1.append(data)
        
        async def handler2(data):
            received2.append(data)
        
        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)
        await bus.publish("test.event", {"value": 1})
        await asyncio.sleep(0.1)
        
        assert len(received1) == 1
        assert len(received2) == 1
