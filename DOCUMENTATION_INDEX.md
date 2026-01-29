# Service_new 文档和测试总索引

本文档提供 service_new 项目所有文档和测试文件的导航。

## 📚 文档目录结构

```
service_new/
├── docs_core/          # 核心系统文档
├── docs_asyncio/       # 异步版本文档
├── docs_qt/            # Qt GUI版本文档
├── tests_core/         # 核心系统测试
├── tests_asyncio/      # 异步版本测试
└── tests_qt/           # Qt GUI版本测试
```

## 📖 文档导航

### 核心系统文档 (docs_core/)
**快速入门**
- [README.md](docs_core/README.md) - 项目总览
- [快速启动指南.md](docs_core/快速启动指南.md) - 5分钟快速上手
- [快速开始.md](docs_core/快速开始.md) - 详细快速开始

**系统文档**
- [系统架构说明.md](docs_core/系统架构说明.md) - 完整架构设计
- [开始使用_最终版.md](docs_core/开始使用_最终版.md) - 完整使用指南
- [项目总结.md](docs_core/项目总结.md) - 功能总结

**配置和脚本**
- [启动脚本说明.md](docs_core/启动脚本说明.md) - 启动脚本使用
- [启动脚本创建完成.md](docs_core/启动脚本创建完成.md) - 脚本创建记录

**开发文档**
- [组织完成说明.md](docs_core/组织完成说明.md) - 项目组织结构
- [依赖修复完成报告.txt](docs_core/依赖修复完成报告.txt) - 依赖修复报告
- [测试报告.md](docs_core/测试报告.md) - 系统测试报告

📋 [查看完整索引](docs_core/README_INDEX.md)

---

### 异步版本文档 (docs_asyncio/)
**核心文档**
- [README_ASYNCIO.md](docs_asyncio/README_ASYNCIO.md) - 异步版本完整说明
- [异步版本说明.md](docs_asyncio/异步版本说明.md) - 开发说明

**开发文档**
- [依赖关系说明.md](docs_asyncio/依赖关系说明.md) - 依赖关系详解
- [目录清理说明.md](docs_asyncio/目录清理说明.md) - 目录结构说明

**特性**
- ✅ 多相机并发采集
- ✅ 异步管道处理
- ✅ 高性能并发
- ✅ 自动负载均衡

📋 [查看完整索引](docs_asyncio/README_INDEX.md)

---

### Qt GUI版本文档 (docs_qt/)
**核心文档**
- [README.md](docs_qt/README.md) - Qt版本总览
- [快速开始.md](docs_qt/快速开始.md) - 快速开始指南

**开发文档**
- [Qt界面开发说明.md](docs_qt/Qt界面开发说明.md) - 界面开发详解

**特性**
- ✅ 海康威视风格界面
- ✅ 实时图像显示
- ✅ 参数可视化配置
- ✅ 检测结果可视化
- ✅ 性能监控面板

📋 [查看完整索引](docs_qt/README_INDEX.md)

---

## 🧪 测试导航

### 核心系统测试 (tests_core/)
**测试文件**
- [test_imports.py](tests_core/test_imports.py) - 模块导入测试
- [test_system.py](tests_core/test_system.py) - 系统功能测试
- [测试导入.bat](tests_core/测试导入.bat) - 批处理测试脚本

**测试覆盖**
- ✅ 模块导入测试
- ✅ 管道核心功能
- ✅ 过滤器执行
- ✅ 数据包处理

📋 [查看完整索引](tests_core/README_INDEX.md)

---

### 异步版本测试 (tests_asyncio/)
**状态**: 测试文件待创建

**计划测试**
- ⏳ 异步管道测试
- ⏳ 多相机管理测试
- ⏳ 异步服务测试
- ⏳ 性能基准测试

📋 [查看完整索引](tests_asyncio/README_INDEX.md)

---

### Qt GUI测试 (tests_qt/)
**测试文件**
- [test_qt.py](tests_qt/test_qt.py) - Qt模块导入测试
- [test_gui_startup.py](tests_qt/test_gui_startup.py) - GUI启动测试

