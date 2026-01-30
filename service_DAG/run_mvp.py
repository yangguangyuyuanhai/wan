# -*- coding: utf-8 -*-
"""
MVP测试脚本
运行最小闭环：Camera -> Display
"""

import asyncio
import signal
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.context import GlobalContext
from core.event_bus import EventBus
from core.plugin_manager import PluginManager
from engine.graph import Graph, parse_graph_definition
from engine.streaming_executor import StreamingExecutor
from logger_config import get_logger

logger = get_logger("MVP")

# 全局变量
executor = None
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info("接收到停止信号")
    shutdown_event.set()


async def main():
    """主函数"""
    global executor
    
    try:
        logger.info("=" * 60)
        logger.info("MVP测试启动 - Camera -> Display")
        logger.info("=" * 60)
        
        # 1. 初始化全局上下文
        logger.info("初始化全局上下文...")
        context = GlobalContext()
        context.config = {
            'error_strategy': 'circuit-break',
            'max_retries': 3,
            'queue_size': 10
        }
        
        # 2. 初始化事件总线
        logger.info("初始化事件总线...")
        event_bus = EventBus()
        context.event_bus = event_bus
        
        # 订阅关键事件
        def on_node_error(event):
            logger.error(f"节点错误: {event.data}")
        
        def on_node_complete(event):
            logger.debug(f"节点完成: {event.data.get('node_id')}")
        
        event_bus.subscribe('node.error', on_node_error)
        event_bus.subscribe('node.complete', on_node_complete)
        
        # 3. 初始化插件管理器
        logger.info("初始化插件管理器...")
        plugin_dirs = [
            str(Path(__file__).parent / 'plugins' / 'basic'),
            str(Path(__file__).parent / 'plugins' / 'algo'),
            str(Path(__file__).parent / 'plugins' / 'ui')
        ]
        
        plugin_manager = PluginManager(plugin_dirs)
        plugin_count = plugin_manager.discover_plugins()
        logger.info(f"发现 {plugin_count} 个插件")
        
        # 列出所有插件
        for plugin in plugin_manager.list_plugins():
            logger.info(f"  - {plugin['type']}: {plugin['name']} v{plugin['version']}")
        
        # 4. 加载图定义
        logger.info("加载图定义...")
        config_path = Path(__file__).parent / 'config' / 'mvp_pipeline.json'
        graph_def = parse_graph_definition(str(config_path))
        logger.info(f"图名称: {graph_def.name}")
        logger.info(f"节点数量: {len(graph_def.nodes)}")
        logger.info(f"连接数量: {len(graph_def.connections)}")
        
        # 5. 创建图对象
        logger.info("创建图对象...")
        graph = Graph(graph_def)
        
        # 实例化所有节点
        for node_def in graph_def.nodes:
            if not node_def.enabled:
                logger.info(f"跳过禁用节点: {node_def.id}")
                continue
            
            plugin_class = plugin_manager.get_plugin(node_def.type)
            if plugin_class is None:
                logger.error(f"未找到插件类型: {node_def.type}")
                continue
            
            node = plugin_class(node_def.id, node_def.config)
            graph.add_node(node_def.id, node)
            logger.info(f"实例化节点: {node_def.id} ({node_def.type})")
        
        # 构建邻接表
        for conn in graph_def.connections:
            if conn.from_node not in graph.adjacency:
                graph.adjacency[conn.from_node] = []
            graph.adjacency[conn.from_node].append(conn.to_node)
        
        # 6. 验证图
        logger.info("验证图...")
        if graph.validate():
            logger.info("图验证通过")
        else:
            logger.error("图验证失败")
            return
        
        # 7. 创建执行器
        logger.info("创建流式执行器...")
        executor = StreamingExecutor(graph, context)
        
        # 8. 启动执行器
        logger.info("启动执行器...")
        await executor.start()
        
        logger.info("=" * 60)
        logger.info("MVP测试运行中...")
        logger.info("按 Ctrl+C 停止")
        logger.info("=" * 60)
        
        # 等待停止信号
        await shutdown_event.wait()
        
    except KeyboardInterrupt:
        logger.info("接收到键盘中断")
    except Exception as e:
        logger.exception(f"运行异常: {e}")
    finally:
        # 停止执行器
        if executor:
            logger.info("停止执行器...")
            await executor.stop()
        
        logger.info("=" * 60)
        logger.info("MVP测试结束")
        logger.info("=" * 60)


if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行主函数
    asyncio.run(main())
