"""
心跳机制模块
定期写入心跳文件，供守护进程检查
"""
import asyncio
import time
from pathlib import Path
from typing import Optional


class HeartbeatManager:
    """心跳管理器"""
    
    def __init__(self, heartbeat_file: str = "heartbeat.txt",
                 interval: int = 10):
        """
        初始化心跳管理器
        
        Args:
            heartbeat_file: 心跳文件路径
            interval: 心跳间隔（秒）
        """
        self.heartbeat_file = Path(heartbeat_file)
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动心跳"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self):
        """停止心跳"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # 删除心跳文件
        if self.heartbeat_file.exists():
            self.heartbeat_file.unlink()
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                # 写入当前时间戳
                with open(self.heartbeat_file, 'w') as f:
                    f.write(str(time.time()))
                
                await asyncio.sleep(self.interval)
            except Exception:
                # 忽略写入错误
                pass
