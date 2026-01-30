# -*- coding: utf-8 -*-
"""
DAG 系统主入口 (Main Entry Point)
初始化微内核、加载插件、启动 DAG 执行引擎

响应需求：需求 9（系统生命周期管理）
响应任务：任务 8 - 创建系统启动入口
"""

import asyncio
import signal
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.context import Context
from core.event_bus import get_event_bus
from core.plugin_manager import PluginManager
from engine.graph import GraphDefinition, Graph
from engine.streaming_executor import StreamingExecutor
from logger_config import get_logger


# ==================== 全局变量 ====================

logger = get_logger("MainDAG")
executor: Optional[StreamingExecutor] = None
shutdown_event = asyncio.Event()


# ==================== 信号处理 ====================

def signal_handler(signum, frame):
    """
    信号处理器（Ctrl+C）
    
    Args:
        signum: 信号编号
        frame: 栈帧
    """
    logger.info("收到停止信号，正在优雅关闭...")
    shutdown_event.set()


# ==================== 主函数 ====================

async def main(config_path: str, log_level: str = "INFO", debug: bool = False, dry_run: bool = False):
    """
    主函数
    
    Args:
        config_path: 配置文件路径
        log_level: 日志级别
        debug: 是否启用调试模式
        dry_run: 是否仅验证配置不执行
    """
    global executor
    
    try:
        # ==================== 1. 初始化全局上下文 ====================
        logger.info("=" * 60)
        logger.info("DAG 系统启动")
        logger.info("=" * 60)
        
        logger.info("1. 初始化全局上下文...")
        context = Context(
            config={
                'error_strategy': 'circuit-break',  # circuit-break, skip, retry, restart
                'max_retries': 3,
                'queue_size': 10,
                'log_level': log_level,
                'debug': debug
            }
        )
        
        # ==================== 2. 初始化事件总线 ====================
        logger.info("2. 初始化事件总线...")
        event_bus = get_event_bus()
        context.event_bus = event_bus
        
        # 订阅系统事件（用于日志）
        def log_event(event):
            if debug:
                logger.debug(f"[Event] {event.topic}: {event.data}")
        
        event_bus.subscribe("*", log_event)
        
        # 发布启动事件
        event_bus.publish('sys.startup', {
            'config_path': config_path,
            'log_level': log_level,
            'debug': debug
        })
        
        # ==================== 3. 创建插件管理器并发现插件 ====================
        logger.info("3. 创建插件管理器...")
        plugin_dirs = [
            str(Path(__file__).parent / "plugins")
        ]
        
        plugin_manager = PluginManager(plugin_dirs, logger=logger)
        plugin_count = plugin_manager.discover_plugins()
        
        logger.info(f"   发现 {plugin_count} 个插件")
        
        # 显示插件列表
        if debug:
            for plugin in plugin_manager.list_plugins():
                logger.debug(f"   - {plugin['type']}: {plugin.get('name', 'Unknown')}")
        
        # 生成依赖报告
        dep_report = plugin_manager.generate_dependency_report()
        if dep_report['missing_dependencies']:
            logger.warning(f"   部分插件缺少依赖: {dep_report['missing_dependencies']}")
        
        # ==================== 4. 加载图定义 ====================
        logger.info(f"4. 加载图定义: {config_path}")
        
        if not Path(config_path).exists():
            logger.error(f"   配置文件不存在: {config_path}")
            return
        
        graph_def = GraphDefinition.load_from_file(config_path)
        logger.info(f"   图名称: {graph_def.name}")
        logger.info(f"   节点数: {len(graph_def.nodes)}")
        logger.info(f"   连接数: {len(graph_def.connections)}")
        
        # ==================== 5. 创建图对象并实例化节点 ====================
        logger.info("5. 创建图对象...")
        graph = Graph(graph_def)
        
        logger.info("6. 实例化节点...")
        for node_def in graph_def.nodes:
            if not node_def.enabled:
                logger.info(f"   跳过禁用节点: {node_def.id}")
                continue
            
            try:
                # 创建插件实例
                node_instance = plugin_manager.create_plugin_instance(
                    plugin_type=node_def.type,
                    node_id=node_def.id,
                    config=node_def.config
                )
                
                # 添加到图
                graph.add_node(node_def.id, node_instance)
                
                logger.info(f"   创建节点: {node_def.id} ({node_def.type})")
                
            except Exception as e:
                logger.error(f"   创建节点失败: {node_def.id} - {e}")
                if not dry_run:
                    return
        
        # ==================== 7. 验证图 ====================
        logger.info("7. 验证图...")
        try:
            graph.validate()
            logger.info("   图验证通过")
            
            # 显示拓扑排序
            order = graph.topological_sort()
            logger.info(f"   执行顺序: {' -> '.join(order)}")
            
        except Exception as e:
            logger.error(f"   图验证失败: {e}")
            return
        
        # ==================== 8. Dry Run 模式 ====================
        if dry_run:
            logger.info("=" * 60)
            logger.info("Dry Run 模式：配置验证完成，不执行图")
            logger.info("=" * 60)
            return
        
        # ==================== 9. 创建流式执行器 ====================
        logger.info("8. 创建流式执行器...")
        executor = StreamingExecutor(
            graph=graph,
            global_context=context,
            queue_size=context.get_config('queue_size', 10)
        )
        
        # ==================== 10. 启动图执行 ====================
        logger.info("9. 启动图执行...")
        await executor.start()
        
        logger.info("=" * 60)
        logger.info("系统运行中... (按 Ctrl+C 停止)")
        logger.info("=" * 60)
        
        # ==================== 11. 等待停止信号 ====================
        await shutdown_event.wait()
        
        # ==================== 12. 停止执行器 ====================
        logger.info("10. 停止执行器...")
        await executor.stop()
        
        # ==================== 13. 发布关闭事件 ====================
        event_bus.publish('sys.shutdown', {
            'reason': 'user_requested'
        })
        
        logger.info("=" * 60)
        logger.info("系统已关闭")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception(f"系统异常: {e}")
        
        # 尝试停止执行器
        if executor:
            try:
                await executor.stop()
            except:
                pass


# ==================== 命令行入口 ====================

def cli():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="DAG 工业视觉系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main_dag.py --config config/pipeline.json
  python main_dag.py --config config/pipeline.json --debug
  python main_dag.py --config config/pipeline.json --dry-run
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/pipeline.json',
        help='配置文件路径 (默认: config/pipeline.json)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅验证配置，不执行图'
    )
    
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行主函数
    try:
        asyncio.run(main(
            config_path=args.config,
            log_level=args.log_level,
            debug=args.debug,
            dry_run=args.dry_run
        ))
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
    except Exception as e:
        logger.exception(f"程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
