# -*- coding: utf-8 -*-
"""
数据类型系统
定义 DAG 节点间传递的强类型数据
支持端口连接时的类型检查
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
import numpy as np


class DataType(ABC):
    """
    数据类型基类
    所有在 DAG 中传递的数据都必须继承此类
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """
        验证数据是否符合类型要求
        
        Args:
            value: 待验证的数据
            
        Returns:
            是否有效
        """
        pass
    
    @abstractmethod
    def convert(self, value: Any) -> Any:
        """
        尝试将数据转换为此类型
        
        Args:
            value: 待转换的数据
            
        Returns:
            转换后的数据
            
        Raises:
            TypeError: 无法转换
        """
        pass
    
    def is_compatible_with(self, other: 'DataType') -> bool:
        """
        检查是否与另一个类型兼容（可连接）
        
        Args:
            other: 另一个数据类型
            
        Returns:
            是否兼容
        """
        # 默认实现：相同类型才兼容
        return type(self) == type(other)
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self):
        return self.__str__()


# ==================== 基础数据类型 ====================

class Image(DataType):
    """
    图像类型
    支持 numpy array 格式的图像数据
    """
    
    def __init__(self, name: str = "Image", channels: Optional[int] = None, 
                 dtype: Optional[np.dtype] = None):
        super().__init__(name, "图像数据")
        self.channels = channels  # None表示任意通道数
        self.dtype = dtype        # None表示任意数据类型
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效图像"""
        if not isinstance(value, np.ndarray):
            return False
        
        if len(value.shape) < 2:
            return False
        
        if self.channels is not None:
            if len(value.shape) == 2 and self.channels != 1:
                return False
            if len(value.shape) == 3 and value.shape[2] != self.channels:
                return False
        
        if self.dtype is not None:
            if value.dtype != self.dtype:
                return False
        
        return True
    
    def convert(self, value: Any) -> np.ndarray:
        """转换为图像"""
        if isinstance(value, np.ndarray):
            return value
        
        # 尝试从其他类型转换
        try:
            return np.array(value)
        except Exception as e:
            raise TypeError(f"无法将 {type(value)} 转换为 Image: {e}")
    
    def is_compatible_with(self, other: DataType) -> bool:
        """图像类型兼容性检查"""
        if not isinstance(other, Image):
            return False
        
        # 如果任一方未指定通道数，则兼容
        if self.channels is None or other.channels is None:
            return True
        
        return self.channels == other.channels


class Point(DataType):
    """
    点类型
    表示 2D 或 3D 坐标点
    """
    
    def __init__(self, name: str = "Point", dimensions: int = 2):
        super().__init__(name, f"{dimensions}D坐标点")
        self.dimensions = dimensions
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效点"""
        if isinstance(value, (tuple, list)):
            return len(value) == self.dimensions
        
        if isinstance(value, np.ndarray):
            return value.shape == (self.dimensions,)
        
        return False
    
    def convert(self, value: Any) -> tuple:
        """转换为点"""
        if isinstance(value, tuple) and len(value) == self.dimensions:
            return value
        
        if isinstance(value, (list, np.ndarray)):
            if len(value) == self.dimensions:
                return tuple(value)
        
        raise TypeError(f"无法将 {type(value)} 转换为 {self.dimensions}D Point")


class Region(DataType):
    """
    区域类型
    表示矩形区域 (x, y, width, height)
    """
    
    def __init__(self, name: str = "Region"):
        super().__init__(name, "矩形区域")
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效区域"""
        if isinstance(value, (tuple, list)):
            return len(value) == 4
        
        if isinstance(value, dict):
            return all(k in value for k in ['x', 'y', 'width', 'height'])
        
        return False
    
    def convert(self, value: Any) -> tuple:
        """转换为区域"""
        if isinstance(value, tuple) and len(value) == 4:
            return value
        
        if isinstance(value, list) and len(value) == 4:
            return tuple(value)
        
        if isinstance(value, dict):
            return (value['x'], value['y'], value['width'], value['height'])
        
        raise TypeError(f"无法将 {type(value)} 转换为 Region")


class String(DataType):
    """字符串类型"""
    
    def __init__(self, name: str = "String", max_length: Optional[int] = None):
        super().__init__(name, "字符串")
        self.max_length = max_length
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效字符串"""
        if not isinstance(value, str):
            return False
        
        if self.max_length is not None:
            return len(value) <= self.max_length
        
        return True
    
    def convert(self, value: Any) -> str:
        """转换为字符串"""
        return str(value)


