# -*- coding: utf-8 -*-
"""
增强事件总线
实现异步发布和事件节流优化

响应任务：任务 13 - 优化事件总线性能
"""

import asyncio
import time
from typing import Dict, Any, Callable, List, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass
import threading


@dataclass
class ThrottleConfig:
    """事件节流配置"""
    interval: float  # 节流间隔（秒）
    max_events: int = 1  # 间隔内最大事件数
    drop_excess: bool = True  # 是否丢弃超出的事件


class EventThrottler:
    """
    事件节流器
    
    功能：
    1. 限制高频事件的发布频率
    2. 防止事件风暴
    3. 统计丢弃的事件
    """
    
    def __init__(self):
        """初始化事件节流器"""
        # 节流配置
        self.throttle_configs: Dict[str, ThrottleConfig] = {}
        
        # 事件时间戳记录
        self.event_timestamps: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # 统计信息
        self.dropped_events: Dict[str, int] = defaultdict(int)
        self.total_events: Dict[str, int] = defaultdict(int)
        
        # 默认节流配置
        self._setup_default_throttles()
    
    def _setup_default_throttles(self):
        """设置默认节流配置"""
        # 高频事件节流
        self.throttle_configs.update({
            'node.complete': ThrottleConfig(interval=0.1, max_events=10),  # 100ms内最多10个
            'node.performance': ThrottleConfig(interval=1.0, max_events=1),  # 1秒1次
            'queue.status': ThrottleConfig(interval=0.5, max_events=5),  # 500ms内最多5个
            'data.branch': ThrottleConfig(interval=0.1, max_events=20),  # 100ms内最多20个
        })
    
    def should_allow_event(self, topic: str) -> bool:
        """
        判断是否允许发布事件
        
        Args:
            topic: 事件主题
            
        Returns:
            bool: 是否允许发布
        """
        self.total_events[topic] += 1
        
        # 检查是否有节流配置
        if topic not in self.throttle_configs:
            return True
        
        config = self.throttle_configs[topic]
        current_time = time.time()
        timestamps = self.event_timestamps[topic]
        
        # 清理过期时间戳
        cutoff_time = current_time - config.interval
        while timestamps and timestamps[0] < cutoff_time:
            timestamps.popleft()
        
        # 检查是否超过限制
        if len(timestamps) >= config.max_events:
            if config.drop_excess:
                self.dropped_events[topic] += 1
                return False
            else:
                # 等待最旧事件过期
                return False
        
        # 记录时间戳
        timestamps.append(current_time)
        return True
    
    def add_throttle(self, topic: str, config: ThrottleConfig):
        """添加节流配置"""
        self.throttle_configs[topic] = config
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取节流统计信息"""
        return {
            'throttled_topics': list(self.throttle_configs.keys()),
            'dropped_events': dict(self.dropped_events),
            'total_events': dict(self.total_events),
            'drop_rates': {
                topic: self.dropped_events[topic] / max(self.total_events[topic], 1)
                for topic in self.total_events
            }
        }


class AsyncEventBus:
    """
    异步事件总线
    
    功能：
    1. 异步非阻塞事件发布
    2. 事件节流
    3. 批量事件处理
    4. 性能监控
    """
    
    def __init__(self, name: str = "AsyncEventBus"):
        """初始化异步事件总线"""
        self.name = name
        
        # 订阅者
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.async_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # 事件队列
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        
        # 节流器
        self.throttler = EventThrottler()
        
        # 运行状态
        self.running = False
        self.consumer_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.published_count = 0
        self.processed_count = 0
        self.error_count = 0
        
        # 锁
        self._lock = asyncio.Lock()
    
    async def start(self):
        """启动事件总线"""
        if self.running:
            return
        
        self.running = True
        self.consumer_task = asyncio.create_task(self._event_consumer())
    
    async def stop(self):
        """停止事件总线"""
        if not self.running:
            return
        
        self.running = False
        
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass
    
    def subscribe(self, topic: str, callback: Callable):
        """
        订阅事件（同步回调）
        
        Args:
            topic: 事件主题
            callback: 回调函数
        """
        self.subscribers[topic].append(callback)
    
    def subscribe_async(self, topic: str, callback: Callable):
        """
        订阅事件（异步回调）
        
        Args:
            topic: 事件主题
            callback: 异步回调函数
        """
        self.async_subscribers[topic].append(callback)
    
    def unsubscribe(self, topic: str, callback: Callable):
        """取消订阅"""
        if topic in self.subscribers:
            try:
                self.subscribers[topic].remove(callback)
            except ValueError:
                pass
        
        if topic in self.async_subscribers:
            try:
                self.async_subscribers[topic].remove(callback)
            except ValueError:
                pass
    
    def publish(self, topic: str, data: Any = None, **metadata):
        """
        发布事件（非阻塞）
        
        Args:
            topic: 事件主题
            data: 事件数据
            **metadata: 元数据
        """
        # 事件节流检查
        if not self.throttler.should_allow_event(topic):
            return
        
        # 创建事件
        event = {
            'topic': topic,
            'data': data,
            'timestamp': time.time(),
            'metadata': metadata
        }
        
        # 异步放入队列
        try:
            self.event_queue.put_nowait(event)
            self.published_count += 1
        except asyncio.QueueFull:
            # 队列满时丢弃事件
            self.throttler.dropped_events[topic] += 1
    
    async def publish_async(self, topic: str, data: Any = None, **metadata):
        """
        异步发布事件
        
        Args:
            topic: 事件主题
            data: 事件数据
            **metadata: 元数据
        """
        # 事件节流检查
        if not self.throttler.should_allow_event(topic):
            return
        
        # 创建事件
        event = {
            'topic': topic,
            'data': data,
            'timestamp': time.time(),
            'metadata': metadata
        }
        
        # 放入队列
        await self.event_queue.put(event)
        self.published_count += 1
    
    async def _event_consumer(self):
        """事件消费者循环"""
        batch_size = 10
        batch_timeout = 0.01  # 10ms
        
        while self.running:
            try:
                # 批量获取事件
                events = []
                deadline = asyncio.get_event_loop().time() + batch_timeout
                
                # 获取第一个事件
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=batch_timeout
                    )
                    events.append(event)
                except asyncio.TimeoutError:
                    continue
                
                # 尝试获取更多事件（批处理）
                while (len(events) < batch_size and 
                       asyncio.get_event_loop().time() < deadline):
                    try:
                        event = self.event_queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break
                
                # 批量处理事件
                await self._process_events_batch(events)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                print(f"事件消费异常: {e}")
    
    async def _process_events_batch(self, events: List[Dict[str, Any]]):
        """批量处理事件"""
        for event in events:
            await self._dispatch_event(event)
            self.processed_count += 1
    
    async def _dispatch_event(self, event: Dict[str, Any]):
        """分发单个事件"""
        topic = event['topic']
        
        # 收集所有匹配的订阅者
        sync_callbacks = []
        async_callbacks = []
        
        # 精确匹配
        sync_callbacks.extend(self.subscribers.get(topic, []))
        async_callbacks.extend(self.async_subscribers.get(topic, []))
        
        # 通配符匹配
        for pattern in self.subscribers:
            if self._match_topic(topic, pattern):
                sync_callbacks.extend(self.subscribers[pattern])
        
        for pattern in self.async_subscribers:
            if self._match_topic(topic, pattern):
                async_callbacks.extend(self.async_subscribers[pattern])
        
        # 执行同步回调（在线程池中）
        if sync_callbacks:
            loop = asyncio.get_event_loop()
            for callback in sync_callbacks:
                try:
                    await loop.run_in_executor(None, callback, event)
                except Exception as e:
                    self.error_count += 1
                    print(f"同步回调异常: {e}")
        
        # 执行异步回调
        if async_callbacks:
            tasks = []
            for callback in async_callbacks:
                try:
                    task = asyncio.create_task(callback(event))
                    tasks.append(task)
                except Exception as e:
                    self.error_count += 1
                    print(f"异步回调创建异常: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _match_topic(self, topic: str, pattern: str) -> bool:
        """匹配主题模式"""
        if pattern == "*":
            return True
        
        if "*" not in pattern:
            return topic == pattern
        
        # 简单通配符匹配
        parts = pattern.split("*")
        if len(parts) == 2:
            prefix, suffix = parts
            return topic.startswith(prefix) and topic.endswith(suffix)
        
        return False
    
    def add_throttle(self, topic: str, interval: float, max_events: int = 1):
        """添加事件节流"""
        config = ThrottleConfig(interval=interval, max_events=max_events)
        self.throttler.add_throttle(topic, config)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'published_count': self.published_count,
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'queue_size': self.event_queue.qsize(),
            'subscribers_count': sum(len(callbacks) for callbacks in self.subscribers.values()),
            'async_subscribers_count': sum(len(callbacks) for callbacks in self.async_subscribers.values()),
            'throttle_stats': self.throttler.get_statistics()
        }


# 全局实例
_async_event_bus = AsyncEventBus()


def get_async_event_bus() -> AsyncEventBus:
    """获取异步事件总线实例"""
    return _async_event_bus
