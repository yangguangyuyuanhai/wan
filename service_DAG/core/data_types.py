# -*- coding: utf-8 -*-
"""
数据类型系统 (Data Types System)
定义 DAG 节点间传递的强类型数据
支持端口连接时的类型检查、验证和转换

响应需求：需求 2（插件系统）
响应建议：change_plus.md - 必须在里程碑1实现强类型系统
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


# ==================== 基础抽象类 ====================

class BaseDataType(ABC):
    """
    数据类型抽象基类
    所有在 DAG 中传递的数据类型都必须继承此类
    
    核心功能：
    1. 类型验证 (validate)
    2. 类型转换 (convert)
    3. 类型兼容性检查 (is_compatible)
    """
    
    def __init__(self, type_name: str, description: str = ""):
        """
        初始化数据类型
        
        Args:
            type_name: 类型名称（用于注册和查找）
            description: 类型描述
        """
        self.type_name = type_name
        self.description = description
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """
        验证数据是否符合类型要求
        
        Args:
            value: 待验证的数据
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    def convert(self, value: Any) -> Any:
        """
        尝试将数据转换为此类型
        
        Args:
            value: 待转换的数据
            
        Returns:
            Any: 转换后的数据
            
        Raises:
            TypeError: 无法转换时抛出
            ValueError: 数据不符合约束时抛出
        """
        pass
    
    def is_compatible(self, other: 'BaseDataType') -> bool:
        """
        检查是否与另一个类型兼容（可连接）
        
        Args:
            other: 另一个数据类型
            
        Returns:
            bool: 是否兼容
        """
        # 默认实现：相同类型才兼容
        return type(self) == type(other)
    
    def __str__(self):
        return f"{self.__class__.__name__}('{self.type_name}')"
    
    def __repr__(self):
        return self.__str__()


# ==================== 图像类型 ====================

class ImageFormat(Enum):
    """图像格式枚举"""
    GRAY = "GRAY"      # 灰度图
    RGB = "RGB"        # RGB 彩色图
    BGR = "BGR"        # BGR 彩色图（OpenCV 默认）
    RGBA = "RGBA"      # 带透明通道的 RGB
    BGRA = "BGRA"      # 带透明通道的 BGR


@dataclass
class ImageData:
    """
    图像数据容器
    包含图像数组和元数据
    """
    array: np.ndarray                    # 图像数组
    width: int                           # 宽度
    height: int                          # 高度
    format: ImageFormat                  # 图像格式
    timestamp: Optional[float] = None    # 时间戳
    frame_id: Optional[int] = None       # 帧ID
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def __post_init__(self):
        """验证数据一致性"""
        if self.array.shape[0] != self.height or self.array.shape[1] != self.width:
            raise ValueError(f"图像尺寸不匹配: array.shape={self.array.shape}, "
                           f"width={self.width}, height={self.height}")


