"""
单元测试 - 插件管理器
测试插件发现、加载和管理功能
"""
import pytest
from pathlib import Path
from service_DAG.core.plugin_manager import PluginManager
from service_DAG.engine.node import INode, NodeResult, ExecutionContext


class MockPlugin(INode):
    """模拟插件用于测试"""
    __plugin_metadata__ = {
        "type": "mock_plugin",
        "name": "Mock Plugin",
        "version": "1.0.0",
        "description": "Test plugin"
    }
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        return NodeResult(success=True, outputs={"result": "mock"})


class TestPluginManager:
    """插件管理器测试"""
    
    def test_register_plugin(self):
        """测试注册插件"""
        manager = PluginManager()
        manager.register_plugin(MockPlugin)
        
        assert "mock_plugin" in manager.get_available_plugins()
    
    def test_get_plugin_class(self):
        """测试获取插件类"""
        manager = PluginManager()
        manager.register_plugin(MockPlugin)
        
        plugin_class = manager.get_plugin_class("mock_plugin")
        assert plugin_class == MockPlugin
    
    def test_create_plugin_instance(self):
        """测试创建插件实例"""
        manager = PluginManager()
        manager.register_plugin(MockPlugin)
        
        instance = manager.create_plugin_instance("mock_plugin", "test_id", {})
        assert isinstance(instance, MockPlugin)
        assert instance.node_id == "test_id"
    
    def test_get_plugin_metadata(self):
        """测试获取插件元数据"""
        manager = PluginManager()
        manager.register_plugin(MockPlugin)
        
        metadata = manager.get_plugin_metadata("mock_plugin")
        assert metadata["name"] == "Mock Plugin"
        assert metadata["version"] == "1.0.0"
    
    def test_duplicate_registration(self):
        """测试重复注册插件"""
        manager = PluginManager()
        manager.register_plugin(MockPlugin)
        
        # 重复注册应该覆盖
        manager.register_plugin(MockPlugin)
        assert len([p for p in manager.get_available_plugins() if p == "mock_plugin"]) == 1
    
    def test_plugin_not_found(self):
        """测试获取不存在的插件"""
        manager = PluginManager()
        
        with pytest.raises(ValueError):
            manager.get_plugin_class("nonexistent")
    
    def test_discover_plugins(self):
        """测试插件发现"""
        manager = PluginManager()
        plugins_dir = Path(__file__).parent.parent.parent / "plugins"
        
        if plugins_dir.exists():
            manager.discover_plugins(str(plugins_dir))
            plugins = manager.get_available_plugins()
            
            # 应该发现一些插件
            assert len(plugins) > 0
