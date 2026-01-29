# Service_new 项目结构说明

本文档详细说明 service_new 项目的完整目录结构和文件组织。

## 📁 完整目录结构

```
service_new/                          # 项目根目录
│
├── 📄 main.py                        # 主程序入口（同步版本）
├── 📄 scheduler.py                   # 管道调度器
├── 📄 pipeline_core.py               # 管道核心模块
├── 📄 pipeline_config.py             # 配置管理模块
├── 📄 logger_config.py               # 日志配置模块
├── 📄 requirements.txt               # Python依赖列表
│
├── 📄 DOCUMENTATION_INDEX.md         # 📚 文档和测试总索引
├── 📄 PROJECT_STRUCTURE.md           # 📁 本文件 - 项目结构说明
│
├── 🔧 启动同步版本.bat               # Windows启动脚本
├── 🔧 一键启动所有版本.bat           # 一键启动所有版本
├── 🔧 快速测试.bat                   # 快速测试脚本
├── 🔧 检查环境.bat                   # 环境检查脚本
├── 🔧 安装依赖.bat                   # 依赖安装脚本
│
├── 📂 services/                      # 微服务模块目录
│   ├── __init__.py                   # 包初始化文件
│   ├── camera_service.py             # 相机采集服务
│   ├── preprocess_service.py         # 图像预处理服务
│   ├── yolo_service.py               # YOLO检测服务
│   ├── opencv_service.py             # OpenCV处理服务
│   ├── display_service.py            # 图像显示服务
│   └── storage_service.py            # 数据存储服务
│
├── 📂 service_asyncio/               # 异步版本目录
│   ├── main_async.py                 # 异步主程序
│   ├── scheduler_async.py            # 异步调度器
│   ├── pipeline_core_async.py        # 异步管道核心
│   ├── camera_service_async.py       # 异步相机服务
│   ├── services_async.py             # 异步服务包装
│   ├── pipeline_config.py            # 配置文件（链接）
│   ├── logger_config.py              # 日志配置（链接）
│   ├── requirements.txt              # 异步版本依赖
│   └── 启动异步版本.bat              # 异步版本启动脚本
│
├── 📂 service_qt/                    # Qt GUI版本目录
│   ├── run_gui.py                    # GUI启动脚本
│   ├── main_window.py                # 主窗口
│   ├── widgets.py                    # 自定义控件
│   ├── dialogs.py                    # 对话框
│   ├── styles.py                     # 样式定义
│   ├── __init__.py                   # 包初始化文件
│   ├── requirements_qt.txt           # Qt版本依赖
│   ├── 启动GUI.bat                   # GUI启动脚本
│   └── logs/                         # Qt版本日志目录
│
├── 📂 docs_core/                     # 📚 核心系统文档目录
│   ├── README_INDEX.md               # 文档索引
│   ├── README.md                     # 项目总览
│   ├── 快速启动指南.md               # 快速上手
│   ├── 快速开始.md                   # 详细快速开始
│   ├── 系统架构说明.md               # 架构设计
│   ├── 开始使用_最终版.md            # 完整使用指南
│   ├── 项目总结.md                   # 功能总结
│   ├── 启动脚本说明.md               # 脚本使用说明
│   ├── 启动脚本创建完成.md           # 脚本创建记录
│   ├── 组织完成说明.md               # 项目组织说明
│   ├── 依赖修复完成报告.txt          # 依赖修复报告
│   └── 测试报告.md                   # 测试报告
│
├── 📂 docs_asyncio/                  # 📚 异步版本文档目录
│   ├── README_INDEX.md               # 文档索引
│   ├── README_ASYNCIO.md             # 异步版本说明
│   ├── 异步版本说明.md               # 开发说明
│   ├── 依赖关系说明.md               # 依赖关系
│   └── 目录清理说明.md               # 目录结构
│
├── 📂 docs_qt/                       # 📚 Qt GUI文档目录
│   ├── README_INDEX.md               # 文档索引
│   ├── README.md                     # Qt版本总览
│   ├── 快速开始.md                   # 快速开始
│   └── Qt界面开发说明.md             # 界面开发
│
├── 📂 tests_core/                    # 🧪 核心系统测试目录
│   ├── README_INDEX.md               # 测试索引
│   ├── test_imports.py               # 导入测试
│   ├── test_system.py                # 系统测试
│   └── 测试导入.bat                  # 测试脚本
│
├── 📂 tests_asyncio/                 # 🧪 异步版本测试目录
│   └── README_INDEX.md               # 测试索引（待添加测试）
│
├── 📂 tests_qt/                      # 🧪 Qt GUI测试目录
│   ├── README_INDEX.md               # 测试索引
│   ├── test_qt.py                    # Qt导入测试
│   ├── test_gui_startup.py           # GUI启动测试
│   └── 测试Qt版本.bat                # 测试脚本
│
└── 📂 logs/                          # 日志文件目录
    ├── PipelineCore_daily.log        # 按日期轮转日志
    ├── PipelineCore_detail.log       # 详细日志
    └── PipelineCore_error.log        # 错误日志
```

