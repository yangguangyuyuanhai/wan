"""
集成测试 - 插件系统测试
测试所有插件的加载、配置和执行
"""
import pytest
import asyncio
import numpy as np
from service_DAG.core.plugin_manager import PluginManager
from service_DAG.engine.node import ExecutionContext
from service_DAG.core.event_bus import EventBus


class TestPluginIntegration:
    """插件系统集成测试"""
    
    def test_plugin_discovery(self):
        """测试插件发现"""
        manager = PluginManager()
        manager.discover_plugins("service_DAG/plugins")
        
        plugins = manager.get_available_plugins()
        
        # 验证核心插件已发现
        assert "camera_hik" in plugins or "test_node" in plugins
        assert len(plugins) > 0
    
    @pytest.mark.asyncio
    async def test_plugin_execution(self):
        """测试插件执行"""
        manager = PluginManager()
        manager.discover_plugins("service_DAG/plugins")
        
        # 尝试创建测试节点
        if "test_node" in manager.get_available_plugins():
            node = manager.create_plugin_instance("test_node", "test1", {})
            
            # 执行节点
            context = ExecutionContext(
                node_id="test1",
                inputs={"input": "test_data"},
                global_context=None,
                event_bus=EventBus()
            )
            
            result = await node.run(context)
            assert result.success
    
    def test_plugin_metadata(self):
        """测试插件元数据"""
        manager = PluginManager()
        manager.discover_plugins("service_DAG/plugins")
        
        for plugin_type in manager.get_available_plugins():
            metadata = manager.get_plugin_metadata(plugin_type)
            
            # 验证元数据完整性
            assert "type" in metadata
            assert "name" in metadata
            assert "version" in metadata
    
    @pytest.mark.asyncio
    async def test_plugin_error_handling(self):
        """测试插件错误处理"""
        manager = PluginManager()
        
        # 尝试创建不存在的插件
        with pytest.raises(ValueError):
            manager.create_plugin_instance("nonexistent", "test", {})