class ImageType(BaseDataType):
    """
    图像类型
    支持 numpy array 格式的图像数据
    """
    
    def __init__(self, format: Optional[ImageFormat] = None, 
                 min_width: Optional[int] = None,
                 min_height: Optional[int] = None):
        """
        初始化图像类型
        
        Args:
            format: 图像格式约束（None 表示任意格式）
            min_width: 最小宽度约束
            min_height: 最小高度约束
        """
        super().__init__("Image", "图像数据类型")
        self.format = format
        self.min_width = min_width
        self.min_height = min_height
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效图像"""
        # 检查是否为 ImageData 实例
        if not isinstance(value, ImageData):
            return False
        
        # 检查格式约束
        if self.format is not None and value.format != self.format:
            return False
        
        # 检查尺寸约束
        if self.min_width is not None and value.width < self.min_width:
            return False
        
        if self.min_height is not None and value.height < self.min_height:
            return False
        
        return True
    
    def convert(self, value: Any) -> ImageData:
        """转换为图像数据"""
        # 如果已经是 ImageData，直接返回
        if isinstance(value, ImageData):
            return value
        
        # 如果是 numpy array，尝试转换
        if isinstance(value, np.ndarray):
            height, width = value.shape[:2]
            
            # 推断格式
            if len(value.shape) == 2:
                format = ImageFormat.GRAY
            elif len(value.shape) == 3:
                channels = value.shape[2]
                if channels == 3:
                    format = ImageFormat.BGR  # 默认 OpenCV 格式
                elif channels == 4:
                    format = ImageFormat.BGRA
                else:
                    raise ValueError(f"不支持的通道数: {channels}")
            else:
                raise ValueError(f"不支持的图像维度: {value.shape}")
            
            return ImageData(
                array=value,
                width=width,
                height=height,
                format=format
            )
        
        raise TypeError(f"无法将 {type(value)} 转换为 ImageType")
    
    def is_compatible(self, other: BaseDataType) -> bool:
        """图像类型兼容性检查"""
        if not isinstance(other, ImageType):
            return False
        
        # 如果任一方未指定格式，则兼容
        if self.format is None or other.format is None:
            return True
        
        return self.format == other.format


# ==================== 边界框类型 ====================

@dataclass
class BBoxData:
    """
    边界框数据容器
    """
    x: float                             # 左上角 x 坐标
    y: float                             # 左上角 y 坐标
    w: float                             # 宽度
    h: float                             # 高度
    confidence: float = 1.0              # 置信度 [0, 1]
    class_id: Optional[int] = None       # 类别ID
    class_name: Optional[str] = None     # 类别名称
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def __post_init__(self):
        """验证数据有效性"""
        if self.w <= 0 or self.h <= 0:
            raise ValueError(f"边界框尺寸必须为正数: w={self.w}, h={self.h}")
        
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"置信度必须在 [0, 1] 范围内: {self.confidence}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'x': self.x,
            'y': self.y,
            'w': self.w,
            'h': self.h,
            'confidence': self.confidence,
            'class_id': self.class_id,
            'class_name': self.class_name,
            'metadata': self.metadata
        }


class BBoxType(BaseDataType):
    """
    边界框类型
    表示目标检测的边界框
    """
    
    def __init__(self, min_confidence: float = 0.0):
        """
        初始化边界框类型
        
        Args:
            min_confidence: 最小置信度阈值
        """
        super().__init__("BBox", "边界框类型")
        self.min_confidence = min_confidence
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效边界框"""
        if not isinstance(value, BBoxData):
            return False
        
        # 检查置信度阈值
        if value.confidence < self.min_confidence:
            return False
        
        return True
    
    def convert(self, value: Any) -> BBoxData:
        """转换为边界框数据"""
        # 如果已经是 BBoxData，直接返回
        if isinstance(value, BBoxData):
            return value
        
        # 如果是字典，尝试转换
        if isinstance(value, dict):
            return BBoxData(
                x=value['x'],
                y=value['y'],
                w=value['w'],
                h=value['h'],
                confidence=value.get('confidence', 1.0),
                class_id=value.get('class_id'),
                class_name=value.get('class_name'),
                metadata=value.get('metadata', {})
            )
        
        # 如果是元组或列表 (x, y, w, h)
        if isinstance(value, (tuple, list)) and len(value) >= 4:
            return BBoxData(
                x=value[0],
                y=value[1],
                w=value[2],
                h=value[3],
                confidence=value[4] if len(value) > 4 else 1.0
            )
        
        raise TypeError(f"无法将 {type(value)} 转换为 BBoxType")


# ==================== 检测结果列表类型 ====================

class DetectionListType(BaseDataType):
    """
    检测结果列表类型
    表示多个目标检测结果
    """
    
    def __init__(self, min_confidence: float = 0.0):
        """
        初始化检测结果列表类型
        
        Args:
            min_confidence: 最小置信度阈值
        """
        super().__init__("DetectionList", "检测结果列表类型")
        self.min_confidence = min_confidence
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效检测结果列表"""
        if not isinstance(value, list):
            return False
        
        # 检查每个元素是否为 BBoxData
        for item in value:
            if not isinstance(item, BBoxData):
                return False
            if item.confidence < self.min_confidence:
                return False
        
        return True
    
    def convert(self, value: Any) -> List[BBoxData]:
        """转换为检测结果列表"""
        if isinstance(value, list):
            # 尝试转换每个元素
            bbox_type = BBoxType()
            result = []
            for item in value:
                result.append(bbox_type.convert(item))
            return result
        
        raise TypeError(f"无法将 {type(value)} 转换为 DetectionListType")


# ==================== 元数据类型 ====================

class MetadataType(BaseDataType):
    """
    元数据类型
    表示通用的键值对字典
    """
    
    def __init__(self, required_keys: Optional[List[str]] = None):
        """
        初始化元数据类型
        
        Args:
            required_keys: 必需的键列表
        """
        super().__init__("Metadata", "元数据类型")
        self.required_keys = required_keys or []
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效元数据"""
        if not isinstance(value, dict):
            return False
        
        # 检查必需键
        for key in self.required_keys:
            if key not in value:
                return False
        
        return True
    
    def convert(self, value: Any) -> Dict[str, Any]:
        """转换为元数据"""
        if isinstance(value, dict):
            return value
        
        raise TypeError(f"无法将 {type(value)} 转换为 MetadataType")


