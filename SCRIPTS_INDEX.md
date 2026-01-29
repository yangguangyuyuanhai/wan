# Service_new 批处理脚本总索引

本文档提供 service_new 项目所有批处理脚本的导航。

## 📁 脚本目录结构

```
service_new/
├── scripts_core/          # 核心系统启动脚本
├── scripts_asyncio/       # 异步版本启动脚本
├── scripts_qt/            # Qt GUI启动脚本
├── scripts_utils/         # 工具和辅助脚本
├── tests_core/            # 核心测试脚本
├── tests_asyncio/         # 异步测试脚本
└── tests_qt/              # Qt测试脚本
```

## 🚀 快速启动

### 推荐方式：使用一键启动菜单
```bash
# 双击运行
scripts_utils/一键启动所有版本.bat

# 会显示交互式菜单，选择要启动的版本
```

### 直接启动特定版本
```bash
# Qt GUI版本（推荐）
scripts_qt/启动GUI.bat

# 同步版本（命令行）
scripts_core/启动同步版本.bat

# 异步版本（多相机）
scripts_asyncio/启动异步版本.bat
```

## 📜 脚本分类导航

### 核心系统脚本 (scripts_core/)
**用途**: 启动核心同步版本系统

**脚本列表**:
- `启动同步版本.bat` - 启动同步版本

**适用场景**:
- 单相机采集
- 简单图像处理
- 开发和调试

📋 [查看详细索引](scripts_core/README_INDEX.md)

---

### 异步版本脚本 (scripts_asyncio/)
**用途**: 启动异步多相机并发系统

**脚本列表**:
- `启动异步版本.bat` - 启动异步版本

**适用场景**:
- 多相机同时采集
- 高并发处理
- 实时性要求高

📋 [查看详细索引](scripts_asyncio/README_INDEX.md)

---

### Qt GUI脚本 (scripts_qt/)
**用途**: 启动图形界面版本

**脚本列表**:
- `启动GUI.bat` - 启动Qt GUI

**适用场景**:
- 需要图形界面
- 参数可视化配置
- 演示和展示

📋 [查看详细索引](scripts_qt/README_INDEX.md)

---

### 工具脚本 (scripts_utils/)
**用途**: 系统工具和辅助功能

**脚本列表**:
- `一键启动所有版本.bat` - 交互式启动菜单 ⭐
- `检查环境.bat` - 检查系统环境
- `安装依赖.bat` - 安装项目依赖
- `快速测试.bat` - 快速系统测试

**推荐使用**:
- ⭐ 首次使用先运行 `检查环境.bat`
- ⭐ 然后运行 `安装依赖.bat`
- ⭐ 日常使用 `一键启动所有版本.bat`

📋 [查看详细索引](scripts_utils/README_INDEX.md)

---

### 测试脚本

#### 核心测试 (tests_core/)
- `测试导入.bat` - 模块导入测试

#### Qt测试 (tests_qt/)
- `测试Qt版本.bat` - Qt GUI测试

#### 异步测试 (tests_asyncio/)
- 待添加

---

## 🎯 使用场景指南

### 场景1：首次使用系统
```bash
1. scripts_utils/检查环境.bat      # 检查环境
2. scripts_utils/安装依赖.bat      # 安装依赖
3. scripts_utils/快速测试.bat      # 验证安装
4. scripts_utils/一键启动所有版本.bat  # 启动系统
```

### 场景2：日常开发
```bash
# 使用一键启动菜单
scripts_utils/一键启动所有版本.bat

# 或直接启动需要的版本
scripts_core/启动同步版本.bat
```

### 场景3：演示展示
```bash
# 启动Qt GUI界面
scripts_qt/启动GUI.bat
```

### 场景4：多相机采集
```bash
# 启动异步版本
scripts_asyncio/启动异步版本.bat
```

### 场景5：问题排查
```bash
1. scripts_utils/检查环境.bat      # 检查环境
2. scripts_utils/快速测试.bat      # 运行测试
3. 查看日志文件分析问题
```

## 📊 脚本统计

### 启动脚本
- 核心启动: 1个
- 异步启动: 1个
- Qt启动: 1个
- **小计**: 3个

### 工具脚本
- 一键启动: 1个
- 环境工具: 2个
- 测试工具: 1个
- **小计**: 4个

### 测试脚本
- 核心测试: 1个
- Qt测试: 1个
- 异步测试: 0个（待添加）
- **小计**: 2个

### 总计
**9个批处理脚本**

## 🔧 脚本自定义

### 修改conda环境
所有脚本中查找并修改：
```batch
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio
```
改为：
```batch
C:\Users\YRQ\miniconda3\_conda.exe run -n 你的环境名
```

### 添加启动参数
在启动脚本中添加参数：
```batch
REM 开发模式
python main.py --mode development

REM 生产模式
python main.py --mode production

REM 自定义参数
python main.py --exposure 15000 --gain 12.0
```

### 修改工作目录
脚本使用 `%~dp0` 获取脚本所在目录：
```batch
REM 切换到service_new根目录
cd /d %~dp0..

REM 切换到service_asyncio目录
cd /d %~dp0..\service_asyncio
```

## 🐛 常见问题

### 问题1：找不到conda命令
**原因**: conda未安装或路径不正确

**解决**:
1. 检查conda安装路径
2. 修改脚本中的conda路径
3. 或手动激活环境后运行Python脚本

### 问题2：找不到Python模块
**原因**: 依赖未安装或环境未激活

**解决**:
1. 运行 `scripts_utils/检查环境.bat`
2. 运行 `scripts_utils/安装依赖.bat`
3. 确认环境已正确激活

### 问题3：相机打开失败
**原因**: 相机未连接或SDK未配置

**解决**:
1. 检查相机连接
2. 检查SDK安装
3. 检查环境变量MVCAM_COMMON_RUNENV

### 问题4：Qt界面无法启动
**原因**: PyQt5未安装

**解决**:
```bash
pip install PyQt5
# 或
conda install pyqt
```

## 💡 最佳实践

### 开发环境
1. 使用 `scripts_core/启动同步版本.bat`
2. 便于调试和开发
3. 日志输出到控制台

### 生产环境
1. 修改脚本使用生产模式
2. 禁用不必要的日志
3. 启用图像保存

### 演示环境
1. 使用 `scripts_qt/启动GUI.bat`
2. 图形界面更直观
3. 便于参数调整

## 📝 脚本维护规范

### 命名规范
- 使用中文描述性名称
- 使用.bat扩展名
- 例如: `启动同步版本.bat`

### 代码规范
- 使用UTF-8编码（chcp 65001）
- 包含清晰的注释
- 处理错误情况
- 提供用户反馈

### 目录规范
- 启动脚本 → scripts_*/
- 测试脚本 → tests_*/
- 工具脚本 → scripts_utils/

### 文档规范
- 每个目录有README_INDEX.md
- 说明脚本用途和使用方法
- 包含故障排除指南

## 🔗 相关文档

- **文档总索引**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- **项目结构**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **核心文档**: [docs_core/README_INDEX.md](docs_core/README_INDEX.md)
- **异步文档**: [docs_asyncio/README_INDEX.md](docs_asyncio/README_INDEX.md)
- **Qt文档**: [docs_qt/README_INDEX.md](docs_qt/README_INDEX.md)

## 🔄 更新记录

### 2026-01-29
- ✅ 创建脚本目录结构
- ✅ 整理所有批处理脚本
- ✅ 创建各目录索引文件
- ✅ 创建脚本总索引
- ✅ 更新脚本路径引用

---

**最后更新**: 2026-01-29
**维护者**: Kiro AI Assistant
