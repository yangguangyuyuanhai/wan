#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAG系统主入口
整合所有组件，提供统一的启动接口

优化版本 - 2026-01-30
"""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.context import GlobalContext
from core.event_bus import get_event_bus
from core.plugin_manager import PluginManager
from core.metrics import get_metrics_collector
from core.logger_subscriber import get_logger_subscriber
from engine.graph import Graph, parse_graph_definition
from engine.streaming_executor import StreamingExecutor


class DAGSystem:
    """DAG系统主类"""
    
    def __init__(self, config_path: str = "./config/pipeline.json"):
        """初始化系统"""
        self.config_path = config_path
        self.global_context = GlobalContext()
        self.event_bus = get_event_bus()
        self.plugin_manager: Optional[PluginManager] = None
        self.graph: Optional[Graph] = None
        self.executor: Optional[StreamingExecutor] = None
        
        # 监控组件
        self.metrics_collector = get_metrics_collector()
        self.logger_subscriber = get_logger_subscriber()
        
        # 运行状态
        self.running = False
        
    async def initialize(self):
        """初始化系统组件"""
        print("初始化DAG系统...")
        
        # 1. 启动监控
        await self.metrics_collector.start()
        self.logger_subscriber.start()
        
        # 2. 初始化插件管理器
        self.plugin_manager = PluginManager([
            "plugins/basic",
            "plugins/algo",
            "plugins/io"
        ])
        plugins = self.plugin_manager.discover_plugins()
        print(f"发现 {len(plugins)} 个插件")
        
        # 3. 加载图定义
        graph_def = parse_graph_definition(self.config_path)
        self.graph = Graph(graph_def, self.plugin_manager)
        
        # 4. 验证图
        if not self.graph.validate():
            raise RuntimeError("图验证失败")
        
        print(f"图验证成功: {len(self.graph.list_nodes())} 个节点")
        
        # 5. 创建执行器
        self.executor = StreamingExecutor(
            self.graph,
            self.global_context,
            queue_size=10
        )
        
        print("系统初始化完成")
    
    async def start(self):
        """启动系统"""
        if self.running:
            return
        
        print("启动DAG系统...")
        self.running = True
        
        # 启动执行器
        await self.executor.start()
        
        print("系统运行中，按Ctrl+C停止")
    
    async def stop(self):
        """停止系统"""
        if not self.running:
            return
        
        print("\n停止DAG系统...")
        self.running = False
        
        # 停止执行器
        if self.executor:
            await self.executor.stop()
        
        # 停止监控
        await self.metrics_collector.stop()
        self.logger_subscriber.stop()
        
        print("系统已停止")
    
    async def run(self):
        """运行系统主循环"""
        await self.initialize()
        await self.start()
        
        try:
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n收到中断信号")
        finally:
            await self.stop()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DAG系统")
    parser.add_argument("--config", default="./config/pipeline.json", help="配置文件路径")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 创建系统
    system = DAGSystem(config_path=args.config)
    
    # 运行系统
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())
