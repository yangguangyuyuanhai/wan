# 异步版本测试文件索引

本目录包含异步版本的所有测试文件。

## 📚 测试文件列表

### 当前状态
目前异步版本的测试文件尚未创建。

### 计划添加的测试

#### 异步核心测试
- **test_async_pipeline.py** - 异步管道测试
  - 测试异步管道创建和运行
  - 测试异步过滤器执行
  - 测试并发处理性能

#### 多相机测试
- **test_multi_camera.py** - 多相机管理测试
  - 测试多相机枚举
  - 测试并发采集
  - 测试相机管理器

#### 异步服务测试
- **test_async_services.py** - 异步服务测试
  - 测试异步预处理服务
  - 测试异步YOLO服务
  - 测试异步显示服务

#### 性能测试
- **test_async_performance.py** - 异步性能测试
  - 测试并发处理性能
  - 对比同步vs异步性能
  - 测试多相机吞吐量

## 🧪 测试计划

### 第一阶段：基础测试
- [ ] 异步管道核心功能测试
- [ ] 异步过滤器执行测试
- [ ] 数据包异步传输测试

### 第二阶段：集成测试
- [ ] 多相机并发采集测试
- [ ] 异步服务集成测试
- [ ] 端到端异步处理测试

### 第三阶段：性能测试
- [ ] 并发性能基准测试
- [ ] 多相机吞吐量测试
- [ ] 资源使用率测试

## 🚀 运行测试（待实现）

### 方法1：直接运行
```bash
cd tests_asyncio
python test_async_pipeline.py
```

### 方法2：使用pytest
```bash
cd tests_asyncio
pytest
```

### 方法3：使用批处理文件
```bash
测试异步版本.bat
```

## 📊 测试重点

### 异步特性测试
- ✅ asyncio事件循环
- ✅ 异步队列处理
- ✅ 并发任务管理
- ✅ 异步上下文管理

### 多相机测试
- ✅ 多相机同时采集
- ✅ 相机资源管理
- ✅ 并发数据处理
- ✅ 负载均衡

### 性能测试
- ✅ 吞吐量测试
- ✅ 延迟测试
- ✅ CPU使用率
- ✅ 内存使用率

## 📂 相关目录

- **异步代码**: ../service_asyncio/
- **核心测试**: ../tests_core/
- **异步文档**: ../docs_asyncio/

## 🔧 测试环境要求

### 必需依赖
- Python 3.7+ (支持asyncio)
- numpy
- opencv-python

### 测试工具
- pytest
- pytest-asyncio（异步测试支持）
- pytest-benchmark（性能测试）

## 📝 测试模板

### 异步测试函数模板
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    """异步测试说明"""
    # 准备测试数据
    # 执行异步测试
    result = await async_function()
    # 验证结果
    assert result is not None
```

### 多相机测试模板
```python
@pytest.mark.asyncio
async def test_multi_camera():
    """多相机测试说明"""
    # 创建多相机管理器
    manager = MultiCameraManager(config)
    
    # 枚举设备
    count = manager.enumerate_devices()
    
    # 并发采集
    packets = await manager.grab_from_all_cameras()
    
    # 验证结果
    assert len(packets) > 0
```

## 📝 文档维护

- 所有异步版本测试文件都应放在此目录
- 测试应充分验证异步特性
- 测试应包含性能基准
- 测试应定期运行和更新