## 📊 目录功能说明

### 核心模块（根目录）
**作用**: 包含同步版本的核心代码和配置

**主要文件**:
- `main.py` - 上帝类，系统入口
- `scheduler.py` - 管道调度器
- `pipeline_core.py` - 管道-过滤器架构核心
- `pipeline_config.py` - 配置管理
- `logger_config.py` - 日志系统

**特点**:
- ✅ 完整的管道-过滤器架构
- ✅ 微服务设计
- ✅ 配置化管理
- ✅ 专业日志系统

---

### 微服务目录 (services/)
**作用**: 包含所有微服务模块

**服务列表**:
1. `camera_service.py` - 相机采集
2. `preprocess_service.py` - 图像预处理
3. `yolo_service.py` - YOLO目标检测
4. `opencv_service.py` - OpenCV图像处理
5. `display_service.py` - 实时显示
6. `storage_service.py` - 数据存储

**特点**:
- ✅ 独立的服务模块
- ✅ 统一的Filter接口
- ✅ 可配置启用/禁用
- ✅ 性能监控

---

### 异步版本目录 (service_asyncio/)
**作用**: 异步多相机并发处理版本

**核心文件**:
- `main_async.py` - 异步主程序
- `scheduler_async.py` - 异步调度器
- `pipeline_core_async.py` - 异步管道核心
- `camera_service_async.py` - 异步相机服务
- `services_async.py` - 异步服务包装

**特点**:
- ✅ 基于asyncio
- ✅ 多相机并发
- ✅ 高性能处理
- ✅ 自动负载均衡

**适用场景**:
- 多相机同时采集
- 高并发处理
- 实时性要求高

---

### Qt GUI版本目录 (service_qt/)
**作用**: 图形界面版本

**核心文件**:
- `run_gui.py` - GUI启动入口
- `main_window.py` - 主窗口
- `widgets.py` - 自定义控件
- `dialogs.py` - 对话框
- `styles.py` - 样式定义

**特点**:
- ✅ 海康威视风格
- ✅ 实时图像显示
- ✅ 参数可视化配置
- ✅ 检测结果可视化
- ✅ 性能监控面板

**适用场景**:
- 需要图形界面
- 参数调试
- 演示展示

---

### 文档目录 (docs_*)

#### docs_core/ - 核心文档
**内容**: 核心系统的所有文档
- 快速入门文档（3个）
- 系统设计文档（3个）
- 开发文档（5个）

#### docs_asyncio/ - 异步文档
**内容**: 异步版本的所有文档
- 核心文档（1个）
- 开发文档（3个）

#### docs_qt/ - Qt文档
**内容**: Qt GUI版本的所有文档
- 核心文档（2个）
- 开发文档（1个）