# ==================== 基础类型 ====================

class StringType(BaseDataType):
    """字符串类型"""
    
    def __init__(self, max_length: Optional[int] = None, 
                 pattern: Optional[str] = None):
        """
        初始化字符串类型
        
        Args:
            max_length: 最大长度约束
            pattern: 正则表达式模式约束
        """
        super().__init__("String", "字符串类型")
        self.max_length = max_length
        self.pattern = pattern
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效字符串"""
        if not isinstance(value, str):
            return False
        
        if self.max_length is not None and len(value) > self.max_length:
            return False
        
        if self.pattern is not None:
            import re
            if not re.match(self.pattern, value):
                return False
        
        return True
    
    def convert(self, value: Any) -> str:
        """转换为字符串"""
        return str(value)


class NumberType(BaseDataType):
    """
    数值类型
    支持整数和浮点数
    """
    
    def __init__(self, min_value: Optional[float] = None,
                 max_value: Optional[float] = None,
                 integer_only: bool = False):
        """
        初始化数值类型
        
        Args:
            min_value: 最小值约束
            max_value: 最大值约束
            integer_only: 是否仅允许整数
        """
        super().__init__("Number", "数值类型")
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效数值"""
        if not isinstance(value, (int, float, np.number)):
            return False
        
        if self.integer_only and not isinstance(value, (int, np.integer)):
            return False
        
        if self.min_value is not None and value < self.min_value:
            return False
        
        if self.max_value is not None and value > self.max_value:
            return False
        
        return True
    
    def convert(self, value: Any) -> Union[int, float]:
        """转换为数值"""
        try:
            if self.integer_only:
                return int(value)
            else:
                return float(value)
        except Exception as e:
            raise TypeError(f"无法将 {type(value)} 转换为 NumberType: {e}")


