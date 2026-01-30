# -*- coding: utf-8 -*-
"""
端口定义
定义节点的输入输出端口，支持类型检查和连接验证
"""

from enum import Enum, auto
from typing import Any, Optional
from dataclasses import dataclass
from core.types import DataType
from core.exceptions import TypeMismatchError


class PortDirection(Enum):
    """端口方向"""
    INPUT = auto()   # 输入端口
    OUTPUT = auto()  # 输出端口


class PortType(Enum):
    """端口类型"""
    DATA = auto()      # 数据端口（传递数据）
    CONTROL = auto()   # 控制端口（触发执行）
    EVENT = auto()     # 事件端口（发送事件）


@dataclass
class Port:
    """
    端口类
    定义节点的输入输出接口
    """
    # 端口名称
    name: str
    
    # 端口方向
    direction: PortDirection
    
    # 数据类型
    data_type: DataType
    
    # 端口类型
    port_type: PortType = PortType.DATA
    
    # 是否必需
    required: bool = True
    
    # 默认值（输入端口）
    default_value: Any = None
    
    # 描述
    description: str = ""
    
    # 所属节点ID
    node_id: str = ""
    
    # 当前值
    _value: Any = None
    
    # 连接的端口
    _connected_port: Optional['Port'] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.default_value is not None:
            self._value = self.default_value
    
    def set_value(self, value: Any):
        """
        设置端口值
        
        Args:
            value: 值
            
        Raises:
            TypeMismatchError: 类型不匹配
        """
        # 验证类型
        if not self.data_type.validate(value):
            raise TypeMismatchError(
                f"端口 {self.name} 类型不匹配",
                {"expected": self.data_type, "got": type(value)}
            )
        
        self._value = value
    
    def get_value(self) -> Any:
        """
        获取端口值
        
        Returns:
            端口值
        """
        return self._value
    
    def has_value(self) -> bool:
        """
        检查是否有值
        
        Returns:
            是否有值
        """
        return self._value is not None
    
    def clear_value(self):
        """清空端口值"""
        self._value = None
    
    def connect_to(self, other_port: 'Port') -> bool:
        """
        连接到另一个端口
        
        Args:
            other_port: 目标端口
            
        Returns:
            是否连接成功
        """
        # 检查方向
        if self.direction == other_port.direction:
            return False
        
        # 检查类型兼容性
        if self.direction == PortDirection.OUTPUT:
            # 输出端口连接到输入端口
            if not self.data_type.is_compatible_with(other_port.data_type):
                return False
            self._connected_port = other_port
            other_port._connected_port = self
        else:
            # 输入端口连接到输出端口
            if not other_port.data_type.is_compatible_with(self.data_type):
                return False
            self._connected_port = other_port
            other_port._connected_port = self
        
        return True
    
    def disconnect(self):
        """断开连接"""
        if self._connected_port:
            self._connected_port._connected_port = None
            self._connected_port = None
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            是否已连接
        """
        return self._connected_port is not None
    
    def get_connected_port(self) -> Optional['Port']:
        """
        获取连接的端口
        
        Returns:
            连接的端口
        """
        return self._connected_port
    
    def transfer_value(self):
        """
        传递值到连接的端口（输出端口调用）
        """
        if self.direction == PortDirection.OUTPUT and self._connected_port:
            if self.has_value():
                self._connected_port.set_value(self._value)
    
    def get_full_name(self) -> str:
        """
        获取完整名称（节点ID.端口名）
        
        Returns:
            完整名称
        """
        if self.node_id:
            return f"{self.node_id}.{self.name}"
        return self.name
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "name": self.name,
            "direction": self.direction.name,
            "data_type": str(self.data_type),
            "port_type": self.port_type.name,
            "required": self.required,
            "description": self.description,
            "node_id": self.node_id,
            "has_value": self.has_value(),
            "is_connected": self.is_connected()
        }
    
    def __str__(self):
        direction_symbol = "→" if self.direction == PortDirection.OUTPUT else "←"
        return f"{direction_symbol} {self.get_full_name()} [{self.data_type}]"
    
    def __repr__(self):
        return self.__str__()


class PortCollection:
    """
    端口集合
    管理节点的所有端口
    """
    
    def __init__(self, node_id: str = ""):
        self.node_id = node_id
        self._inputs: dict[str, Port] = {}
        self._outputs: dict[str, Port] = {}
    
    def add_input(self, port: Port):
        """
        添加输入端口
        
        Args:
            port: 端口对象
        """
        port.node_id = self.node_id
        port.direction = PortDirection.INPUT
        self._inputs[port.name] = port
    
    def add_output(self, port: Port):
        """
        添加输出端口
        
        Args:
            port: 端口对象
        """
        port.node_id = self.node_id
        port.direction = PortDirection.OUTPUT
        self._outputs[port.name] = port
    
    def get_input(self, name: str) -> Optional[Port]:
        """获取输入端口"""
        return self._inputs.get(name)
    
    def get_output(self, name: str) -> Optional[Port]:
        """获取输出端口"""
        return self._outputs.get(name)
    
    def list_inputs(self) -> list[Port]:
        """列出所有输入端口"""
        return list(self._inputs.values())
    
    def list_outputs(self) -> list[Port]:
        """列出所有输出端口"""
        return list(self._outputs.values())
    
    def get_all_ports(self) -> list[Port]:
        """获取所有端口"""
        return self.list_inputs() + self.list_outputs()
    
    def clear_all_values(self):
        """清空所有端口的值"""
        for port in self.get_all_ports():
            port.clear_value()
    
    def validate_required_inputs(self) -> bool:
        """
        验证所有必需的输入端口是否有值
        
        Returns:
            是否全部有值
        """
        for port in self._inputs.values():
            if port.required and not port.has_value():
                return False
        return True


if __name__ == "__main__":
    # 测试端口系统
    print("端口系统测试\n")
    
    from core.types import Image, Number
    
    # 创建端口
    print("1. 创建端口")
    input_port = Port(
        name="image_in",
        direction=PortDirection.INPUT,
        data_type=Image(),
        description="输入图像"
    )
    
    output_port = Port(
        name="image_out",
        direction=PortDirection.OUTPUT,
        data_type=Image(),
        description="输出图像"
    )
    
    print(f"输入端口: {input_port}")
    print(f"输出端口: {output_port}")
    
    # 测试连接
    print("\n2. 测试端口连接")
    success = output_port.connect_to(input_port)
    print(f"连接成功: {success}")
    print(f"输出端口已连接: {output_port.is_connected()}")
    print(f"输入端口已连接: {input_port.is_connected()}")
    
    # 测试数据传递
    print("\n3. 测试数据传递")
    import numpy as np
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    output_port.set_value(test_image)
    output_port.transfer_value()
    print(f"输入端口有值: {input_port.has_value()}")
    print(f"值的形状: {input_port.get_value().shape}")
    
    # 测试端口集合
    print("\n4. 测试端口集合")
    ports = PortCollection(node_id="node_1")
    ports.add_input(Port("in1", PortDirection.INPUT, Number()))
    ports.add_input(Port("in2", PortDirection.INPUT, Number()))
    ports.add_output(Port("out1", PortDirection.OUTPUT, Number()))
    
    print(f"输入端口: {[p.name for p in ports.list_inputs()]}")
    print(f"输出端口: {[p.name for p in ports.list_outputs()]}")
    
    print("\n测试完成")


# ==================== 辅助函数 ====================

def InputPort(name: str, data_type: DataType, required: bool = True, 
              default_value: Any = None, description: str = "") -> Port:
    """
    创建输入端口的辅助函数
    
    Args:
        name: 端口名称
        data_type: 数据类型
        required: 是否必需
        default_value: 默认值
        description: 描述
        
    Returns:
        输入端口对象
    """
    return Port(
        name=name,
        direction=PortDirection.INPUT,
        data_type=data_type,
        required=required,
        default_value=default_value,
        description=description
    )


def OutputPort(name: str, data_type: DataType, required: bool = True,
               description: str = "") -> Port:
    """
    创建输出端口的辅助函数
    
    Args:
        name: 端口名称
        data_type: 数据类型
        required: 是否必需
        description: 描述
        
    Returns:
        输出端口对象
    """
    return Port(
        name=name,
        direction=PortDirection.OUTPUT,
        data_type=data_type,
        required=required,
        description=description
    )