**测试覆盖**
- ✅ PyQt5导入测试
- ✅ 主窗口创建测试
- ✅ 启动流程测试

**计划测试**
- ⏳ 界面交互测试
- ⏳ 控件功能测试
- ⏳ 对话框测试

📋 [查看完整索引](tests_qt/README_INDEX.md)

---

## 🎯 快速导航

### 我是新手，想快速上手
1. 阅读 [docs_core/README.md](docs_core/README.md)
2. 阅读 [docs_core/快速启动指南.md](docs_core/快速启动指南.md)
3. 运行 `启动同步版本.bat`

### 我想了解系统架构
1. 阅读 [docs_core/系统架构说明.md](docs_core/系统架构说明.md)
2. 阅读 [docs_core/项目总结.md](docs_core/项目总结.md)
3. 查看源代码注释

### 我想使用异步版本
1. 阅读 [docs_asyncio/README_ASYNCIO.md](docs_asyncio/README_ASYNCIO.md)
2. 进入 `service_asyncio/` 目录
3. 运行 `启动异步版本.bat`

### 我想使用Qt GUI版本
1. 阅读 [docs_qt/README.md](docs_qt/README.md)
2. 阅读 [docs_qt/快速开始.md](docs_qt/快速开始.md)
3. 进入 `service_qt/` 目录
4. 运行 `启动GUI.bat`

### 我想运行测试
1. 核心测试: `cd tests_core && python test_imports.py`
2. Qt测试: `cd tests_qt && python test_qt.py`
3. 或使用批处理: `tests_core/测试导入.bat`

### 我想开发新功能
1. 阅读 [docs_core/系统架构说明.md](docs_core/系统架构说明.md)
2. 阅读 [docs_core/组织完成说明.md](docs_core/组织完成说明.md)
3. 查看相关模块源代码
4. 编写测试用例

---

## 📊 文档统计

### 核心文档
- 总文档数: 11个
- 快速入门: 3个
- 系统文档: 3个
- 开发文档: 5个

### 异步文档
- 总文档数: 4个
- 核心文档: 1个
- 开发文档: 3个

### Qt文档
- 总文档数: 3个
- 核心文档: 2个
- 开发文档: 1个

### 测试文件
- 核心测试: 3个
- 异步测试: 0个（待创建）
- Qt测试: 2个

---

## 🔄 文档更新记录

### 2026-01-29
- ✅ 创建文档目录结构
- ✅ 整理所有文档到对应目录
- ✅ 创建各目录索引文件
- ✅ 创建总索引文件
- ✅ 整理测试文件到对应目录

---

## 📝 文档维护规范

### 文档命名规范
- 使用中文命名（除README外）
- 使用.md扩展名
- 使用描述性名称

### 文档组织规范
- 核心系统文档 → docs_core/
- 异步版本文档 → docs_asyncio/
- Qt GUI文档 → docs_qt/
- 核心测试 → tests_core/
- 异步测试 → tests_asyncio/
- Qt测试 → tests_qt/

### 文档内容规范
- 包含清晰的标题和目录
- 包含代码示例
- 包含使用说明
- 及时更新

### 索引文件维护
- 每个目录都有README_INDEX.md
- 索引文件列出所有文档
- 索引文件提供导航链接
- 索引文件说明文档用途

---

## 🔗 相关链接

- **项目根目录**: [service_new/](.)
- **源代码**: 
  - 核心系统: [./](.)
  - 异步版本: [service_asyncio/](service_asyncio/)
  - Qt GUI: [service_qt/](service_qt/)
- **依赖文件**: [requirements.txt](requirements.txt)
- **配置文件**: [pipeline_config.py](pipeline_config.py)

---

## 📧 反馈和建议

如果您发现文档有任何问题或有改进建议，请：
1. 查看相关文档的索引文件
2. 检查文档是否已更新
3. 提出具体的改进建议

---

**最后更新**: 2026-01-29
**维护者**: Kiro AI Assistant
