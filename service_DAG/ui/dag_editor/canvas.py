"""
可视化DAG编辑器 - 画布
"""
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QWheelEvent
from .node_graphics import NodeGraphicsItem, ConnectionGraphicsItem


class GraphCanvas(QGraphicsView):
    """图形化画布"""
    
    def __init__(self):
        super().__init__()
        
        # 创建场景
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 设置画布属性
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 缩放因子
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.min_zoom = 0.3
        self.max_zoom = 3.0
        
        # 连接模式
        self.connecting_mode = False
        self.connection_start_node = None
        self.temp_connection_line = None
        
        # 节点列表
        self.nodes = {}
        self.connections = []
    
    def add_node(self, node_id: str, node_type: str, x: float = 0, y: float = 0):
        """添加节点"""
        node = NodeGraphicsItem(node_id, node_type, x, y)
        self.scene.addItem(node)
        self.nodes[node_id] = node
        return node
    
    def remove_node(self, node_id: str):
        """删除节点"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            
            # 删除相关连接
            for conn in node.connections[:]:
                self.remove_connection(conn)
            
            # 删除节点
            self.scene.removeItem(node)
            del self.nodes[node_id]
    
    def add_connection(self, from_node_id: str, to_node_id: str):
        """添加连接"""
        if from_node_id in self.nodes and to_node_id in self.nodes:
            from_node = self.nodes[from_node_id]
            to_node = self.nodes[to_node_id]
            
            connection = ConnectionGraphicsItem(from_node, to_node)
            self.scene.addItem(connection)
            self.connections.append(connection)
            return connection
        return None
    
    def remove_connection(self, connection: ConnectionGraphicsItem):
        """删除连接"""
        if connection in self.connections:
            self.scene.removeItem(connection)
            self.connections.remove(connection)
            
            # 从节点中移除
            if connection in connection.from_node.connections:
                connection.from_node.connections.remove(connection)
            if connection in connection.to_node.connections:
                connection.to_node.connections.remove(connection)
    
    def clear(self):
        """清空画布"""
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
    
    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮缩放"""
        # 计算缩放因子
        if event.angleDelta().y() > 0:
            factor = 1 + self.zoom_step
        else:
            factor = 1 - self.zoom_step
        
        # 应用缩放
        new_zoom = self.zoom_factor * factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.zoom_factor = new_zoom
    
    def keyPressEvent(self, event):
        """键盘事件"""
        # Delete键删除选中节点
        if event.key() == Qt.Key_Delete:
            for item in self.scene.selectedItems():
                if isinstance(item, NodeGraphicsItem):
                    self.remove_node(item.node_id)
        
        super().keyPressEvent(event)
    
    def get_graph_data(self) -> dict:
        """获取图数据"""
        nodes_data = []
        connections_data = []
        
        # 节点数据
        for node_id, node in self.nodes.items():
            pos = node.scenePos()
            nodes_data.append({
                "id": node_id,
                "type": node.node_type,
                "x": pos.x(),
                "y": pos.y()
            })
        
        # 连接数据
        for conn in self.connections:
            connections_data.append({
                "from_node": conn.from_node.node_id,
                "to_node": conn.to_node.node_id
            })
        
        return {
            "nodes": nodes_data,
            "connections": connections_data
        }
    
    def load_graph_data(self, data: dict):
        """加载图数据"""
        self.clear()
        
        # 加载节点
        for node_data in data.get("nodes", []):
            self.add_node(
                node_data["id"],
                node_data["type"],
                node_data.get("x", 0),
                node_data.get("y", 0)
            )
        
        # 加载连接
        for conn_data in data.get("connections", []):
            self.add_connection(
                conn_data["from_node"],
                conn_data["to_node"]
            )