**特点**:
- ✅ 按功能分类
- ✅ 独立的索引文件
- ✅ 清晰的导航
- ✅ 完整的说明

---

### 测试目录 (tests_*)

#### tests_core/ - 核心测试
**内容**: 核心系统测试
- 导入测试
- 系统功能测试
- 批处理测试脚本

#### tests_asyncio/ - 异步测试
**状态**: 待创建
**计划**: 异步功能测试、性能测试

#### tests_qt/ - Qt测试
**内容**: Qt GUI测试
- Qt导入测试
- GUI启动测试
- 批处理测试脚本

**特点**:
- ✅ 按版本分类
- ✅ 独立的测试环境
- ✅ 批处理脚本支持
- ✅ 详细的测试说明

---

## 🎯 文件组织原则

### 1. 按功能分类
- 核心代码在根目录
- 文档按版本分类到 docs_* 目录
- 测试按版本分类到 tests_* 目录

### 2. 独立性
- 每个版本可以独立运行
- 每个文档目录有独立索引
- 每个测试目录有独立说明

### 3. 清晰性
- 使用描述性的目录名
- 使用中文命名（除代码外）
- 提供完整的索引和导航

### 4. 可维护性
- 统一的命名规范
- 清晰的目录结构
- 完整的文档说明

---

## 📝 文件命名规范

### Python代码文件
- 使用小写字母和下划线
- 例如: `camera_service.py`, `main_async.py`

### 文档文件
- 使用中文描述性名称
- 使用.md扩展名
- 例如: `快速启动指南.md`, `系统架构说明.md`

### 批处理文件
- 使用中文描述性名称
- 使用.bat扩展名
- 例如: `启动同步版本.bat`, `测试导入.bat`

### 索引文件
- 统一命名为 `README_INDEX.md`
- 放在每个文档/测试目录中

---

## 🔄 目录维护

### 添加新文档
1. 确定文档类型（核心/异步/Qt）
2. 放入对应的 docs_* 目录
3. 更新该目录的 README_INDEX.md
4. 更新 DOCUMENTATION_INDEX.md

### 添加新测试
1. 确定测试类型（核心/异步/Qt）
2. 放入对应的 tests_* 目录
3. 更新该目录的 README_INDEX.md
4. 创建对应的批处理脚本

### 添加新功能
1. 在对应目录添加代码文件
2. 在 docs_* 添加说明文档
3. 在 tests_* 添加测试文件
4. 更新相关索引文件

---

## 📊 统计信息

### 代码文件
- 核心模块: 5个
- 微服务: 6个
- 异步版本: 5个
- Qt GUI: 5个
- **总计**: 21个

### 文档文件
- 核心文档: 11个
- 异步文档: 4个
- Qt文档: 3个
- **总计**: 18个

### 测试文件
- 核心测试: 3个
- 异步测试: 0个（待创建）
- Qt测试: 3个
- **总计**: 6个

### 批处理脚本
- 启动脚本: 5个
- 测试脚本: 3个
- 工具脚本: 3个
- **总计**: 11个

---

## 🔗 快速导航

- **文档总索引**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- **核心文档**: [docs_core/README_INDEX.md](docs_core/README_INDEX.md)
- **异步文档**: [docs_asyncio/README_INDEX.md](docs_asyncio/README_INDEX.md)
- **Qt文档**: [docs_qt/README_INDEX.md](docs_qt/README_INDEX.md)
- **核心测试**: [tests_core/README_INDEX.md](tests_core/README_INDEX.md)
- **异步测试**: [tests_asyncio/README_INDEX.md](tests_asyncio/README_INDEX.md)
- **Qt测试**: [tests_qt/README_INDEX.md](tests_qt/README_INDEX.md)

---

**最后更新**: 2026-01-29
**维护者**: Kiro AI Assistant
