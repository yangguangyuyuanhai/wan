# -*- coding: utf-8 -*-
"""
异步微服务模块
将同步服务包装为异步服务
"""

import asyncio
from pipeline_core_async import AsyncFilter, DataPacket
from typing import Optional

# 导入原始同步服务
import sys
import os

# 添加service_new根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
service_new_root = os.path.dirname(current_dir)
if service_new_root not in sys.path:
    sys.path.insert(0, service_new_root)

from services.preprocess_service import PreprocessService
from services.yolo_service import YOLOService
from services.opencv_service import OpenCVService
from services.display_service import DisplayService
from services.storage_service import StorageService


class AsyncPreprocessService(AsyncFilter):
    """异步预处理服务"""
    
    def __init__(self, config):
        super().__init__("AsyncPreprocessService", config)
        self.sync_service = PreprocessService(config)
    
    async def process(self, packet: DataPacket) -> Optional[DataPacket]:
        """异步处理"""
        # 在线程池中执行同步处理
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_service.process, packet)


class AsyncYOLOService(AsyncFilter):
    """异步YOLO服务"""
    
    def __init__(self, config):
        super().__init__("AsyncYOLOService", config)
        self.sync_service = YOLOService(config)
    
    async def process(self, packet: DataPacket) -> Optional[DataPacket]:
        """异步处理"""
        # 在线程池中执行同步处理
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_service.process, packet)


class AsyncOpenCVService(AsyncFilter):
    """异步OpenCV服务"""
    
    def __init__(self, config):
        super().__init__("AsyncOpenCVService", config)
        self.sync_service = OpenCVService(config)
    
    async def process(self, packet: DataPacket) -> Optional[DataPacket]:
        """异步处理"""
        # 在线程池中执行同步处理
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_service.process, packet)


class AsyncDisplayService(AsyncFilter):
    """异步显示服务"""
    
    def __init__(self, config):
        super().__init__("AsyncDisplayService", config)
        self.sync_service = DisplayService(config)
    
    async def process(self, packet: DataPacket) -> Optional[DataPacket]:
        """异步处理"""
        # 在线程池中执行同步处理
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_service.process, packet)


class AsyncStorageService(AsyncFilter):
    """异步存储服务"""
    
    def __init__(self, config):
        super().__init__("AsyncStorageService", config)
        self.sync_service = StorageService(config)
    
    async def process(self, packet: DataPacket) -> Optional[DataPacket]:
        """异步处理"""
        # 在线程池中执行同步处理
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_service.process, packet)


__all__ = [
    'AsyncPreprocessService',
    'AsyncYOLOService',
    'AsyncOpenCVService',
    'AsyncDisplayService',
    'AsyncStorageService',
]
