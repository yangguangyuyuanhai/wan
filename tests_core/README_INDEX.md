# 核心测试文件索引

本目录包含核心系统的所有测试文件。

## 📚 测试文件列表

### 导入测试
- **test_imports.py** - 模块导入测试
  - 测试所有核心模块是否可以正常导入
  - 验证无父目录依赖
  - 检查模块完整性

### 系统测试
- **test_system.py** - 系统功能测试
  - 测试管道核心功能
  - 测试过滤器执行
  - 测试数据包处理

### 批处理测试
- **测试导入.bat** - Windows批处理测试脚本
  - 自动激活conda环境
  - 运行导入测试
  - 显示测试结果

## 🧪 测试说明

### test_imports.py
测试所有模块的导入功能，确保：
- 核心模块可以正常导入
- 微服务模块可以正常导入
- 异步版本模块可以正常导入
- Qt GUI模块可以正常导入（如果安装了PyQt5）
- 无父目录依赖

### test_system.py
测试系统核心功能，包括：
- Pipeline创建和运行
- Filter执行和性能
- DataPacket处理
- 队列管理

## 🚀 运行测试

### 方法1：直接运行Python脚本
```bash
# 导入测试
python test_imports.py

# 系统测试
python test_system.py
```

### 方法2：使用批处理文件（Windows）
```bash
# 运行导入测试（自动激活conda环境）
测试导入.bat
```

### 方法3：使用pytest（推荐）
```bash
# 安装pytest
pip install pytest

# 运行所有测试
pytest

# 运行特定测试
pytest test_imports.py
pytest test_system.py
```

## 📊 测试覆盖

### 已覆盖的模块
- ✅ logger_config
- ✅ pipeline_config
- ✅ pipeline_core
- ✅ scheduler
- ✅ main
- ✅ services/*

### 待添加的测试
- ⏳ 相机服务集成测试
- ⏳ YOLO服务测试
- ⏳ OpenCV服务测试
- ⏳ 端到端测试

## 📂 相关目录

- **核心代码**: ../
- **异步测试**: ../tests_asyncio/
- **Qt测试**: ../tests_qt/
- **文档**: ../docs_core/

## 🔧 测试环境

### 必需依赖
- Python 3.7+
- numpy
- opencv-python

### 可选依赖
- pytest（用于测试框架）
- pytest-cov（用于代码覆盖率）
- PyQt5（用于GUI测试）

## 📝 添加新测试

### 测试文件命名规范
- 测试文件以 `test_` 开头
- 测试函数以 `test_` 开头
- 测试类以 `Test` 开头

### 测试文件模板
```python
# -*- coding: utf-8 -*-
"""
测试模块说明
"""

def test_功能名称():
    """测试说明"""
    # 准备测试数据
    # 执行测试
    # 验证结果
    assert True
```

## 📝 文档维护

- 所有核心系统测试文件都应放在此目录
- 测试应覆盖主要功能
- 测试应包含清晰的注释
- 测试应定期运行和更新
