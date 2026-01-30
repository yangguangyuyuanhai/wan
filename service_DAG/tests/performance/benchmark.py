# -*- coding: utf-8 -*-
"""
性能基准测试
测量 DAG 系统的关键性能指标
"""

import asyncio
import time
import psutil
import os
import sys
from typing import Dict, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.data_types import ImageType, NumberType
from core.context import GlobalContext
from core.event_bus import EventBus
from engine.node import INode, NodeMetadata, NodeState
from engine.port import InputPort, OutputPort
from engine.graph import Graph
from engine.streaming_executor import StreamingExecutor
import numpy as np


# ==================== 测试节点 ====================

class BenchmarkProducerNode(INode):
    """性能测试数据生产者"""
    
    __plugin_metadata__ = {
        "type": "benchmark_producer",
        "name": "Benchmark Producer",
        "version": "1.0.0",
        "author": "System",
        "description": "生成测试数据用于性能基准测试",
        "category": "test"
    }
    
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.state = NodeState.IDLE
        
        # 配置参数
        self.image_width = config.get("image_width", 1920)
        self.image_height = config.get("image_height", 1080)
        self.total_frames = config.get("total_frames", 1000)
        self.frame_count = 0
        
    def get_metadata(self) -> NodeMetadata:
        return NodeMetadata(
            node_id=self.node_id,
            node_type="benchmark_producer",
            display_name="Benchmark Producer",
            description="生成测试数据"
        )
    
    def get_ports(self) -> tuple:
        inputs = []
        outputs = [
            OutputPort("image", ImageType(), required=True)
        ]
        return inputs, outputs
    
    def validate_config(self) -> tuple:
        return True, ""
    
    async def initialize(self):
        """初始化节点"""
        self.state = NodeState.IDLE
        self.frame_count = 0
    
    async def run(self, inputs: Dict) -> Dict:
        """生成测试图像"""
        if self.frame_count >= self.total_frames:
            return None  # 完成所有帧
        
        # 生成随机图像
        image = np.random.randint(0, 255, 
                                 (self.image_height, self.image_width, 3), 
                                 dtype=np.uint8)
        
        self.frame_count += 1
        
        return {
            "image": ImageType(
                data=image,
                width=self.image_width,
                height=self.image_height,
                format="BGR"
            )
        }
    
    async def cleanup(self):
        """清理资源"""
        pass


class BenchmarkProcessNode(INode):
    """性能测试处理节点"""
    
    __plugin_metadata__ = {
        "type": "benchmark_process",
        "name": "Benchmark Process",
        "version": "1.0.0",
        "author": "System",
        "description": "模拟图像处理",
        "category": "test"
    }
    
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.state = NodeState.IDLE
        
        # 配置参数
        self.processing_delay = config.get("processing_delay", 0.001)  # 1ms
        
    def get_metadata(self) -> NodeMetadata:
        return NodeMetadata(
            node_id=self.node_id,
            node_type="benchmark_process",
            display_name="Benchmark Process",
            description="模拟图像处理"
        )
    
    def get_ports(self) -> tuple:
        inputs = [
            InputPort("image", ImageType(), required=True)
        ]
        outputs = [
            OutputPort("image", ImageType(), required=True)
        ]
        return inputs, outputs
    
    def validate_config(self) -> tuple:
        return True, ""
    
    async def initialize(self):
        """初始化节点"""
        self.state = NodeState.IDLE
    
    async def run(self, inputs: Dict) -> Dict:
        """处理图像"""
        # 模拟处理延迟
        await asyncio.sleep(self.processing_delay)
        
        # 简单的图像处理（模拟）
        image_data = inputs["image"]
        if hasattr(image_data, 'data'):
            processed = image_data.data * 0.9  # 简单的亮度调整
            
            return {
                "image": ImageType(
                    data=processed.astype(np.uint8),
                    width=image_data.width,
                    height=image_data.height,
                    format=image_data.format
                )
            }
        
        return {"image": image_data}
    
    async def cleanup(self):
        """清理资源"""
        pass


