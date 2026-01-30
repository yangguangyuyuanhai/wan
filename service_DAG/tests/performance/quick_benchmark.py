# -*- coding: utf-8 -*-
"""
快速性能测试
用于快速验证系统性能
"""

import asyncio
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from plugins.basic.test_node import TestProducerNode, TestConsumerNode, TestProcessNode
from engine.graph import Graph
from engine.streaming_executor import StreamingExecutor
from core.context import GlobalContext


async def quick_test():
    """快速性能测试"""
    print("="*60)
    print("快速性能测试")
    print("="*60)
    
    # 创建图定义
    from engine.graph import GraphDefinition, NodeDefinition, Connection
    
    graph_def = GraphDefinition(
        name="QuickTest",
        version="1.0.0",
        nodes=[
            NodeDefinition(id="producer", type="test_producer"),
            NodeDefinition(id="processor", type="test_process"),
            NodeDefinition(id="consumer", type="test_consumer")
        ],
        connections=[
            Connection(from_node="producer", from_port="data", 
                      to_node="processor", to_port="input"),
            Connection(from_node="processor", from_port="output", 
                      to_node="consumer", to_port="data")
        ]
    )
    
    # 创建图
    graph = Graph(graph_def)
    
    # 创建节点
    producer = TestProducerNode("producer", {"count": 100, "interval": 0.01})
    processor = TestProcessNode("processor", {})
    consumer = TestConsumerNode("consumer", {})
    
    nodes = {
        "producer": producer,
        "processor": processor,
        "consumer": consumer
    }
    
    # 添加节点到图
    graph.add_node("producer", producer)
    graph.add_node("processor", processor)
    graph.add_node("consumer", consumer)
    
    # 验证图
    is_valid, errors = graph.validate()
    if not is_valid:
        print(f"图验证失败: {errors}")
        return
    
    print("图验证成功!")
    
    # 初始化全局上下文
    context = GlobalContext()
    context.set("error_strategy", "circuit-break")
    context.set("queue_max_size", 10)
    
    # 创建执行器
    executor = StreamingExecutor(graph, nodes, context)
    
    # 启动执行器
    print("\n启动执行器...")
    start_time = time.time()
    await executor.start()
    
    # 等待处理完成
    print("等待处理完成...")
    await asyncio.sleep(5)  # 等待5秒
    
    # 停止执行器
    print("停止执行器...")
    await executor.stop()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # 打印统计
    print(f"\n{'='*60}")
    print("测试结果")
    print(f"{'='*60}")
    print(f"持续时间: {duration:.2f} 秒")
    print(f"生产者发送: {producer.count} 条数据")
    print(f"消费者接收: {consumer.received_count} 条数据")
    
    if consumer.received_count > 0:
        fps = consumer.received_count / duration
        print(f"吞吐量: {fps:.2f} 条/秒")
        print("\n✅ 测试通过!")
    else:
        print("\n❌ 测试失败: 没有接收到数据")
    
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(quick_test())
