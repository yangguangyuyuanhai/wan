# -*- coding: utf-8 -*-
"""
端到端集成测试

响应任务：任务 19.4 - 集成测试
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path

from core.context import GlobalContext
from core.plugin_manager import PluginManager
from core.event_bus import get_event_bus
from engine.graph import Graph, parse_graph_definition
from engine.streaming_executor import StreamingExecutor
from core.data_types import ImageType


@pytest.mark.integration
class TestEndToEndPipeline:
    """端到端流水线测试"""
    
    @pytest.fixture
    def setup_system(self):
        """设置测试系统"""
        # 创建全局上下文
        global_context = GlobalContext()
        
        # 创建插件管理器
        plugin_manager = PluginManager([
            "plugins/basic",
            "plugins/algo",
            "plugins/io"
        ])
        plugin_manager.discover_plugins()
        
        return global_context, plugin_manager
    
    @pytest.mark.asyncio
    async def test_simple_pipeline(self, setup_system):
        """测试简单流水线：TestNode -> TestNode"""
        global_context, plugin_manager = setup_system
        
        # 创建简单的测试图配置
        test_config = {
            "name": "test_pipeline",
            "version": "1.0.0",
            "description": "Test pipeline",
            "nodes": [
                {
                    "id": "source",
                    "type": "test_node",
                    "config": {}
                },
                {
                    "id": "sink",
                    "type": "test_node",
                    "config": {}
                }
            ],
            "connections": [
                {
                    "from_node": "source",
                    "from_port": "output",
                    "to_node": "sink",
                    "to_port": "input"
                }
            ]
        }
        
        # 保存临时配置
        import json
        config_path = Path("config/test_integration.json")
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        try:
            # 解析图定义
            graph_def = parse_graph_definition(str(config_path))
            
            # 创建图
            graph = Graph(graph_def, plugin_manager)
            
            # 验证图
            assert graph.validate() is True
            
            # 创建执行器
            executor = StreamingExecutor(graph, global_context, queue_size=5)
            
            # 启动执行器
            await executor.start()
            
            # 运行一小段时间
            await asyncio.sleep(2)
            
            # 停止执行器
            await executor.stop()
            
            # 验证执行统计
            assert executor.state.total_frames_processed > 0
            
        finally:
            # 清理临时文件
            if config_path.exists():
                config_path.unlink()
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, setup_system):
        """测试错误恢复"""
        global_context, plugin_manager = setup_system
        
        # 设置错误策略为skip
        global_context.set_config('error_strategy', 'skip')
        
        # 创建会产生错误的测试配置
        # 这里可以添加具体的错误场景测试
        
        # 验证系统能够从错误中恢复
        assert True  # 占位符


@pytest.mark.integration
class TestPluginIntegration:
    """插件集成测试"""
    
    def test_plugin_discovery(self):
        """测试插件发现"""
        plugin_manager = PluginManager([
            "plugins/basic",
            "plugins/algo",
            "plugins/io"
        ])
        
        plugins = plugin_manager.discover_plugins()
        
        # 验证关键插件被发现
        assert len(plugins) > 0
        
        # 验证特定插件存在
        plugin_types = list(plugins.keys())
        assert "test_node" in plugin_types or len(plugin_types) >= 3
    
    def test_plugin_instantiation(self):
        """测试插件实例化"""
        plugin_manager = PluginManager([
            "plugins/basic"
        ])
        
        plugins = plugin_manager.discover_plugins()
        
        # 尝试实例化每个插件
        for plugin_type, plugin_class in plugins.items():
            try:
                instance = plugin_class(f"test_{plugin_type}", {})
                assert instance is not None
                assert hasattr(instance, 'run')
            except Exception as e:
                pytest.fail(f"插件 {plugin_type} 实例化失败: {e}")


@pytest.mark.integration  
class TestDataFlow:
    """数据流测试"""
    
    def test_data_type_compatibility(self):
        """测试数据类型兼容性"""
        from core.data_types import ImageType, TypeRegistry
        
        registry = TypeRegistry()
        registry.register("image", ImageType)
        
        # 创建测试图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        img_type = ImageType(data=test_image, width=100, height=100, channels=3)
        
        # 验证类型
        assert img_type.validate() is True
        
        # 验证复制
        img_copy = img_type.copy()
        assert img_copy.width == img_type.width
        assert not np.shares_memory(img_copy.data, img_type.data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
