# -*- coding: utf-8 -*-
"""
数据类型系统单元测试

响应任务：任务 19.1 - 核心模块测试
"""

import pytest
import numpy as np
from core.data_types import (
    ImageType, BBoxType, DetectionListType, MetadataType,
    StringType, NumberType, BooleanType, TypeRegistry
)


class TestImageType:
    """ImageType测试"""
    
    def test_create_image(self):
        """测试创建图像"""
        data = np.zeros((480, 640, 3), dtype=np.uint8)
        img = ImageType(data=data, width=640, height=480, channels=3, format="BGR")
        
        assert img.width == 640
        assert img.height == 480
        assert img.channels == 3
        assert img.format == "BGR"
        assert img.data.shape == (480, 640, 3)
    
    def test_validate_image(self):
        """测试图像验证"""
        data = np.zeros((480, 640, 3), dtype=np.uint8)
        img = ImageType(data=data, width=640, height=480, channels=3)
        
        assert img.validate() is True
    
    def test_copy_image(self):
        """测试图像复制"""
        data = np.ones((100, 100, 3), dtype=np.uint8)
        img1 = ImageType(data=data, width=100, height=100, channels=3)
        img2 = img1.copy()
        
        assert img2.width == img1.width
        assert img2.height == img1.height
        assert not np.shares_memory(img1.data, img2.data)


class TestBBoxType:
    """BBoxType测试"""
    
    def test_create_bbox(self):
        """测试创建边界框"""
        bbox = BBoxType(x=10, y=20, width=100, height=50, confidence=0.95, class_id=1, class_name="person")
        
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
        assert bbox.confidence == 0.95
        assert bbox.class_id == 1
        assert bbox.class_name == "person"
    
    def test_validate_bbox(self):
        """测试边界框验证"""
        bbox = BBoxType(x=10, y=20, width=100, height=50, confidence=0.95)
        assert bbox.validate() is True
        
        # 无效的置信度
        bbox_invalid = BBoxType(x=10, y=20, width=100, height=50, confidence=1.5)
        assert bbox_invalid.validate() is False


class TestDetectionListType:
    """DetectionListType测试"""
    
    def test_create_detection_list(self):
        """测试创建检测列表"""
        bbox1 = BBoxType(x=10, y=20, width=100, height=50, confidence=0.95)
        bbox2 = BBoxType(x=200, y=100, width=80, height=60, confidence=0.88)
        
        detections = DetectionListType(detections=[bbox1, bbox2])
        
        assert len(detections.detections) == 2
        assert detections.detections[0].x == 10
        assert detections.detections[1].x == 200
    
    def test_validate_detection_list(self):
        """测试检测列表验证"""
        bbox = BBoxType(x=10, y=20, width=100, height=50, confidence=0.95)
        detections = DetectionListType(detections=[bbox])
        
        assert detections.validate() is True


class TestMetadataType:
    """MetadataType测试"""
    
    def test_create_metadata(self):
        """测试创建元数据"""
        metadata = MetadataType(data={"frame_id": 123, "timestamp": 1234567890.0})
        
        assert metadata.data["frame_id"] == 123
        assert metadata.data["timestamp"] == 1234567890.0
    
    def test_validate_metadata(self):
        """测试元数据验证"""
        metadata = MetadataType(data={"key": "value"})
        assert metadata.validate() is True


class TestBasicTypes:
    """基础类型测试"""
    
    def test_string_type(self):
        """测试字符串类型"""
        str_type = StringType(value="test")
        assert str_type.value == "test"
        assert str_type.validate() is True
    
    def test_number_type(self):
        """测试数字类型"""
        num_type = NumberType(value=42.5)
        assert num_type.value == 42.5
        assert num_type.validate() is True
    
    def test_boolean_type(self):
        """测试布尔类型"""
        bool_type = BooleanType(value=True)
        assert bool_type.value is True
        assert bool_type.validate() is True


class TestTypeRegistry:
    """TypeRegistry测试"""
    
    def test_register_type(self):
        """测试类型注册"""
        registry = TypeRegistry()
        
        # 注册类型
        registry.register("image", ImageType)
        
        # 获取类型
        img_type = registry.get("image")
        assert img_type == ImageType
    
    def test_list_types(self):
        """测试列出所有类型"""
        registry = TypeRegistry()
        registry.register("image", ImageType)
        registry.register("bbox", BBoxType)
        
        types = registry.list_types()
        assert "image" in types
        assert "bbox" in types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