class BooleanType(BaseDataType):
    """布尔类型"""
    
    def __init__(self):
        super().__init__("Boolean", "布尔类型")
    
    def validate(self, value: Any) -> bool:
        """验证是否为有效布尔值"""
        return isinstance(value, bool)
    
    def convert(self, value: Any) -> bool:
        """转换为布尔值"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ('true', '1', 'yes', 'on'):
                return True
            if value_lower in ('false', '0', 'no', 'off'):
                return False
        
        return bool(value)


# ==================== 类型注册表 ====================

class TypeRegistry:
    """
    类型注册表
    管理所有可用的数据类型
    支持类型注册、查找和兼容性检查
    """
    
    def __init__(self):
        """初始化类型注册表"""
        self._types: Dict[str, BaseDataType] = {}
        self._register_builtin_types()
    
    def _register_builtin_types(self):
        """注册内置类型"""
        # 图像类型
        self.register(ImageType())
        
        # 边界框类型
        self.register(BBoxType())
        
        # 检测结果列表类型
        self.register(DetectionListType())
        
        # 元数据类型
        self.register(MetadataType())
        
        # 基础类型
        self.register(StringType())
        self.register(NumberType())
        self.register(BooleanType())
    
    def register(self, data_type: BaseDataType):
        """
        注册数据类型
        
        Args:
            data_type: 数据类型实例
        """
        self._types[data_type.type_name] = data_type
        print(f"[TypeRegistry] 注册类型: {data_type.type_name}")
    
    def get(self, type_name: str) -> Optional[BaseDataType]:
        """
        获取数据类型
        
        Args:
            type_name: 类型名称
            
        Returns:
            数据类型实例，如果不存在返回 None
        """
        return self._types.get(type_name)
    
    def list_types(self) -> List[str]:
        """
        列出所有已注册的类型
        
        Returns:
            类型名称列表
        """
        return list(self._types.keys())
    
    def check_compatibility(self, source_type_name: str, target_type_name: str) -> bool:
        """
        检查两个类型是否兼容
        
        Args:
            source_type_name: 源类型名称
            target_type_name: 目标类型名称
            
        Returns:
            是否兼容
        """
        source = self.get(source_type_name)
        target = self.get(target_type_name)
        
        if source is None or target is None:
            return False
        
        return source.is_compatible(target)
    
    def validate_value(self, type_name: str, value: Any) -> bool:
        """
        验证值是否符合指定类型
        
        Args:
            type_name: 类型名称
            value: 待验证的值
            
        Returns:
            是否有效
        """
        data_type = self.get(type_name)
        if data_type is None:
            return False
        
        return data_type.validate(value)
    
    def convert_value(self, type_name: str, value: Any) -> Any:
        """
        将值转换为指定类型
        
        Args:
            type_name: 类型名称
            value: 待转换的值
            
        Returns:
            转换后的值
            
        Raises:
            TypeError: 类型不存在或无法转换
        """
        data_type = self.get(type_name)
        if data_type is None:
            raise TypeError(f"类型不存在: {type_name}")
        
        return data_type.convert(value)


# 全局类型注册表实例
global_type_registry = TypeRegistry()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("数据类型系统测试")
    print("=" * 60)
    
    # 测试图像类型
    print("\n1. 测试图像类型")
    print("-" * 60)
    img_type = ImageType(format=ImageFormat.BGR)
    test_array = np.zeros((480, 640, 3), dtype=np.uint8)
    img_data = ImageData(
        array=test_array,
        width=640,
        height=480,
        format=ImageFormat.BGR,
        frame_id=1
    )
    print(f"图像数据: {img_data.width}x{img_data.height}, 格式: {img_data.format}")
    print(f"图像验证: {img_type.validate(img_data)}")
    
    # 测试边界框类型
    print("\n2. 测试边界框类型")
    print("-" * 60)
    bbox_type = BBoxType(min_confidence=0.5)
    bbox_data = BBoxData(
        x=100, y=200, w=50, h=80,
        confidence=0.85,
        class_id=1,
        class_name="person"
    )
    print(f"边界框: ({bbox_data.x}, {bbox_data.y}, {bbox_data.w}, {bbox_data.h})")
    print(f"置信度: {bbox_data.confidence}, 类别: {bbox_data.class_name}")
    print(f"边界框验证: {bbox_type.validate(bbox_data)}")
    
    # 测试检测结果列表类型
    print("\n3. 测试检测结果列表类型")
    print("-" * 60)
    detection_list_type = DetectionListType(min_confidence=0.5)
    detections = [
        BBoxData(x=10, y=20, w=30, h=40, confidence=0.9, class_name="cat"),
        BBoxData(x=50, y=60, w=70, h=80, confidence=0.8, class_name="dog")
    ]
    print(f"检测结果数量: {len(detections)}")
    print(f"检测列表验证: {detection_list_type.validate(detections)}")
    
    # 测试类型转换
    print("\n4. 测试类型转换")
    print("-" * 60)
    bbox_dict = {'x': 10, 'y': 20, 'w': 30, 'h': 40, 'confidence': 0.75}
    converted_bbox = bbox_type.convert(bbox_dict)
    print(f"字典转边界框: {converted_bbox}")
    
    # 测试类型注册表
    print("\n5. 测试类型注册表")
    print("-" * 60)
    registry = global_type_registry
    print(f"已注册类型: {registry.list_types()}")
    print(f"Image 与 Image 兼容: {registry.check_compatibility('Image', 'Image')}")
    print(f"Image 与 String 兼容: {registry.check_compatibility('Image', 'String')}")
    
    # 测试基础类型
    print("\n6. 测试基础类型")
    print("-" * 60)
    string_type = StringType(max_length=10)
    print(f"字符串验证 'hello': {string_type.validate('hello')}")
    print(f"字符串验证 'hello world': {string_type.validate('hello world')}")
    
    number_type = NumberType(min_value=0, max_value=100)
    print(f"数值验证 50: {number_type.validate(50)}")
    print(f"数值验证 150: {number_type.validate(150)}")
    
    bool_type = BooleanType()
    print(f"布尔转换 'true': {bool_type.convert('true')}")
    print(f"布尔转换 'false': {bool_type.convert('false')}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
