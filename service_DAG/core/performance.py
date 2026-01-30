"""
性能分析和优化工具
提供完整的性能监控、分析和优化功能
"""
import time
import psutil
import asyncio
import gc
import cProfile
import pstats
import io
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    fps: float
    avg_latency_ms: float
    frame_count: int
    node_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """性能报告"""
    duration_seconds: float
    avg_cpu_percent: float
    peak_cpu_percent: float
    avg_memory_mb: float
    peak_memory_mb: float
    avg_fps: float
    min_fps: float
    max_fps: float
    avg_latency_ms: float
    total_frames: int
    bottlenecks: List[str]
    recommendations: List[str]


class PerformanceProfiler:
    """性能分析器 - 实时监控和分析系统性能"""
    
    def __init__(self, sample_size: int = 100):
        """
        初始化性能分析器
        
        Args:
            sample_size: 采样窗口大小
        """
        self.process = psutil.Process()
        self.sample_size = sample_size
        
        # 时间序列数据
        self.frame_times: List[float] = []
        self.node_times: Dict[str, List[float]] = {}
        self.metrics_history: List[PerformanceMetrics] = []
        
        # 统计数据
        self.start_time = time.time()
        self.total_frames = 0
        
        # 性能阈值
        self.cpu_warning_threshold = 80.0  # CPU使用率警告阈值
        self.memory_warning_threshold = 80.0  # 内存使用率警告阈值
        self.latency_warning_threshold = 100.0  # 延迟警告阈值(ms)
    
    def record_frame(self, duration: float):
        """记录帧处理时间"""
        self.frame_times.append(duration)
        self.total_frames += 1
        
        # 保持窗口大小
        if len(self.frame_times) > self.sample_size:
            self.frame_times.pop(0)
    
    def record_node(self, node_id: str, duration: float):
        """记录节点执行时间"""
        if node_id not in self.node_times:
            self.node_times[node_id] = []
        
        self.node_times[node_id].append(duration)
        
        # 保持窗口大小
        if len(self.node_times[node_id]) > self.sample_size:
            self.node_times[node_id].pop(0)
    
    def capture_metrics(self) -> PerformanceMetrics:
        """捕获当前性能指标"""
        # 系统资源
        cpu = self.process.cpu_percent()
        mem_info = self.process.memory_info()
        memory_mb = mem_info.rss / 1024 / 1024
        memory_percent = self.process.memory_percent()
        
        # FPS计算
        fps = 0.0
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        # 延迟计算
        avg_latency = 0.0
        if self.frame_times:
            avg_latency = sum(self.frame_times) / len(self.frame_times) * 1000
        
        # 节点指标
        node_metrics = {}
        for node_id, times in self.node_times.items():
            if times:
                node_metrics[node_id] = {
                    'avg_ms': sum(times) / len(times) * 1000,
                    'min_ms': min(times) * 1000,
                    'max_ms': max(times) * 1000,
                    'count': len(times)
                }
        
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            fps=fps,
            avg_latency_ms=avg_latency,
            frame_count=self.total_frames,
            node_metrics=node_metrics
        )
        
        # 保存历史
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.sample_size:
            self.metrics_history.pop(0)
        
        return metrics
    
    def identify_bottlenecks(self) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        # 检查节点执行时间
        for node_id, times in self.node_times.items():
            if times:
                avg_time_ms = sum(times) / len(times) * 1000
                if avg_time_ms > 50:  # 超过50ms
                    bottlenecks.append(
                        f"节点 {node_id}: 平均执行时间 {avg_time_ms:.1f}ms (建议优化)"
                    )
        
        # 检查CPU使用率
        if self.metrics_history:
            recent_cpu = [m.cpu_percent for m in self.metrics_history[-10:]]
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            if avg_cpu > self.cpu_warning_threshold:
                bottlenecks.append(
                    f"CPU使用率过高: {avg_cpu:.1f}% (建议使用run_in_executor)"
                )
        
        # 检查内存使用
        if self.metrics_history:
            recent_mem = [m.memory_percent for m in self.metrics_history[-10:]]
            avg_mem = sum(recent_mem) / len(recent_mem)
            if avg_mem > self.memory_warning_threshold:
                bottlenecks.append(
                    f"内存使用率过高: {avg_mem:.1f}% (建议优化内存使用)"
                )
        
        # 检查延迟
        if self.frame_times:
            recent_latency = sum(self.frame_times[-10:]) / len(self.frame_times[-10:]) * 1000
            if recent_latency > self.latency_warning_threshold:
                bottlenecks.append(
                    f"延迟过高: {recent_latency:.1f}ms (建议优化流水线)"
                )
        
        return bottlenecks
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于瓶颈生成建议
        bottlenecks = self.identify_bottlenecks()
        
        if any("CPU使用率过高" in b for b in bottlenecks):
            recommendations.append("使用run_in_executor将CPU密集任务移到线程池")
            recommendations.append("检查是否有不必要的同步操作")
        
        if any("内存使用率过高" in b for b in bottlenecks):
            recommendations.append("实现对象池复用大对象")
            recommendations.append("及时释放不再使用的数据")
            recommendations.append("使用float32代替float64")
        
        if any("延迟过高" in b for b in bottlenecks):
            recommendations.append("调整队列大小以平衡吞吐量和延迟")
            recommendations.append("检查是否有阻塞操作")
        
        # 节点级别建议
        for node_id, times in self.node_times.items():
            if times:
                avg_time_ms = sum(times) / len(times) * 1000
                if avg_time_ms > 50:
                    recommendations.append(
                        f"优化节点 {node_id}: 考虑算法优化或并行处理"
                    )
        
        return recommendations
    
    def generate_report(self) -> PerformanceReport:
        """生成完整性能报告"""
        duration = time.time() - self.start_time
        
        # CPU统计
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        peak_cpu = max(cpu_values) if cpu_values else 0
        
        # 内存统计
        mem_values = [m.memory_mb for m in self.metrics_history]
        avg_mem = sum(mem_values) / len(mem_values) if mem_values else 0
        peak_mem = max(mem_values) if mem_values else 0
        
        # FPS统计
        fps_values = [m.fps for m in self.metrics_history if m.fps > 0]
        avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0
        min_fps = min(fps_values) if fps_values else 0
        max_fps = max(fps_values) if fps_values else 0
        
        # 延迟统计
        latency_values = [m.avg_latency_ms for m in self.metrics_history]
        avg_latency = sum(latency_values) / len(latency_values) if latency_values else 0
        
        return PerformanceReport(
            duration_seconds=duration,
            avg_cpu_percent=avg_cpu,
            peak_cpu_percent=peak_cpu,
            avg_memory_mb=avg_mem,
            peak_memory_mb=peak_mem,
            avg_fps=avg_fps,
            min_fps=min_fps,
            max_fps=max_fps,
            avg_latency_ms=avg_latency,
            total_frames=self.total_frames,
            bottlenecks=self.identify_bottlenecks(),
            recommendations=self.generate_recommendations()
        )
    
    def print_report(self):
        """打印性能报告"""
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("性能分析报告")
        print("=" * 70)
        print(f"运行时长: {report.duration_seconds:.1f}秒")
        print(f"总帧数: {report.total_frames}")
        print()
        print("CPU使用率:")
        print(f"  平均: {report.avg_cpu_percent:.1f}%")
        print(f"  峰值: {report.peak_cpu_percent:.1f}%")
        print()
        print("内存使用:")
        print(f"  平均: {report.avg_memory_mb:.1f} MB")
        print(f"  峰值: {report.peak_memory_mb:.1f} MB")
        print()
        print("帧率 (FPS):")
        print(f"  平均: {report.avg_fps:.1f}")
        print(f"  最小: {report.min_fps:.1f}")
        print(f"  最大: {report.max_fps:.1f}")
        print()
        print(f"平均延迟: {report.avg_latency_ms:.1f} ms")
        
        if report.bottlenecks:
            print()
            print("⚠ 性能瓶颈:")
            for bottleneck in report.bottlenecks:
                print(f"  • {bottleneck}")
        
        if report.recommendations:
            print()
            print("💡 优化建议:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("=" * 70)
    
    def save_report(self, filepath: str):
        """保存报告到文件"""
        report = self.generate_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("性能分析报告\n")
            f.write("=" * 70 + "\n")
            f.write(f"运行时长: {report.duration_seconds:.1f}秒\n")
            f.write(f"总帧数: {report.total_frames}\n\n")
            
            f.write("CPU使用率:\n")
            f.write(f"  平均: {report.avg_cpu_percent:.1f}%\n")
            f.write(f"  峰值: {report.peak_cpu_percent:.1f}%\n\n")
            
            f.write("内存使用:\n")
            f.write(f"  平均: {report.avg_memory_mb:.1f} MB\n")
            f.write(f"  峰值: {report.peak_memory_mb:.1f} MB\n\n")
            
            f.write("帧率 (FPS):\n")
            f.write(f"  平均: {report.avg_fps:.1f}\n")
            f.write(f"  最小: {report.min_fps:.1f}\n")
            f.write(f"  最大: {report.max_fps:.1f}\n\n")
            
            f.write(f"平均延迟: {report.avg_latency_ms:.1f} ms\n\n")
            
            if report.bottlenecks:
                f.write("性能瓶颈:\n")
                for bottleneck in report.bottlenecks:
                    f.write(f"  • {bottleneck}\n")
                f.write("\n")
            
            if report.recommendations:
                f.write("优化建议:\n")
                for i, rec in enumerate(report.recommendations, 1):
                    f.write(f"  {i}. {rec}\n")


class MemoryOptimizer:
    """内存优化器 - 提供内存优化工具"""
    
    @staticmethod
    def optimize_image_dtype(image: np.ndarray) -> np.ndarray:
        """优化图像数据类型"""
        if image.dtype == np.float64:
            return image.astype(np.float32)
        return image
    
    @staticmethod
    def clear_cache():
        """清理Python垃圾回收缓存"""
        gc.collect()
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process()
        mem_info = process.memory_info()
        
        return {
            'rss_mb': mem_info.rss / 1024 / 1024,
            'vms_mb': mem_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }


class CPUProfiler:
    """CPU性能分析器 - 使用cProfile进行详细分析"""
    
    def __init__(self):
        self.profiler = cProfile.Profile()
        self.is_profiling = False
    
    def start(self):
        """开始性能分析"""
        self.profiler.enable()
        self.is_profiling = True
    
    def stop(self):
        """停止性能分析"""
        self.profiler.disable()
        self.is_profiling = False
    
    def print_stats(self, sort_by: str = 'cumulative', limit: int = 20):
        """打印统计信息"""
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.sort_stats(sort_by)
        ps.print_stats(limit)
        print(s.getvalue())
    
    def save_stats(self, filepath: str):
        """保存统计信息到文件"""
        self.profiler.dump_stats(filepath)


# 性能优化最佳实践
PERFORMANCE_BEST_PRACTICES = """
性能优化最佳实践

1. CPU优化:
   ✓ 使用run_in_executor处理CPU密集任务(YOLO, OpenCV)
   ✓ 避免在主事件循环中执行阻塞操作
   ✓ 使用numpy向量化操作代替Python循环
   ✓ 合理设置线程池大小(通常为CPU核心数)

2. 内存优化:
   ✓ 及时释放大对象(图像数据)
   ✓ 使用float32代替float64
   ✓ 实现对象池复用频繁创建的对象
   ✓ 定期调用gc.collect()清理内存

3. I/O优化:
   ✓ 使用异步I/O操作(aiofiles)
   ✓ 批量写入日志减少I/O次数
   ✓ 压缩存储数据节省空间
   ✓ 使用内存映射文件处理大文件

4. 流水线优化:
   ✓ 调整队列大小平衡吞吐量和延迟
   ✓ 识别并优化瓶颈节点
   ✓ 使用COW减少不必要的数据复制
   ✓ 实现并行分支提高并发度

5. 事件系统优化:
   ✓ 使用事件节流避免事件风暴
   ✓ 异步发布事件避免阻塞
   ✓ 批量处理事件减少开销

6. 监控和分析:
   ✓ 使用PerformanceProfiler实时监控
   ✓ 定期生成性能报告
   ✓ 识别瓶颈并针对性优化
   ✓ 进行性能回归测试
"""
