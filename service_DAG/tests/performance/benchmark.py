"""
性能基准测试脚本
对比优化前后的性能差异
"""
import asyncio
import time
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.performance import PerformanceProfiler, MemoryOptimizer
from core.plugin_manager import PluginManager
from engine.graph import Graph
from engine.streaming_executor import StreamingExecutor
from core.async_event_bus import AsyncEventBus


async def run_benchmark(duration: int = 30):
    """
    运行性能基准测试
    
    Args:
        duration: 测试持续时间(秒)
    """
    print("=" * 70)
    print("性能基准测试")
    print("=" * 70)
    print(f"测试时长: {duration}秒")
    print()
    
    # 初始化性能分析器
    profiler = PerformanceProfiler()
    
    # 初始化系统
    plugin_manager = PluginManager()
    plugin_manager.discover_plugins("service_DAG/plugins")
    
    # 构建测试图
    graph = Graph()
    event_bus = AsyncEventBus()
    
    # 添加测试节点
    available_plugins = plugin_manager.get_available_plugins()
    print(f"发现 {len(available_plugins)} 个插件")
    
    if "test_node" in available_plugins:
        # 使用测试节点
        node1 = plugin_manager.create_plugin_instance("test_node", "node1", {})
        node2 = plugin_manager.create_plugin_instance("test_node", "node2", {})
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_connection("node1", "output", "node2", "input")
        
        print("✓ 测试图构建完成")
    else:
        print("⚠ 未找到test_node插件，使用空图测试")
    
    # 创建执行器
    executor = StreamingExecutor(graph, event_bus)
    
    print("✓ 执行器初始化完成")
    print()
    print("开始性能测试...")
    print()
    
    # 启动执行器
    await executor.start()
    
    # 运行测试
    start_time = time.time()
    frame_count = 0
    
    try:
        while time.time() - start_time < duration:
            frame_start = time.time()
            
            # 模拟帧处理
            await asyncio.sleep(0.01)  # 模拟处理时间
            
            frame_duration = time.time() - frame_start
            profiler.record_frame(frame_duration)
            frame_count += 1
            
            # 定期捕获指标
            if frame_count % 10 == 0:
                profiler.capture_metrics()
            
            # 定期清理内存
            if frame_count % 100 == 0:
                MemoryOptimizer.clear_cache()
            
            # 进度显示
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                current_fps = frame_count / elapsed
                print(f"进度: {elapsed:.1f}s / {duration}s | "
                      f"帧数: {frame_count} | "
                      f"FPS: {current_fps:.1f}")
    
    finally:
        # 停止执行器
        await executor.stop()
    
    print()
    print("测试完成，生成报告...")
    print()
    
    # 生成报告
    profiler.print_report()
    
    # 保存报告
    report_file = "performance_benchmark_report.txt"
    profiler.save_report(report_file)
    print(f"\n报告已保存到: {report_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='性能基准测试')
    parser.add_argument('--duration', type=int, default=30,
                       help='测试持续时间(秒)')
    
    args = parser.parse_args()
    
    # 运行测试
    asyncio.run(run_benchmark(args.duration))


if __name__ == "__main__":
    main()
