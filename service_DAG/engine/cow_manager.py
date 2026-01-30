# -*- coding: utf-8 -*-
"""
写时复制(COW)和并行分支增强模块
为StreamingExecutor提供智能数据复制和并行分支执行功能

响应任务：任务 16 - 实现写时复制(COW)和并行分支
"""

import asyncio
import copy
from typing import Dict, Any, List, Optional
import time


class COWDataManager:
    """
    写时复制数据管理器
    
    功能：
    1. 智能数据复制策略
    2. 数据大小估算
    3. 分支优化
    4. 性能监控
    """
    
    def __init__(self):
        """初始化COW数据管理器"""
        # 统计信息
        self.copy_count = 0
        self.zero_copy_count = 0
        self.total_copy_time = 0.0
        self.total_data_size = 0
        
        # 配置
        self.deep_copy_threshold = 1024 * 1024  # 1MB以上使用深拷贝
        self.max_branches_for_shallow_copy = 3  # 最多3个分支使用浅拷贝
    
    def should_deep_copy_data(self, data: Any, branch_count: int) -> bool:
        """
        判断是否需要深拷贝数据
        
        Args:
            data: 数据对象
            branch_count: 分支数量
            
        Returns:
            bool: 是否需要深拷贝
        """
        try:
            # 导入数据类型
            from core.data_types import ImageType, DetectionListType
            
            # 对于图像数据，总是深拷贝（避免并发修改）
            if isinstance(data, ImageType):
                return True
            
            # 对于检测结果，如果分支数量多，使用深拷贝
            if isinstance(data, DetectionListType) and branch_count > self.max_branches_for_shallow_copy:
                return True
        except ImportError:
            pass
        
        # 对于numpy数组，根据大小决定
        try:
            import numpy as np
            if isinstance(data, np.ndarray):
                data_size = data.nbytes
                return data_size > self.deep_copy_threshold or branch_count > self.max_branches_for_shallow_copy
        except ImportError:
            pass
        
        # 估算数据大小
        data_size = self.estimate_data_size(data)
        if data_size > self.deep_copy_threshold:
            return True
        
        # 分支数量多时使用深拷贝
        return branch_count > self.max_branches_for_shallow_copy
    
    def smart_copy_data(self, data: Any) -> Any:
        """
        智能数据复制
        
        Args:
            data: 数据对象
            
        Returns:
            复制后的数据
        """
        start_time = time.time()
        
        try:
            # 对于自定义数据类型，使用其内置的复制方法
            if hasattr(data, 'copy'):
                result = data.copy()
                self.copy_count += 1
                self.total_copy_time += time.time() - start_time
                return result
            
            # 对于numpy数组，使用copy()
            try:
                import numpy as np
                if isinstance(data, np.ndarray):
                    result = data.copy()
                    self.copy_count += 1
                    self.total_copy_time += time.time() - start_time
                    self.total_data_size += data.nbytes
                    return result
            except ImportError:
                pass
            
            # 默认使用浅拷贝
            result = copy.copy(data)
            self.copy_count += 1
            self.total_copy_time += time.time() - start_time
            return result
            
        except Exception as e:
            # 复制失败，返回原始数据（风险：可能被修改）
            print(f"数据复制失败: {e}")
            return data
    
    def deep_copy_data(self, data: Any) -> Any:
        """
        深拷贝数据
        
        Args:
            data: 数据对象
            
        Returns:
            深拷贝后的数据
        """
        start_time = time.time()
        
        try:
            result = copy.deepcopy(data)
            self.copy_count += 1
            self.total_copy_time += time.time() - start_time
            self.total_data_size += self.estimate_data_size(data)
            return result
            
        except Exception as e:
            print(f"深拷贝失败: {e}")
            return self.smart_copy_data(data)
    
    def estimate_data_size(self, data: Any) -> int:
        """
        估算数据大小（字节）
        
        Args:
            data: 数据对象
            
        Returns:
            int: 估算的数据大小
        """
        try:
            import sys
            
            # 对于numpy数组
            try:
                import numpy as np
                if isinstance(data, np.ndarray):
                    return data.nbytes
            except ImportError:
                pass
            
            # 对于自定义数据类型
            try:
                from core.data_types import ImageType, DetectionListType
                
                if isinstance(data, ImageType):
                    return data.data.nbytes if hasattr(data.data, 'nbytes') else sys.getsizeof(data.data)
                
                if isinstance(data, DetectionListType):
                    return sys.getsizeof(data.detections) * len(data.detections)
                    
            except ImportError:
                pass
            
            # 默认使用sys.getsizeof
            return sys.getsizeof(data)
            
        except Exception:
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取COW统计信息"""
        avg_copy_time = (self.total_copy_time / self.copy_count 
                        if self.copy_count > 0 else 0.0)
        
        return {
            "copy_count": self.copy_count,
            "zero_copy_count": self.zero_copy_count,
            "total_copy_time": self.total_copy_time,
            "average_copy_time": avg_copy_time,
            "total_data_size": self.total_data_size,
            "copy_efficiency": self.zero_copy_count / max(self.copy_count + self.zero_copy_count, 1)
        }


class ParallelBranchManager:
    """
    并行分支管理器
    
    功能：
    1. 并行分支执行
    2. 分支负载均衡
    3. 分支性能监控
    4. 错误处理
    """
    
    def __init__(self):
        """初始化并行分支管理器"""
        # 统计信息
        self.branch_count = 0
        self.parallel_executions = 0
        self.total_branch_time = 0.0
        self.branch_errors = 0
        
        # 配置
        self.max_concurrent_branches = 10  # 最大并发分支数
        self.branch_timeout = 30.0  # 分支超时时间（秒）
    
    async def execute_parallel_branches(self, branch_tasks: List[asyncio.Task]) -> List[Any]:
        """
        并行执行分支任务
        
        Args:
            branch_tasks: 分支任务列表
            
        Returns:
            List[Any]: 执行结果列表
        """
        if not branch_tasks:
            return []
        
        start_time = time.time()
        self.parallel_executions += 1
        self.branch_count += len(branch_tasks)
        
        try:
            # 限制并发数量
            if len(branch_tasks) > self.max_concurrent_branches:
                # 分批执行
                results = []
                for i in range(0, len(branch_tasks), self.max_concurrent_branches):
                    batch = branch_tasks[i:i + self.max_concurrent_branches]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    results.extend(batch_results)
                return results
            else:
                # 直接并行执行
                results = await asyncio.wait_for(
                    asyncio.gather(*branch_tasks, return_exceptions=True),
                    timeout=self.branch_timeout
                )
                return results
                
        except asyncio.TimeoutError:
            self.branch_errors += 1
            print(f"分支执行超时: {len(branch_tasks)} 个分支")
            return [None] * len(branch_tasks)
            
        except Exception as e:
            self.branch_errors += 1
            print(f"并行分支执行失败: {e}")
            return [None] * len(branch_tasks)
            
        finally:
            self.total_branch_time += time.time() - start_time
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取并行分支统计信息"""
        avg_branch_time = (self.total_branch_time / self.parallel_executions 
                          if self.parallel_executions > 0 else 0.0)
        
        avg_branches_per_execution = (self.branch_count / self.parallel_executions 
                                    if self.parallel_executions > 0 else 0.0)
        
        return {
            "parallel_executions": self.parallel_executions,
            "total_branches": self.branch_count,
            "branch_errors": self.branch_errors,
            "total_branch_time": self.total_branch_time,
            "average_branch_time": avg_branch_time,
            "average_branches_per_execution": avg_branches_per_execution,
            "error_rate": self.branch_errors / max(self.parallel_executions, 1)
        }


# 全局实例
_cow_manager = COWDataManager()
_branch_manager = ParallelBranchManager()


def get_cow_manager() -> COWDataManager:
    """获取COW数据管理器实例"""
    return _cow_manager


def get_branch_manager() -> ParallelBranchManager:
    """获取并行分支管理器实例"""
    return _branch_manager
