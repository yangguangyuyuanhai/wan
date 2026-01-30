# 性能基准测试

## 概述

本目录包含 DAG 系统的性能基准测试工具。

## 测试脚本

### 1. quick_benchmark.py - 快速性能测试

快速验证系统基本性能。

**运行方式：**
```bash
cd service_DAG
python tests/performance/quick_benchmark.py
```

**测试内容：**
- Producer -> Process -> Consumer 管道
- 100 条测试数据
- 测量吞吐量和延迟

### 2. benchmark.py - 完整性能基准测试

完整的性能基准测试，包含多个测试场景。

**运行方式：**
```bash
cd service_DAG
python tests/performance/benchmark.py
```

**测试内容：**
- 简单管道（Producer -> Consumer）
- 处理管道（Producer -> Process -> Consumer）
- 1000 帧测试数据
- 测量 FPS、延迟、内存使用

## 性能指标

### 关键指标

1. **吞吐量（FPS）** - 每秒处理的帧数
2. **平均延迟** - 从生产到消费的平均时间
3. **内存增长** - 运行期间的内存增长量

### 准入标准

- 新版本性能 ≥ 旧版本的 90%
- 内存增长 < 100 MB（1000 帧）
- 无内存泄漏

## 结果文件

测试结果会保存到 `benchmark_results.txt`