class BenchmarkConsumerNode(INode):
    """性能测试数据消费者"""
    
    __plugin_metadata__ = {
        "type": "benchmark_consumer",
        "name": "Benchmark Consumer",
        "version": "1.0.0",
        "author": "System",
        "description": "接收测试数据并统计",
        "category": "test"
    }
    
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.state = NodeState.IDLE
        
        # 统计信息
        self.received_count = 0
        self.start_time = None
        self.end_time = None
        self.latencies = []
        
    def get_metadata(self) -> NodeMetadata:
        return NodeMetadata(
            node_id=self.node_id,
            node_type="benchmark_consumer",
            display_name="Benchmark Consumer",
            description="接收测试数据"
        )
    
    def get_ports(self) -> tuple:
        inputs = [
            InputPort("image", ImageType(), required=True)
        ]
        outputs = []
        return inputs, outputs
    
    def validate_config(self) -> tuple:
        return True, ""
    
    async def initialize(self):
        """初始化节点"""
        self.state = NodeState.IDLE
        self.received_count = 0
        self.start_time = None
        self.end_time = None
        self.latencies = []
    
    async def run(self, inputs: Dict) -> Dict:
        """接收数据"""
        if self.start_time is None:
            self.start_time = time.time()
        
        self.received_count += 1
        self.end_time = time.time()
        
        # 记录延迟（如果有时间戳）
        if hasattr(inputs.get("image"), 'timestamp'):
            latency = time.time() - inputs["image"].timestamp
            self.latencies.append(latency)
        
        return {}
    
    async def cleanup(self):
        """清理资源"""
        pass
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        fps = self.received_count / duration if duration > 0 else 0
        
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        
        return {
            "received_count": self.received_count,
            "duration": duration,
            "fps": fps,
            "avg_latency": avg_latency * 1000,  # 转换为毫秒
            "latencies": self.latencies
        }


# ==================== 性能测试器 ====================

