# -*- coding: utf-8 -*-
"""
事件总线
系统的"神经"，负责跨组件的消息传递
解耦模块间的通信
"""

import time
import threading
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import queue


class EventPriority(Enum):
    """事件优先级"""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class Event:
    """
    事件对象
    封装事件的所有信息
    """
    # 事件主题（如 "sys.startup", "node.error"）
    topic: str
    
    # 事件数据
    data: Any = None
    
    # 事件源（发布者）
    source: str = ""
    
    # 时间戳
    timestamp: float = field(default_factory=time.time)
    
    # 优先级
    priority: EventPriority = EventPriority.NORMAL
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"Event(topic={self.topic}, source={self.source}, priority={self.priority.name})"
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority.value > other.priority.value  # 优先级高的先处理


class EventBus:
    """
    事件总线
    实现发布-订阅模式的事件系统
    """
    
    def __init__(self, name: str = "EventBus", async_mode: bool = True):
        """
        初始化事件总线
        
        Args:
            name: 事件总线名称
            async_mode: 是否异步处理事件
        """
        self.name = name
        self.async_mode = async_mode
        
        # 订阅者字典：topic -> [callbacks]
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # 订阅者锁
        self._lock = threading.RLock()
        
        # 事件队列（异步模式）
        self._event_queue: Optional[queue.PriorityQueue] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        
        # 统计信息
        self._published_count = 0
        self._processed_count = 0
        self._error_count = 0
        
        if self.async_mode:
            self._start_worker()
    
    def _start_worker(self):
        """启动异步工作线程"""
        self._event_queue = queue.PriorityQueue()
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
    
    def _worker_loop(self):
        """工作线程主循环"""
        while self._running:
            try:
                # 获取事件（带优先级）
                event = self._event_queue.get(timeout=0.1)
                
                # 分发事件
                self._dispatch_event(event)
                
                self._event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self._error_count += 1
                print(f"[{self.name}] 事件处理异常: {e}")
    
    def subscribe(self, topic: str, callback: Callable[[Event], None]):
        """
        订阅事件
        
        Args:
            topic: 事件主题（支持通配符 "*"）
            callback: 回调函数，接收 Event 对象
        """
        with self._lock:
            self._subscribers[topic].append(callback)
    
    def unsubscribe(self, topic: str, callback: Callable[[Event], None]):
        """
        取消订阅
        
        Args:
            topic: 事件主题
            callback: 回调函数
        """
        with self._lock:
            if topic in self._subscribers:
                try:
                    self._subscribers[topic].remove(callback)
                except ValueError:
                    pass
    
    def publish(self, topic: str, data: Any = None, source: str = "",
                priority: EventPriority = EventPriority.NORMAL, **metadata):
        """
        发布事件
        
        Args:
            topic: 事件主题
            data: 事件数据
            source: 事件源
            priority: 优先级
            **metadata: 元数据
        """
        event = Event(
            topic=topic,
            data=data,
            source=source,
            priority=priority,
            metadata=metadata
        )
        
        self._published_count += 1
        
        if self.async_mode:
            # 异步模式：放入队列
            self._event_queue.put(event)
        else:
            # 同步模式：立即分发
            self._dispatch_event(event)
    
    def _dispatch_event(self, event: Event):
        """
        分发事件到订阅者
        
        Args:
            event: 事件对象
        """
        with self._lock:
            # 精确匹配
            callbacks = self._subscribers.get(event.topic, []).copy()
            
            # 通配符匹配
            if "*" in self._subscribers:
                callbacks.extend(self._subscribers["*"])
            
            # 前缀匹配（如 "node.*" 匹配 "node.error"）
            for topic, subs in self._subscribers.items():
                if topic.endswith(".*"):
                    prefix = topic[:-2]
                    if event.topic.startswith(prefix + "."):
                        callbacks.extend(subs)
        
        # 调用所有订阅者
        for callback in callbacks:
            try:
                callback(event)
                self._processed_count += 1
            except Exception as e:
                self._error_count += 1
                print(f"[{self.name}] 订阅者回调异常: {e}")
    
    def wait_for_event(self, topic: str, timeout: float = None) -> Optional[Event]:
        """
        等待特定事件（阻塞）
        
        Args:
            topic: 事件主题
            timeout: 超时时间（秒）
            
        Returns:
            事件对象，超时返回 None
        """
        result_queue = queue.Queue()
        
        def callback(event: Event):
            result_queue.put(event)
        
        self.subscribe(topic, callback)
        
        try:
            event = result_queue.get(timeout=timeout)
            return event
        except queue.Empty:
            return None
        finally:
            self.unsubscribe(topic, callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            subscriber_count = sum(len(subs) for subs in self._subscribers.values())
            
            return {
                "name": self.name,
                "async_mode": self.async_mode,
                "published_count": self._published_count,
                "processed_count": self._processed_count,
                "error_count": self._error_count,
                "subscriber_count": subscriber_count,
                "topics": list(self._subscribers.keys())
            }
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print(f"事件总线统计: {stats['name']}")
        print("=" * 60)
        print(f"模式: {'异步' if stats['async_mode'] else '同步'}")
        print(f"已发布事件: {stats['published_count']}")
        print(f"已处理事件: {stats['processed_count']}")
        print(f"错误次数: {stats['error_count']}")
        print(f"订阅者数量: {stats['subscriber_count']}")
        print(f"订阅主题: {', '.join(stats['topics'])}")
        print("=" * 60)
    
    def shutdown(self):
        """关闭事件总线"""
        if self.async_mode:
            self._running = False
            if self._worker_thread:
                self._worker_thread.join(timeout=2)


# ==================== 预定义事件主题 ====================

class SystemEvents:
    """系统事件"""
    STARTUP = "sys.startup"
    SHUTDOWN = "sys.shutdown"
    ERROR = "sys.error"
    WARNING = "sys.warning"


class NodeEvents:
    """节点事件"""
    CREATED = "node.created"
    STARTED = "node.started"
    STOPPED = "node.stopped"
    ERROR = "node.error"
    COMPLETED = "node.completed"


class GraphEvents:
    """图事件"""
    LOADED = "graph.loaded"
    STARTED = "graph.started"
    STOPPED = "graph.stopped"
    THROUGHPUT = "graph.throughput"
    CYCLE_DETECTED = "graph.cycle"


class DataEvents:
    """数据事件"""
    RECEIVED = "data.received"
    PROCESSED = "data.processed"
    DROPPED = "data.dropped"


# ==================== 全局事件总线实例 ====================

global_event_bus = EventBus(name="GlobalEventBus", async_mode=True)


if __name__ == "__main__":
    # 测试事件总线
    print("事件总线测试\n")
    
    # 创建事件总线
    bus = EventBus(name="TestBus", async_mode=True)
    
    # 订阅者1：监听所有事件
    def on_any_event(event: Event):
        print(f"[订阅者1] 收到事件: {event}")
    
    bus.subscribe("*", on_any_event)
    
    # 订阅者2：只监听错误事件
    def on_error(event: Event):
        print(f"[订阅者2] 错误事件: {event.data}")
    
    bus.subscribe(NodeEvents.ERROR, on_error)
    
    # 订阅者3：监听所有节点事件
    def on_node_event(event: Event):
        print(f"[订阅者3] 节点事件: {event.topic}")
    
    bus.subscribe("node.*", on_node_event)
    
    # 发布事件
    print("\n发布事件:")
    bus.publish(SystemEvents.STARTUP, data="系统启动", source="Main")
    bus.publish(NodeEvents.STARTED, data="节点1启动", source="Node1")
    bus.publish(NodeEvents.ERROR, data="节点2错误", source="Node2", priority=EventPriority.HIGH)
    
    # 等待异步处理完成
    time.sleep(0.5)
    
    # 打印统计
    bus.print_statistics()
    
    # 关闭
    bus.shutdown()
    
    print("\n测试完成")



def get_event_bus() -> EventBus:
    """
    获取全局事件总线实例
    
    Returns:
        全局事件总线
    """
    return global_event_bus
