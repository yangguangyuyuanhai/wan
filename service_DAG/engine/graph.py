# -*- coding: utf-8 -*-
"""
图管理器 (Graph Manager)
实现 DAG 图的定义、解析、验证和拓扑排序

响应需求：需求 3（DAG引擎）
响应任务：任务 3 - 实现图管理器
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import json
from pathlib import Path

from .node import INode
from .port import Port, PortDirection
from core.exceptions import GraphValidationError, CycleDetectedError


# ==================== 图定义数据类 ====================

@dataclass
class NodeDefinition:
    """
    节点定义
    描述图中的一个节点
    """
    id: str                          # 节点唯一标识
    type: str                        # 节点类型（对应插件类型）
    config: Dict = field(default_factory=dict)  # 节点配置
    position: Tuple[int, int] = (0, 0)  # 位置（用于可视化编辑器）
    enabled: bool = True             # 是否启用
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'config': self.config,
            'position': list(self.position),
            'enabled': self.enabled
        }


@dataclass
class Connection:
    """
    连接定义
    描述两个节点端口之间的连接
    """
    from_node: str                   # 源节点ID
    from_port: str                   # 源端口名称
    to_node: str                     # 目标节点ID
    to_port: str                     # 目标端口名称
    enabled: bool = True             # 是否启用
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'from': f"{self.from_node}.{self.from_port}",
            'to': f"{self.to_node}.{self.to_port}",
            'enabled': self.enabled
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Connection':
        """从字典创建连接"""
        from_parts = data['from'].split('.')
        to_parts = data['to'].split('.')
        
        return Connection(
            from_node=from_parts[0],
            from_port=from_parts[1],
            to_node=to_parts[0],
            to_port=to_parts[1],
            enabled=data.get('enabled', True)
        )


@dataclass
class GraphDefinition:
    """
    图定义
    描述完整的 DAG 图结构
    """
    name: str                        # 图名称
    version: str                     # 版本号
    nodes: List[NodeDefinition] = field(default_factory=list)  # 节点列表
    connections: List[Connection] = field(default_factory=list)  # 连接列表
    metadata: Dict = field(default_factory=dict)  # 额外元数据
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'version': self.version,
            'nodes': [n.to_dict() for n in self.nodes],
            'connections': [c.to_dict() for c in self.connections],
            'metadata': self.metadata
        }
    
    def save_to_file(self, file_path: str):
        """保存到 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_from_file(file_path: str) -> 'GraphDefinition':
        """从 JSON 文件加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return GraphDefinition(
            name=data.get('name', 'Unnamed'),
            version=data.get('version', '1.0.0'),
            nodes=[
                NodeDefinition(
                    id=n['id'],
                    type=n['type'],
                    config=n.get('config', {}),
                    position=tuple(n.get('position', [0, 0])),
                    enabled=n.get('enabled', True)
                )
                for n in data.get('nodes', [])
            ],
            connections=[
                Connection.from_dict(c)
                for c in data.get('connections', [])
            ],
            metadata=data.get('metadata', {})
        )


# ==================== 图类 ====================

class Graph:
    """
    DAG 图
    管理节点和连接，提供验证和拓扑排序功能
    """
    
    def __init__(self, definition: GraphDefinition):
        """
        初始化图
        
        Args:
            definition: 图定义
        """
        self.definition = definition
        self.nodes: Dict[str, INode] = {}  # node_id -> node_instance
        self.adjacency: Dict[str, List[str]] = {}  # node_id -> [downstream_node_ids]
        self.reverse_adjacency: Dict[str, List[str]] = {}  # node_id -> [upstream_node_ids]
        self.connections: List[Connection] = definition.connections
        
        # 初始化邻接表
        for node_def in definition.nodes:
            self.adjacency[node_def.id] = []
            self.reverse_adjacency[node_def.id] = []
        
        # 构建邻接表
        for conn in self.connections:
            if conn.enabled:
                self.adjacency[conn.from_node].append(conn.to_node)
                self.reverse_adjacency[conn.to_node].append(conn.from_node)
    
    # ==================== 节点管理 ====================
    
    def add_node(self, node_id: str, node: INode):
        """
        添加节点实例
        
        Args:
            node_id: 节点ID
            node: 节点实例
        """
        self.nodes[node_id] = node
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []
            self.reverse_adjacency[node_id] = []
    
    def get_node(self, node_id: str) -> Optional[INode]:
        """
        获取节点实例
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点实例，如果不存在返回 None
        """
        return self.nodes.get(node_id)
    
    def remove_node(self, node_id: str):
        """
        移除节点
        
        Args:
            node_id: 节点ID
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
        if node_id in self.adjacency:
            del self.adjacency[node_id]
        if node_id in self.reverse_adjacency:
            del self.reverse_adjacency[node_id]
    
    def list_nodes(self) -> List[str]:
        """
        列出所有节点ID
        
        Returns:
            节点ID列表
        """
        return list(self.nodes.keys())
    
    # ==================== 连接管理 ====================
    
    def add_connection(self, connection: Connection):
        """
        添加连接
        
        Args:
            connection: 连接定义
        """
        self.connections.append(connection)
        if connection.enabled:
            self.adjacency[connection.from_node].append(connection.to_node)
            self.reverse_adjacency[connection.to_node].append(connection.from_node)
    
    def get_connections_from(self, node_id: str) -> List[Connection]:
        """
        获取从指定节点出发的所有连接
        
        Args:
            node_id: 节点ID
            
        Returns:
            连接列表
        """
        return [c for c in self.connections if c.from_node == node_id and c.enabled]
    
    def get_connections_to(self, node_id: str) -> List[Connection]:
        """
        获取到达指定节点的所有连接
        
        Args:
            node_id: 节点ID
            
        Returns:
            连接列表
        """
        return [c for c in self.connections if c.to_node == node_id and c.enabled]
    
    # ==================== 图查询 ====================
    
    def get_source_nodes(self) -> List[str]:
        """
        获取源节点（无输入的节点）
        
        Returns:
            源节点ID列表
        """
        return [
            node_id for node_id in self.nodes.keys()
            if len(self.reverse_adjacency.get(node_id, [])) == 0
        ]
    
    def get_sink_nodes(self) -> List[str]:
        """
        获取终端节点（无输出的节点）
        
        Returns:
            终端节点ID列表
        """
        return [
            node_id for node_id in self.nodes.keys()
            if len(self.adjacency.get(node_id, [])) == 0
        ]
    
    def get_downstream_nodes(self, node_id: str) -> List[str]:
        """
        获取下游节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            下游节点ID列表
        """
        return self.adjacency.get(node_id, [])
    
    def get_upstream_nodes(self, node_id: str) -> List[str]:
        """
        获取上游节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            上游节点ID列表
        """
        return self.reverse_adjacency.get(node_id, [])
    
    # ==================== 图验证 ====================
    
    def validate(self) -> bool:
        """
        验证图的有效性
        
        Returns:
            是否有效
            
        Raises:
            GraphValidationError: 验证失败
        """
        # 1. 检查循环
        if self._has_cycle():
            raise CycleDetectedError("图中存在循环")
        
        # 2. 检查节点定义存在
        self._validate_node_definitions()
        
        # 3. 检查端口连接
        self._validate_connections()
        
        # 4. 检查必需输入
        self._validate_required_inputs()
        
        return True
    
    def _has_cycle(self) -> bool:
        """
        检测循环（DFS 算法）
        
        Returns:
            是否存在循环
        """
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in self.adjacency.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def _validate_node_definitions(self):
        """验证节点定义存在"""
        for node_def in self.definition.nodes:
            if node_def.id not in self.nodes:
                raise GraphValidationError(f"节点实例不存在: {node_def.id}")
    
    def _validate_connections(self):
        """验证连接的有效性"""
        for conn in self.connections:
            if not conn.enabled:
                continue
            
            # 检查节点存在
            if conn.from_node not in self.nodes:
                raise GraphValidationError(f"源节点不存在: {conn.from_node}")
            if conn.to_node not in self.nodes:
                raise GraphValidationError(f"目标节点不存在: {conn.to_node}")
            
            # 检查端口存在和兼容性
            from_node = self.nodes[conn.from_node]
            to_node = self.nodes[conn.to_node]
            
            _, from_outputs = from_node.get_ports()
            to_inputs, _ = to_node.get_ports()
            
            from_port = next((p for p in from_outputs if p.name == conn.from_port), None)
            to_port = next((p for p in to_inputs if p.name == conn.to_port), None)
            
            if not from_port:
                raise GraphValidationError(
                    f"输出端口不存在: {conn.from_node}.{conn.from_port}"
                )
            if not to_port:
                raise GraphValidationError(
                    f"输入端口不存在: {conn.to_node}.{conn.to_port}"
                )
            
            # 检查端口类型兼容性
            # 注意：这里需要根据实际的 Port 类实现来检查兼容性
            # 暂时跳过详细的类型检查
    
    def _validate_required_inputs(self):
        """验证必需输入是否都已连接"""
        for node_id, node in self.nodes.items():
            inputs, _ = node.get_ports()
            required_inputs = {p.name for p in inputs if p.required}
            
            # 查找连接到此节点的连接
            connected_inputs = {
                conn.to_port
                for conn in self.connections
                if conn.to_node == node_id and conn.enabled
            }
            
            missing = required_inputs - connected_inputs
            if missing:
                raise GraphValidationError(
                    f"节点 {node_id} 缺少必需输入: {missing}"
                )
    
    # ==================== 拓扑排序 ====================
    
    def topological_sort(self) -> List[str]:
        """
        拓扑排序（Kahn 算法）
        
        Returns:
            节点ID列表（执行顺序）
            
        Raises:
            CycleDetectedError: 图中存在循环
        """
        # 计算入度
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        for node_id in self.nodes:
            for neighbor in self.adjacency.get(node_id, []):
                in_degree[neighbor] += 1
        
        # 找到所有入度为0的节点
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in self.adjacency.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self.nodes):
            raise CycleDetectedError("拓扑排序失败：图中存在循环")
        
        return result
    
    # ==================== 辅助方法 ====================
    
    def get_statistics(self) -> Dict:
        """
        获取图统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'name': self.definition.name,
            'version': self.definition.version,
            'node_count': len(self.nodes),
            'connection_count': len([c for c in self.connections if c.enabled]),
            'source_nodes': self.get_source_nodes(),
            'sink_nodes': self.get_sink_nodes()
        }
    
    def __str__(self):
        return f"Graph('{self.definition.name}', nodes={len(self.nodes)}, connections={len(self.connections)})"
    
    def __repr__(self):
        return self.__str__()


# ==================== 辅助函数 ====================

def parse_graph_definition(json_path: str) -> GraphDefinition:
    """
    从 JSON 文件解析图定义
    
    Args:
        json_path: JSON 文件路径
        
    Returns:
        图定义对象
    """
    return GraphDefinition.load_from_file(json_path)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("图管理器测试")
    print("=" * 60)
    
    # 创建测试图定义
    print("\n1. 创建图定义")
    print("-" * 60)
    graph_def = GraphDefinition(
        name="Test Graph",
        version="1.0.0",
        nodes=[
            NodeDefinition(id="node1", type="source", config={}),
            NodeDefinition(id="node2", type="process", config={}),
            NodeDefinition(id="node3", type="sink", config={})
        ],
        connections=[
            Connection(from_node="node1", from_port="out", to_node="node2", to_port="in"),
            Connection(from_node="node2", from_port="out", to_node="node3", to_port="in")
        ]
    )
    print(f"图定义: {graph_def.name}, 节点数: {len(graph_def.nodes)}")
    
    # 创建图
    print("\n2. 创建图对象")
    print("-" * 60)
    graph = Graph(graph_def)
    print(f"图: {graph}")
    print(f"源节点: {graph.get_source_nodes()}")
    print(f"终端节点: {graph.get_sink_nodes()}")
    
    # 测试拓扑排序（需要先添加节点实例）
    print("\n3. 测试拓扑排序")
    print("-" * 60)
    
    # 创建简单的测试节点
    from .node import INode, NodeMetadata, ExecutionContext, NodeResult
    
    class SimpleNode(INode):
        def get_metadata(self):
            return NodeMetadata(
                name="Simple Node",
                version="1.0.0",
                author="Test",
                description="Test node",
                category="test"
            )
        
        def get_ports(self):
            return ([], [])
        
        def validate_config(self, config):
            return True
        
        async def run(self, context):
            return NodeResult(success=True, outputs={})
    
    # 添加节点实例
    for node_def in graph_def.nodes:
        graph.add_node(node_def.id, SimpleNode(node_def.id, node_def.config))
    
    try:
        order = graph.topological_sort()
        print(f"拓扑排序结果: {order}")
    except Exception as e:
        print(f"拓扑排序失败: {e}")
    
    # 测试循环检测
    print("\n4. 测试循环检测")
    print("-" * 60)
    
    # 创建包含循环的图
    cyclic_def = GraphDefinition(
        name="Cyclic Graph",
        version="1.0.0",
        nodes=[
            NodeDefinition(id="A", type="test", config={}),
            NodeDefinition(id="B", type="test", config={}),
            NodeDefinition(id="C", type="test", config={})
        ],
        connections=[
            Connection(from_node="A", from_port="out", to_node="B", to_port="in"),
            Connection(from_node="B", from_port="out", to_node="C", to_port="in"),
            Connection(from_node="C", from_port="out", to_node="A", to_port="in")  # 循环
        ]
    )
    
    cyclic_graph = Graph(cyclic_def)
    for node_def in cyclic_def.nodes:
        cyclic_graph.add_node(node_def.id, SimpleNode(node_def.id, node_def.config))
    
    try:
        cyclic_graph.validate()
        print("验证通过（不应该到达这里）")
    except CycleDetectedError as e:
        print(f"成功检测到循环: {e}")
    
    # 测试保存和加载
    print("\n5. 测试保存和加载")
    print("-" * 60)
    
    test_file = "test_graph.json"
    graph_def.save_to_file(test_file)
    print(f"已保存到: {test_file}")
    
    loaded_def = GraphDefinition.load_from_file(test_file)
    print(f"已加载: {loaded_def.name}, 节点数: {len(loaded_def.nodes)}")
    
    # 清理测试文件
    import os
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"已删除测试文件: {test_file}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
