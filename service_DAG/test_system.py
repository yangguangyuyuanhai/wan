# -*- coding: utf-8 -*-
"""
系统测试脚本
测试 DAG 系统的基本功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.context import Context
from core.event_bus import get_event_bus
from core.plugin_manager import PluginManager
from engine.graph import GraphDefinition, Graph
from engine.streaming_executor import StreamingExecutor
from logger_config import get_logger


logger = get_logger("TestSystem")


async def test_basic_system():
    """测试基本系统功能"""
    
    print("=" * 60)
    print("DAG 系统基本功能测试")
    print("=" * 60)
    
    try:
        # 1. 初始化上下文
        print("\n1. 初始化上下文...")
        context = Context(
            config={
                'error_strategy': 'circuit-break',
                'max_retries': 3,
                'queue_size': 5
            }
        )
        
        # 2. 初始化事件总线
        print("2. 初始化事件总线...")
        event_bus = get_event_bus()
        context.event_bus = event_bus
        
        # 订阅事件
        events_received = []
        
        def event_handler(event):
            events_received.append(event.topic)
            print(f"   [Event] {event.topic}")
        
        event_bus.subscribe("*", event_handler)
        
        # 3. 创建插件管理器
        print("3. 创建插件管理器...")
        plugin_dirs = [str(Path(__file__).parent / "plugins")]
        plugin_manager = PluginManager(plugin_dirs, logger=logger)
        
        plugin_count = plugin_manager.discover_plugins()
        print(f"   发现 {plugin_count} 个插件")
        
        # 列出插件
        for plugin in plugin_manager.list_plugins():
            print(f"   - {plugin['type']}: {plugin.get('name', 'Unknown')}")
        
        # 4. 加载测试图定义
        print("4. 加载测试图定义...")
        config_path = Path(__file__).parent / "config" / "test_pipeline.json"
        
        if not config_path.exists():
            print(f"   错误：配置文件不存在: {config_path}")
            return False
        
        graph_def = GraphDefinition.load_from_file(str(config_path))
        print(f"   图名称: {graph_def.name}")
        print(f"   节点数: {len(graph_def.nodes)}")
        
        # 5. 创建图并实例化节点
        print("5. 创建图并实例化节点...")
        graph = Graph(graph_def)
        
        for node_def in graph_def.nodes:
            node_instance = plugin_manager.create_plugin_instance(
                plugin_type=node_def.type,
                node_id=node_def.id,
                config=node_def.config
            )
            graph.add_node(node_def.id, node_instance)
            print(f"   创建节点: {node_def.id} ({node_def.type})")
        
        # 6. 验证图
        print("6. 验证图...")
        graph.validate()
        print("   图验证通过")
        
        order = graph.topological_sort()
        print(f"   执行顺序: {' -> '.join(order)}")
        
        # 7. 创建执行器
        print("7. 创建流式执行器...")
        executor = StreamingExecutor(
            graph=graph,
            global_context=context,
            queue_size=5
        )
        
        # 8. 启动执行器
        print("8. 启动执行器...")
        await executor.start()
        print("   执行器已启动")
        
        # 9. 运行一段时间
        print("9. 运行测试（5秒）...")
        await asyncio.sleep(5)
        
        # 10. 停止执行器
        print("10. 停止执行器...")
        await executor.stop()
        print("   执行器已停止")
        
        # 11. 显示统计信息
        print("\n11. 统计信息:")
        stats = executor.get_statistics()
        print(f"   运行时长: {stats['duration']:.2f}秒")
        print(f"   处理帧数: {stats['frames_processed']}")
        print(f"   节点状态: {stats['node_status']}")
        
        # 12. 显示事件统计
        print(f"\n12. 事件统计:")
        print(f"   收到事件数: {len(events_received)}")
        
        print("\n" + "=" * 60)
        print("测试完成 ✓")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_plugin_system():
    """测试插件系统"""
    
    print("\n" + "=" * 60)
    print("插件系统测试")
    print("=" * 60)
    
    try:
        # 创建插件管理器
        print("\n1. 创建插件管理器...")
        plugin_dirs = [str(Path(__file__).parent / "plugins")]
        plugin_manager = PluginManager(plugin_dirs)
        
        # 发现插件
        print("2. 发现插件...")
        count = plugin_manager.discover_plugins()
        print(f"   发现 {count} 个插件")
        
        # 列出插件
        print("\n3. 插件列表:")
        for plugin in plugin_manager.list_plugins():
            print(f"   - {plugin['type']}")
            print(f"     名称: {plugin.get('name', 'Unknown')}")
            print(f"     版本: {plugin.get('version', 'Unknown')}")
            print(f"     类别: {plugin.get('category', 'Unknown')}")
        
        # 生成依赖报告
        print("\n4. 依赖报告:")
        report = plugin_manager.generate_dependency_report()
        print(f"   总插件数: {report['total_plugins']}")
        print(f"   所有依赖: {report['all_dependencies']}")
        
        if report['missing_dependencies']:
            print(f"   缺失依赖: {report['missing_dependencies']}")
        else:
            print("   所有依赖满足 ✓")
        
        # 测试插件实例化
        print("\n5. 测试插件实例化...")
        test_node = plugin_manager.create_plugin_instance(
            plugin_type='test_producer',
            node_id='test_001',
            config={'interval': 1.0}
        )
        print(f"   创建实例: {test_node}")
        print(f"   元数据: {test_node.get_metadata()}")
        
        print("\n" + "=" * 60)
        print("插件系统测试完成 ✓")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    
    # 测试插件系统
    result1 = await test_plugin_system()
    
    # 测试基本系统
    result2 = await test_basic_system()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"插件系统测试: {'✓ 通过' if result1 else '✗ 失败'}")
    print(f"基本系统测试: {'✓ 通过' if result2 else '✗ 失败'}")
    print("=" * 60)
    
    return result1 and result2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
