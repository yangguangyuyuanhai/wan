# -*- coding: utf-8 -*-
"""
图管理器单元测试

响应任务：任务 19.2 - 引擎模块测试
"""

import pytest
from engine.graph import Graph, GraphDefinition, NodeDefinition, Connection
from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult
from engine.port import InputPort, OutputPort
from core.data_types import ImageType
from core.plugin_manager import PluginManager


class MockNode(INode):
    """测试用的模拟节点"""
    
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self._input_ports = [InputPort("input", ImageType, required=True)]
        self._output_ports = [OutputPort("output", ImageType)]
    
    def get_metadata(self) -> NodeMetadata:
        return NodeMetadata(
            name="MockNode",
            version="1.0.0",
            author="Test",
            description="Test node",
            category="test"
        )
    
    def get_ports(self):
        return self._input_ports, self._output_ports
    
    def validate_config(self) -> bool:
        return True
    
    async def initialize(self) -> bool:
        return True
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        return NodeResult(success=True, outputs={"output": "test"})
    
    async def cleanup(self) -> None:
        pass
    
    def input_data_processed_hook(self, input_name: str) -> None:
        pass


class TestGraphDefinition:
    """GraphDefinition测试"""
    
    def test_create_graph_definition(self):
        """测试创建图定义"""
        graph_def = GraphDefinition(
            name="test_graph",
            version="1.0.0",
            description="Test graph",
            nodes=[],
            connections=[]
        )
        
        assert graph_def.name == "test_graph"
        assert graph_def.version == "1.0.0"
        assert len(graph_def.nodes) == 0
        assert len(graph_def.connections) == 0


class TestNodeDefinition:
    """NodeDefinition测试"""
    
    def test_create_node_definition(self):
        """测试创建节点定义"""
        node_def = NodeDefinition(
            id="node1",
            type="test_node",
            config={"param": "value"}
        )
        
        assert node_def.id == "node1"
        assert node_def.type == "test_node"
        assert node_def.config["param"] == "value"


class TestConnection:
    """Connection测试"""
    
    def test_create_connection(self):
        """测试创建连接"""
        conn = Connection(
            from_node="node1",
            from_port="output",
            to_node="node2",
            to_port="input"
        )
        
        assert conn.from_node == "node1"
        assert conn.from_port == "output"
        assert conn.to_node == "node2"
        assert conn.to_port == "input"


class TestGraph:
    """Graph测试"""
    
    def test_create_empty_graph(self):
        """测试创建空图"""
        graph_def = GraphDefinition(
            name="empty_graph",
            version="1.0.0",
            nodes=[],
            connections=[]
        )
        
        plugin_manager = PluginManager([])
        graph = Graph(graph_def, plugin_manager)
        
        assert graph.definition.name == "empty_graph"
        assert len(graph.list_nodes()) == 0
    
    def test_add_node(self):
        """测试添加节点"""
        graph_def = GraphDefinition(
            name="test_graph",
            version="1.0.0",
            nodes=[],
            connections=[]
        )
        
        plugin_manager = PluginManager([])
        graph = Graph(graph_def, plugin_manager)
        
        node = MockNode("node1", {})
        graph.nodes["node1"] = node
        
        assert "node1" in graph.list_nodes()
        assert graph.get_node("node1") == node
    
    def test_add_connection(self):
        """测试添加连接"""
        graph_def = GraphDefinition(
            name="test_graph",
            version="1.0.0",
            nodes=[],
            connections=[
                Connection("node1", "output", "node2", "input")
            ]
        )
        
        plugin_manager = PluginManager([])
        graph = Graph(graph_def, plugin_manager)
        
        assert len(graph.definition.connections) == 1
    
    def test_get_source_nodes(self):
        """测试获取源节点"""
        # 创建简单的图：node1 -> node2
        graph_def = GraphDefinition(
            name="test_graph",
            version="1.0.0",
            nodes=[
                NodeDefinition("node1", "mock", {}),
                NodeDefinition("node2", "mock", {})
            ],
            connections=[
                Connection("node1", "output", "node2", "input")
            ]
        )
        
        plugin_manager = PluginManager([])
        graph = Graph(graph_def, plugin_manager)
        
        # node1应该是源节点（无输入）
        sources = graph.get_source_nodes()
        assert "node1" in sources
        assert "node2" not in sources


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