class Number(DataType):
    """
    数值类型
    支持整数和浮点数
    """
    
    def __init__(self, name: str = "Number", min_value: Optional[float] = None,
                 max_value: Optional[float] = None):
        super().__init__(name, "数值")
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效数值"""
        if not isinstance(value, (int, float, np.number)):
            return False
        
        if self.min_value is not None and value < self.min_value:
            return False
        
        if self.max_value is not None and value > self.max_value:
            return False
        
        return True
    
    def convert(self, value: Any) -> float:
        """转换为数值"""
        try:
            return float(value)
        except Exception as e:
            raise TypeError(f"无法将 {type(value)} 转换为 Number: {e}")


class Boolean(DataType):
    """布尔类型"""
    
    def __init__(self, name: str = "Boolean"):
        super().__init__(name, "布尔值")
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效布尔值"""
        return isinstance(value, bool)
    
    def convert(self, value: Any) -> bool:
        """转换为布尔值"""
        return bool(value)


class Array(DataType):
    """
    数组类型
    表示同类型元素的列表
    """
    
    def __init__(self, name: str = "Array", element_type: Optional[DataType] = None):
        super().__init__(name, "数组")
        self.element_type = element_type
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效数组"""
        if not isinstance(value, (list, tuple)):
            return False
        
        if self.element_type is not None:
            return all(self.element_type.validate(item) for item in value)
        
        return True
    
    def convert(self, value: Any) -> list:
        """转换为数组"""
        if isinstance(value, list):
            return value
        
        if isinstance(value, tuple):
            return list(value)
        
        if isinstance(value, np.ndarray):
            return value.tolist()
        
        raise TypeError(f"无法将 {type(value)} 转换为 Array")


# ==================== 复合数据类型 ====================

@dataclass
class Detection:
    """
    检测结果类型
    表示目标检测的单个结果
    """
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple  # (x, y, width, height)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'confidence': self.confidence,
            'bbox': self.bbox
        }


class DetectionList(DataType):
    """
    检测结果列表类型
    """
    
    def __init__(self, name: str = "DetectionList"):
        super().__init__(name, "检测结果列表")
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效检测结果列表"""
        if not isinstance(value, list):
            return False
        
        return all(isinstance(item, Detection) for item in value)
    
    def convert(self, value: Any) -> List[Detection]:
        """转换为检测结果列表"""
        if isinstance(value, list):
            # 尝试转换每个元素
            result = []
            for item in value:
                if isinstance(item, Detection):
                    result.append(item)
                elif isinstance(item, dict):
                    result.append(Detection(**item))
                else:
                    raise TypeError(f"无法将 {type(item)} 转换为 Detection")
            return result
        
        raise TypeError(f"无法将 {type(value)} 转换为 DetectionList")


# ==================== 类型注册表 ====================

class TypeRegistry:
    """
    类型注册表
    管理所有可用的数据类型
    """
    
    def __init__(self):
        self._types: Dict[str, DataType] = {}
        self._register_builtin_types()
    
    def _register_builtin_types(self):
        """注册内置类型"""
        self.register(Image())
        self.register(Point())
        self.register(Region())
        self.register(String())
        self.register(Number())
        self.register(Boolean())
        self.register(Array())
        self.register(DetectionList())
    
    def register(self, data_type: DataType):
        """
        注册数据类型
        
        Args:
            data_type: 数据类型实例
        """
        type_name = data_type.__class__.__name__
        self._types[type_name] = data_type
    
    def get(self, type_name: str) -> Optional[DataType]:
        """
        获取数据类型
        
        Args:
            type_name: 类型名称
            
        Returns:
            数据类型实例，如果不存在返回 None
        """
        return self._types.get(type_name)
    
    def list_types(self) -> List[str]:
        """列出所有已注册的类型"""
        return list(self._types.keys())
    
    def check_compatibility(self, source_type: str, target_type: str) -> bool:
        """
        检查两个类型是否兼容
        
        Args:
            source_type: 源类型名称
            target_type: 目标类型名称
            
        Returns:
            是否兼容
        """
        source = self.get(source_type)
        target = self.get(target_type)
        
        if source is None or target is None:
            return False
        
        return source.is_compatible_with(target)


# 全局类型注册表实例
global_type_registry = TypeRegistry()


if __name__ == "__main__":
    # 测试数据类型系统
    print("数据类型系统测试\n")
    
    # 测试图像类型
    img_type = Image(channels=3)
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    print(f"图像验证: {img_type.validate(test_img)}")
    
    # 测试点类型
    point_type = Point(dimensions=2)
    test_point = (100, 200)
    print(f"点验证: {point_type.validate(test_point)}")
    
    # 测试类型兼容性
    img_type1 = Image(channels=3)
    img_type2 = Image(channels=3)
    img_type3 = Image(channels=1)
    print(f"RGB图像兼容性: {img_type1.is_compatible_with(img_type2)}")
    print(f"RGB与灰度图兼容性: {img_type1.is_compatible_with(img_type3)}")
    
    # 测试类型注册表
    registry = TypeRegistry()
    print(f"\n已注册类型: {registry.list_types()}")
    print(f"Image与Image兼容: {registry.check_compatibility('Image', 'Image')}")
    print(f"Image与String兼容: {registry.check_compatibility('Image', 'String')}")
    
    print("\n测试完成")
