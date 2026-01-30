#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控和可观察性测试脚本
测试性能指标收集、日志订阅和事件总线优化

响应任务：任务 16.4 - 添加性能监控测试
"""

import asyncio
import time
import random
from pathlib import Path

from core.metrics import get_metrics_collector
from core.logger_subscriber import get_logger_subscriber
from core.async_event_bus import get_async_event_bus
from core.event_bus import get_event_bus


class MonitoringTester:
    """监控功能测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.metrics_collector = get_metrics_collector()
        self.logger_subscriber = get_logger_subscriber()
        self.async_event_bus = get_async_event_bus()
        self.event_bus = get_event_bus()
        
        # 测试结果
        self.test_results = {}
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("监控和可观察性测试开始")
        print("=" * 60)
        
        try:
            # 启动监控组件
            await self._start_monitoring()
            
            # 1. 测试指标收集
            await self.test_metrics_collection()
            
            # 2. 测试事件发布频率
            await self.test_event_publishing()
            
            # 3. 测试日志订阅
            await self.test_log_subscription()
            
            # 4. 测试事件节流
            await self.test_event_throttling()
            
            # 5. 测试异步事件总线
            await self.test_async_event_bus()
            
            # 停止监控组件
            await self._stop_monitoring()
            
            # 输出测试结果
            self.print_test_results()
            
        except Exception as e:
            print(f"测试过程中发生异常: {e}")
            import traceback
            traceback.print_exc()
    
    async def _start_monitoring(self):
        """启动监控组件"""
        print("\n启动监控组件...")
        
        # 启动指标收集器
        await self.metrics_collector.start()
        
        # 启动日志订阅者
        self.logger_subscriber.start()
        
        # 启动异步事件总线
        await self.async_event_bus.start()
        
        print("监控组件启动完成")
    
    async def _stop_monitoring(self):
        """停止监控组件"""
        print("\n停止监控组件...")
        
        # 停止指标收集器
        await self.metrics_collector.stop()
        
        # 停止日志订阅者
        self.logger_subscriber.stop()
        
        # 停止异步事件总线
        await self.async_event_bus.stop()
        
        print("监控组件停止完成")
    
    async def test_metrics_collection(self):
        """测试指标收集准确性"""
        print("\n1. 测试指标收集准确性...")
        
        try:
            # 模拟节点执行事件
            test_nodes = ['test_node_1', 'test_node_2', 'test_node_3']
            
            for i in range(10):
                for node_id in test_nodes:
                    # 发布节点开始事件
                    self.event_bus.publish('node.start', {
                        'node_id': node_id,
                        'packet_id': f'packet_{i}'
                    })
                    
                    # 模拟执行时间
                    execution_time = random.uniform(0.01, 0.1)
                    await asyncio.sleep(execution_time)
                    
                    # 发布节点完成事件
                    if random.random() > 0.1:  # 90% 成功率
                        self.event_bus.publish('node.complete', {
                            'node_id': node_id,
                            'packet_id': f'packet_{i}',
                            'execution_time': execution_time
                        })
                    else:
                        # 模拟错误
                        self.event_bus.publish('node.error', {
                            'node_id': node_id,
                            'packet_id': f'packet_{i}',
                            'error': 'test error'
                        })
            
            # 等待指标收集
            await asyncio.sleep(2)
            
            # 检查指标
            metrics_found = 0
            for node_id in test_nodes:
                node_metrics = self.metrics_collector.get_node_metrics(node_id)
                if node_metrics and node_metrics.execution_count > 0:
                    metrics_found += 1
                    print(f"  ✓ {node_id}: 执行{node_metrics.execution_count}次, "
                          f"错误{node_metrics.error_count}次, "
                          f"平均耗时{node_metrics.get_average_time():.3f}s")
            
            if metrics_found == len(test_nodes):
                self.test_results['metrics_collection'] = "成功"
            else:
                self.test_results['metrics_collection'] = f"部分成功: {metrics_found}/{len(test_nodes)}"
                
        except Exception as e:
            self.test_results['metrics_collection'] = f"异常: {e}"
    
    async def test_event_publishing(self):
        """测试事件发布频率"""
        print("\n2. 测试事件发布频率...")
        
        try:
            # 记录发布的事件
            published_events = []
            
            def event_counter(event_data):
                published_events.append(time.time())
            
            # 订阅测试事件
            self.event_bus.subscribe('test.frequency', event_counter)
            
            # 快速发布事件
            start_time = time.time()
            for i in range(100):
                self.event_bus.publish('test.frequency', {'index': i})
                await asyncio.sleep(0.001)  # 1ms间隔
            
            # 等待处理完成
            await asyncio.sleep(1)
            
            # 计算频率
            duration = time.time() - start_time
            actual_frequency = len(published_events) / duration
            
            print(f"  发布频率: {actual_frequency:.1f} events/s")
            print(f"  处理事件: {len(published_events)}/100")
            
            if len(published_events) >= 90:  # 允许少量丢失
                self.test_results['event_publishing'] = "成功"
            else:
                self.test_results['event_publishing'] = f"部分成功: {len(published_events)}/100"
                
        except Exception as e:
            self.test_results['event_publishing'] = f"异常: {e}"
    
    async def test_log_subscription(self):
        """测试日志订阅功能"""
        print("\n3. 测试日志订阅功能...")
        
        try:
            # 检查日志文件是否创建
            log_dir = Path("./logs")
            expected_files = ['system.log', 'performance.log', 'error.log']
            
            # 发布一些测试事件
            self.event_bus.publish('graph.start', {
                'graph_name': 'test_graph',
                'node_count': 3
            })
            
            self.event_bus.publish('node.error', {
                'node_id': 'test_node',
                'error': 'test error message',
                'packet_id': 'test_packet'
            })
            
            self.event_bus.publish('node.performance', {
                'node_id': 'test_node',
                'execution_count': 100,
                'error_rate': 0.05,
                'average_time': 0.025
            })
            
            # 等待日志写入
            await asyncio.sleep(1)
            
            # 检查日志文件
            found_files = 0
            for filename in expected_files:
                log_file = log_dir / filename
                if log_file.exists() and log_file.stat().st_size > 0:
                    found_files += 1
                    print(f"  ✓ {filename}: {log_file.stat().st_size} bytes")
                else:
                    print(f"  ✗ {filename}: 不存在或为空")
            
            if found_files == len(expected_files):
                self.test_results['log_subscription'] = "成功"
            else:
                self.test_results['log_subscription'] = f"部分成功: {found_files}/{len(expected_files)}"
                
        except Exception as e:
            self.test_results['log_subscription'] = f"异常: {e}"
    
    async def test_event_throttling(self):
        """测试事件节流功能"""
        print("\n4. 测试事件节流功能...")
        
        try:
            # 测试异步事件总线的节流功能
            throttled_events = []
            
            async def throttle_counter(event_data):
                throttled_events.append(time.time())
            
            # 订阅会被节流的事件
            self.async_event_bus.subscribe_async('node.performance', throttle_counter)
            
            # 快速发布大量事件
            start_time = time.time()
            for i in range(50):
                self.async_event_bus.publish('node.performance', {'index': i})
                await asyncio.sleep(0.01)  # 10ms间隔
            
            # 等待处理
            await asyncio.sleep(2)
            
            # 检查节流效果
            duration = time.time() - start_time
            received_count = len(throttled_events)
            
            print(f"  发布事件: 50")
            print(f"  接收事件: {received_count}")
            print(f"  节流效果: {(50 - received_count) / 50 * 100:.1f}% 被节流")
            
            # 获取节流统计
            stats = self.async_event_bus.get_statistics()
            throttle_stats = stats.get('throttle_stats', {})
            
            print(f"  节流统计: {throttle_stats}")
            
            if received_count < 50:  # 应该有事件被节流
                self.test_results['event_throttling'] = "成功"
            else:
                self.test_results['event_throttling'] = "节流未生效"
                
        except Exception as e:
            self.test_results['event_throttling'] = f"异常: {e}"
    
    async def test_async_event_bus(self):
        """测试异步事件总线"""
        print("\n5. 测试异步事件总线...")
        
        try:
            # 测试异步发布和订阅
            async_events = []
            
            async def async_handler(event_data):
                async_events.append(event_data)
                await asyncio.sleep(0.001)  # 模拟异步处理
            
            # 订阅异步事件
            self.async_event_bus.subscribe_async('test.async', async_handler)
            
            # 异步发布事件
            for i in range(20):
                await self.async_event_bus.publish_async('test.async', {'index': i})
            
            # 等待处理完成
            await asyncio.sleep(1)
            
            # 检查结果
            print(f"  发布事件: 20")
            print(f"  处理事件: {len(async_events)}")
            
            # 获取统计信息
            stats = self.async_event_bus.get_statistics()
            print(f"  队列大小: {stats['queue_size']}")
            print(f"  处理计数: {stats['processed_count']}")
            print(f"  错误计数: {stats['error_count']}")
            
            if len(async_events) >= 18:  # 允许少量丢失
                self.test_results['async_event_bus'] = "成功"
            else:
                self.test_results['async_event_bus'] = f"部分成功: {len(async_events)}/20"
                
        except Exception as e:
            self.test_results['async_event_bus'] = f"异常: {e}"
    
    def print_test_results(self):
        """输出测试结果"""
        print("\n" + "=" * 60)
        print("监控和可观察性测试结果")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✓" if "成功" in result else "✗"
            print(f"{status} {test_name}: {result}")
        
        # 统计
        success_count = sum(1 for result in self.test_results.values() if "成功" in result)
        total_count = len(self.test_results)
        
        print(f"\n总体结果: {success_count}/{total_count} 项测试通过")
        
        if success_count == total_count:
            print("🎉 监控和可观察性测试全部通过！")
        else:
            print("⚠️  部分测试未通过，请检查上述结果")
        
        # 输出最终统计
        print("\n" + "=" * 60)
        print("最终统计信息")
        print("=" * 60)
        
        # 指标收集器统计
        metrics_stats = self.metrics_collector.get_all_metrics()
        print(f"指标收集器:")
        print(f"  - 监控节点数: {len(metrics_stats['nodes'])}")
        print(f"  - 监控图数: {len(metrics_stats['graphs'])}")
        print(f"  - 整体FPS: {metrics_stats['overall']['fps']:.1f}")
        print(f"  - 整体错误率: {metrics_stats['overall']['error_rate']:.2%}")
        
        # 异步事件总线统计
        bus_stats = self.async_event_bus.get_statistics()
        print(f"异步事件总线:")
        print(f"  - 发布事件数: {bus_stats['published_count']}")
        print(f"  - 处理事件数: {bus_stats['processed_count']}")
        print(f"  - 错误事件数: {bus_stats['error_count']}")
        print(f"  - 订阅者数: {bus_stats['subscribers_count'] + bus_stats['async_subscribers_count']}")


async def main():
    """主函数"""
    tester = MonitoringTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
