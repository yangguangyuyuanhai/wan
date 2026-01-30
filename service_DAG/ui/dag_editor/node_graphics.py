"""
可视化DAG编辑器 - 图形化节点
"""
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsEllipseItem, 
                             QGraphicsTextItem, QGraphicsLineItem)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter


class NodeGraphicsItem(QGraphicsItem):
    """图形化节点"""
    
    def __init__(self, node_id: str, node_type: str, x: float = 0, y: float = 0):
        super().__init__()
        
        self.node_id = node_id
        self.node_type = node_type
        
        # 节点尺寸
        self.width = 150
        self.height = 80
        
        # 设置位置
        self.setPos(x, y)
        
        # 设置标志
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # 端口
        self.input_ports = []
        self.output_ports = []
        
        # 连接线
        self.connections = []
    
    def boundingRect(self) -> QRectF:
        """边界矩形"""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter: QPainter, option, widget):
        """绘制节点"""
        # 节点背景
        if self.isSelected():
            painter.setBrush(QBrush(QColor(100, 150, 255)))
        else:
            painter.setBrush(QBrush(QColor(70, 70, 70)))
        
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        
        # 节点标题
        painter.setPen(QPen(QColor(255, 255, 255)))
        title_rect = QRectF(5, 5, self.width - 10, 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.node_id)
        
        # 节点类型
        painter.setPen(QPen(QColor(180, 180, 180)))
        type_rect = QRectF(5, 30, self.width - 10, 20)
        painter.drawText(type_rect, Qt.AlignCenter, f"[{self.node_type}]")
        
        # 输入端口
        port_y = 55
        painter.setBrush(QBrush(QColor(100, 255, 100)))
        painter.drawEllipse(5, port_y, 10, 10)
        painter.drawText(20, port_y + 10, "input")
        
        # 输出端口
        painter.setBrush(QBrush(QColor(255, 100, 100)))
        painter.drawEllipse(self.width - 15, port_y, 10, 10)
        painter.drawText(self.width - 60, port_y + 10, "output")
    
    def itemChange(self, change, value):
        """节点变化时更新连接线"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            for connection in self.connections:
                connection.update_position()
        
        return super().itemChange(change, value)
    
    def get_input_port_pos(self) -> QPointF:
        """获取输入端口位置"""
        return self.scenePos() + QPointF(10, 60)
    
    def get_output_port_pos(self) -> QPointF:
        """获取输出端口位置"""
        return self.scenePos() + QPointF(self.width - 10, 60)


class ConnectionGraphicsItem(QGraphicsLineItem):
    """连接线"""
    
    def __init__(self, from_node: NodeGraphicsItem, to_node: NodeGraphicsItem):
        super().__init__()
        
        self.from_node = from_node
        self.to_node = to_node
        
        # 设置样式
        self.setPen(QPen(QColor(150, 150, 150), 2))
        
        # 注册到节点
        from_node.connections.append(self)
        to_node.connections.append(self)
        
        # 更新位置
        self.update_position()
    
    def update_position(self):
        """更新连接线位置"""
        start = self.from_node.get_output_port_pos()
        end = self.to_node.get_input_port_pos()
        self.setLine(start.x(), start.y(), end.x(), end.y())
