# 异步版本批处理脚本索引

本目录包含异步版本（多相机并发）的所有批处理脚本。

## 📜 脚本列表

### 启动脚本
- **启动异步版本.bat** - 启动异步多相机并发系统
  - 自动激活conda环境
  - 切换到service_asyncio目录
  - 运行main_async.py
  - 显示运行日志

## 🚀 使用方法

### 启动异步版本
```bash
# 方法1：直接双击
启动异步版本.bat

# 方法2：命令行运行
cd scripts_asyncio
启动异步版本.bat

# 方法3：从根目录运行
cd service_new
scripts_asyncio\启动异步版本.bat
```

## 📝 脚本说明

### 启动异步版本.bat
**功能**: 启动异步多相机并发处理系统

**执行流程**:
1. 激活conda环境（label_studio）
2. 切换到service_asyncio目录
3. 运行 `python main_async.py`
4. 显示系统运行日志
5. 等待用户按键退出

**适用场景**:
- 多相机同时采集
- 高并发图像处理
- 实时性要求高的场景
- 需要充分利用多核CPU

**环境要求**:
- Python 3.7+ (支持asyncio)
- conda环境已配置
- 依赖包已安装
- 多个相机设备（可选）

## 🔧 自定义参数

可以修改脚本添加命令行参数：

```batch
REM 开发模式
python main_async.py --mode development

REM 生产模式
python main_async.py --mode production

REM 自定义参数
python main_async.py --exposure 15000 --gain 12.0

REM 禁用显示
python main_async.py --no-display

REM 启用图像保存
python main_async.py --save-images
```

## 📊 异步版本特性

### 核心优势
- ✅ 支持多相机并发采集
- ✅ 基于asyncio的异步处理
- ✅ 高性能并发管道
- ✅ 自动负载均衡
- ✅ 非阻塞I/O操作

### 性能对比
- 单相机: 与同步版本性能相当
- 多相机: 性能显著提升（接近线性扩展）
- CPU利用率: 更高的多核利用率
- 吞吐量: 多相机场景下提升2-4倍

## 📂 相关目录

- **源代码**: ../service_asyncio/
- **文档**: ../docs_asyncio/
- **测试**: ../tests_asyncio/
- **核心脚本**: ../scripts_core/
- **Qt脚本**: ../scripts_qt/
- **工具脚本**: ../scripts_utils/

## 🔗 相关脚本

- **一键启动**: ../scripts_utils/一键启动所有版本.bat
- **快速测试**: ../scripts_utils/快速测试.bat
- **环境检查**: ../scripts_utils/检查环境.bat

## 📝 脚本维护

### 修改conda环境
如果使用不同的conda环境，修改脚本中的环境名称：
```batch
call C:\Users\YRQ\miniconda3\Scripts\activate.bat 你的环境名
```

### 修改工作目录
如果需要从不同位置运行，修改脚本中的目录切换：
```batch
cd /d %~dp0..\service_asyncio
```

### 添加性能监控
添加性能监控参数：
```batch
python main_async.py --enable-profiling
```

## 🐛 故障排除

### 问题1：找不到asyncio模块
**解决**: 确保Python版本 >= 3.7

### 问题2：多相机冲突
**解决**: 
- 检查相机是否被其他程序占用
- 确保每个相机有独立的IP（GigE相机）
- 检查USB带宽是否足够（USB相机）

### 问题3：性能不如预期
**解决**:
- 检查CPU核心数
- 调整并发数量
- 优化图像处理参数
- 使用性能分析工具

### 问题4：内存占用过高
**解决**:
- 减少缓冲区大小
- 降低图像分辨率
- 限制并发相机数量

## 💡 使用建议

### 单相机场景
- 使用同步版本即可
- 异步版本无明显优势

### 2-4个相机
- 推荐使用异步版本
- 性能提升明显

### 5个以上相机
- 必须使用异步版本
- 注意系统资源限制
- 考虑分布式部署

## 📝 文档维护

- 所有异步版本批处理脚本都应放在此目录
- 脚本应包含清晰的注释
- 脚本应处理错误情况
- 脚本应提供性能提示