class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self):
        self.results = {}
        
    async def run_test(self, test_name: str, graph: Graph, 
                      nodes: Dict[str, INode], total_frames: int = 1000):
        """
        运行性能测试
        
        Args:
            test_name: 测试名称
            graph: 图对象
            nodes: 节点字典
            total_frames: 总帧数
        """
        print(f"\n{'='*60}")
        print(f"运行测试: {test_name}")
        print(f"{'='*60}")
        
        # 初始化全局上下文
        context = GlobalContext()
        context.set("error_strategy", "circuit-break")
        context.set("queue_max_size", 10)
        
        # 创建执行器
        executor = StreamingExecutor(graph, nodes, context)
        
        # 记录初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 启动执行器
        print("启动执行器...")
        await executor.start()
        
        # 等待处理完成
        print(f"处理 {total_frames} 帧...")
        start_time = time.time()
        
        # 等待消费者接收所有数据
        consumer_node = nodes.get("consumer")
        while consumer_node and consumer_node.received_count < total_frames:
            await asyncio.sleep(0.1)
            
            # 超时检查（60秒）
            if time.time() - start_time > 60:
                print("警告: 测试超时")
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 停止执行器
        print("停止执行器...")
        await executor.stop()
        
        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # 收集统计信息
        stats = consumer_node.get_statistics() if consumer_node else {}
        
        # 计算性能指标
        fps = total_frames / duration if duration > 0 else 0
        avg_latency = stats.get("avg_latency", 0)
        
        # 保存结果
        self.results[test_name] = {
            "total_frames": total_frames,
            "duration": duration,
            "fps": fps,
            "avg_latency": avg_latency,
            "initial_memory": initial_memory,
            "final_memory": final_memory,
            "memory_growth": memory_growth,
            "received_count": stats.get("received_count", 0)
        }
        
        # 打印结果
        self.print_test_result(test_name)
        
    def print_test_result(self, test_name: str):
        """打印测试结果"""
        result = self.results[test_name]
        
        print(f"\n测试结果: {test_name}")
        print(f"  总帧数: {result['total_frames']}")
        print(f"  接收帧数: {result['received_count']}")
        print(f"  持续时间: {result['duration']:.2f} 秒")
        print(f"  吞吐量: {result['fps']:.2f} FPS")
        print(f"  平均延迟: {result['avg_latency']:.2f} ms")
        print(f"  初始内存: {result['initial_memory']:.2f} MB")
        print(f"  最终内存: {result['final_memory']:.2f} MB")
        print(f"  内存增长: {result['memory_growth']:.2f} MB")
        
    def print_summary(self):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("性能基准测试总结")
        print(f"{'='*60}\n")
        
        for test_name, result in self.results.items():
            print(f"{test_name}:")
            print(f"  FPS: {result['fps']:.2f}")
            print(f"  延迟: {result['avg_latency']:.2f} ms")
            print(f"  内存增长: {result['memory_growth']:.2f} MB")
            print()
        
    def save_results(self, filename: str = "benchmark_results.txt"):
        """保存结果到文件"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("DAG 系统性能基准测试报告\n")
            f.write("="*60 + "\n\n")
            f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for test_name, result in self.results.items():
                f.write(f"\n{test_name}\n")
                f.write("-"*40 + "\n")
                f.write(f"总帧数: {result['total_frames']}\n")
                f.write(f"接收帧数: {result['received_count']}\n")
                f.write(f"持续时间: {result['duration']:.2f} 秒\n")
                f.write(f"吞吐量: {result['fps']:.2f} FPS\n")
                f.write(f"平均延迟: {result['avg_latency']:.2f} ms\n")
                f.write(f"初始内存: {result['initial_memory']:.2f} MB\n")
                f.write(f"最终内存: {result['final_memory']:.2f} MB\n")
                f.write(f"内存增长: {result['memory_growth']:.2f} MB\n")
        
        print(f"\n结果已保存到: {filepath}")


# ==================== 主测试函数 ====================

async def test_simple_pipeline():
    """测试简单的 Producer -> Consumer 管道"""
    # 创建图
    graph = Graph()
    
    # 创建节点
    producer = BenchmarkProducerNode("producer", {"total_frames": 1000})
    consumer = BenchmarkConsumerNode("consumer", {})
    
    nodes = {
        "producer": producer,
        "consumer": consumer
    }
    
    # 添加节点到图
    graph.add_node("producer", producer)
    graph.add_node("consumer", consumer)
    
    # 添加连接
    graph.add_connection("producer", "image", "consumer", "image")
    
    # 验证图
    is_valid, errors = graph.validate()
    if not is_valid:
        print(f"图验证失败: {errors}")
        return
    
    # 运行测试
    benchmark = PerformanceBenchmark()
    await benchmark.run_test("Simple Pipeline (Producer -> Consumer)", 
                            graph, nodes, total_frames=1000)
    
    return benchmark


async def test_processing_pipeline():
    """测试带处理的 Producer -> Process -> Consumer 管道"""
    # 创建图
    graph = Graph()
    
    # 创建节点
    producer = BenchmarkProducerNode("producer", {"total_frames": 1000})
    processor = BenchmarkProcessNode("processor", {"processing_delay": 0.001})
    consumer = BenchmarkConsumerNode("consumer", {})
    
    nodes = {
        "producer": producer,
        "processor": processor,
        "consumer": consumer
    }
    
    # 添加节点到图
    graph.add_node("producer", producer)
    graph.add_node("processor", processor)
    graph.add_node("consumer", consumer)
    
    # 添加连接
    graph.add_connection("producer", "image", "processor", "image")
    graph.add_connection("processor", "image", "consumer", "image")
    
    # 验证图
    is_valid, errors = graph.validate()
    if not is_valid:
        print(f"图验证失败: {errors}")
        return
    
    # 运行测试
    benchmark = PerformanceBenchmark()
    await benchmark.run_test("Processing Pipeline (Producer -> Process -> Consumer)", 
                            graph, nodes, total_frames=1000)
    
    return benchmark


async def main():
    """主函数"""
    print("="*60)
    print("DAG 系统性能基准测试")
    print("="*60)
    
    # 运行测试
    benchmark1 = await test_simple_pipeline()
    benchmark2 = await test_processing_pipeline()
    
    # 合并结果
    all_results = {}
    if benchmark1:
        all_results.update(benchmark1.results)
    if benchmark2:
        all_results.update(benchmark2.results)
    
    # 创建总结报告
    final_benchmark = PerformanceBenchmark()
    final_benchmark.results = all_results
    final_benchmark.print_summary()
    final_benchmark.save_results()
    
    print("\n性能基准测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
