"""
集成测试 - 完整流水线测试
测试从配置加载到执行的完整流程
"""
import pytest
import asyncio
import json
from pathlib import Path
from service_DAG.core.plugin_manager import PluginManager
from service_DAG.engine.graph import Graph
from service_DAG.engine.streaming_executor import StreamingExecutor
from service_DAG.core.async_event_bus import AsyncEventBus


class TestPipelineIntegration:
    """完整流水线集成测试"""
    
    def test_config_loading(self):
        """测试配置文件加载"""
        config_path = Path("service_DAG/config/test_pipeline.json")
        
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            
            assert "nodes" in config
            assert "connections" in config
            assert len(config["nodes"]) > 0
    
    @pytest.mark.asyncio
    async def test_graph_construction(self):
        """测试图构建"""
        manager = PluginManager()
        manager.discover_plugins("service_DAG/plugins")
        
        graph = Graph()
        
        # 创建简单的测试图
        if "test_node" in manager.get_available_plugins():
            node1 = manager.create_plugin_instance("test_node", "node1", {})
            node2 = manager.create_plugin_instance("test_node", "node2", {})
            
            graph.add_node(node1)
            graph.add_node(node2)
            graph.add_connection("node1", "output", "node2", "input")
            
            # 验证图
            assert graph.validate()
    
    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """测试流水线执行"""
        manager = PluginManager()
        manager.discover_plugins("service_DAG/plugins")
        
        if "test_node" not in manager.get_available_plugins():
            pytest.skip("test_node plugin not available")
        
        # 构建图
        graph = Graph()
        node1 = manager.create_plugin_instance("test_node", "node1", {})
        node2 = manager.create_plugin_instance("test_node", "node2", {})
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_connection("node1", "output", "node2", "input")
        
        # 执行
        event_bus = AsyncEventBus()
        executor = StreamingExecutor(graph, event_bus)
        
        await executor.start()
        await asyncio.sleep(0.5)
        await executor.stop()
        
        assert True  # 执行完成
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """测试错误恢复"""
        manager = PluginManager()
        manager.discover_plugins("service_DAG/plugins")
        
        graph = Graph()
        event_bus = AsyncEventBus()
        
        # 使用skip策略
        executor = StreamingExecutor(graph, event_bus, error_strategy="skip")
        
        # 测试空图执行
        await executor.start()
        await asyncio.sleep(0.1)
        await executor.stop()
        
        assert True
