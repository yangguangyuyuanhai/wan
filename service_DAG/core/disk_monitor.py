"""
磁盘空间监控模块
监控磁盘剩余空间，防止磁盘写满
"""
import os
import shutil
import asyncio
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class DiskStatus:
    """磁盘状态"""
    total: int          # 总空间（字节）
    used: int           # 已用空间
    free: int           # 剩余空间
    percent: float      # 使用百分比


class DiskMonitor:
    """磁盘空间监控器"""
    
    def __init__(self, event_bus, check_interval: int = 60,
                 warning_threshold: float = 0.8,
                 critical_threshold: float = 0.9):
        """
        初始化磁盘监控器
        
        Args:
            event_bus: 事件总线
            check_interval: 检查间隔（秒）
            warning_threshold: 警告阈值（使用率）
            critical_threshold: 严重阈值（使用率）
        """
        self.event_bus = event_bus
        self.check_interval = check_interval
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_status = None
    
    def get_disk_status(self, path: str = ".") -> DiskStatus:
        """获取磁盘状态"""
        stat = shutil.disk_usage(path)
        return DiskStatus(
            total=stat.total,
            used=stat.used,
            free=stat.free,
            percent=stat.used / stat.total
        )
    
    async def start(self):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """停止监控"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                status = self.get_disk_status()
                
                # 检查状态变化
                if status.percent >= self.critical_threshold:
                    if self._last_status is None or \
                       self._last_status.percent < self.critical_threshold:
                        await self.event_bus.publish("disk.critical", {
                            "percent": status.percent,
                            "free_gb": status.free / (1024**3),
                            "message": f"磁盘空间严重不足: {status.percent:.1%}"
                        })
                
                elif status.percent >= self.warning_threshold:
                    if self._last_status is None or \
                       self._last_status.percent < self.warning_threshold:
                        await self.event_bus.publish("disk.low_space", {
                            "percent": status.percent,
                            "free_gb": status.free / (1024**3),
                            "message": f"磁盘空间不足: {status.percent:.1%}"
                        })
                
                self._last_status = status
                
            except Exception as e:
                await self.event_bus.publish("log.error", {
                    "message": f"磁盘监控错误: {e}"
                })
            
            await asyncio.sleep(self.check_interval)


class FileRotationManager:
    """文件轮转管理器"""
    
    def __init__(self, base_path: str, max_files: int = 1000,
                 max_days: int = 7, max_size_mb: int = 1000):
        """
        初始化文件轮转管理器
        
        Args:
            base_path: 文件存储路径
            max_files: 最大文件数量
            max_days: 最大保留天数
            max_size_mb: 最大总大小（MB）
        """
        self.base_path = Path(base_path)
        self.max_files = max_files
        self.max_days = max_days
        self.max_size_mb = max_size_mb
    
    def cleanup(self) -> dict:
        """清理旧文件"""
        if not self.base_path.exists():
            return {"deleted": 0, "freed_mb": 0}
        
        files = sorted(self.base_path.glob("*"), key=lambda p: p.stat().st_mtime)
        deleted_count = 0
        freed_bytes = 0
        
        # 按数量清理
        if len(files) > self.max_files:
            for file in files[:len(files) - self.max_files]:
                freed_bytes += file.stat().st_size
                file.unlink()
                deleted_count += 1
        
        # 按时间清理
        import time
        current_time = time.time()
        max_age = self.max_days * 24 * 3600
        
        for file in files:
            if current_time - file.stat().st_mtime > max_age:
                freed_bytes += file.stat().st_size
                file.unlink()
                deleted_count += 1
        
        # 按大小清理
        files = sorted(self.base_path.glob("*"), key=lambda p: p.stat().st_mtime)
        total_size = sum(f.stat().st_size for f in files)
        max_size_bytes = self.max_size_mb * 1024 * 1024
        
        while total_size > max_size_bytes and files:
            file = files.pop(0)
            freed_bytes += file.stat().st_size
            total_size -= file.stat().st_size
            file.unlink()
            deleted_count += 1
        
        return {
            "deleted": deleted_count,
            "freed_mb": freed_bytes / (1024 * 1024)
        }
