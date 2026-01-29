# 核心系统批处理脚本索引

本目录包含核心系统（同步版本）的所有批处理脚本。

## 📜 脚本列表

### 启动脚本
- **启动同步版本.bat** - 启动核心同步版本系统
  - 自动激活conda环境
  - 运行main.py
  - 显示运行日志

## 🚀 使用方法

### 启动同步版本
```bash
# 方法1：直接双击
启动同步版本.bat

# 方法2：命令行运行
cd scripts_core
启动同步版本.bat
```

## 📝 脚本说明

### 启动同步版本.bat
**功能**: 启动核心同步版本系统

**执行流程**:
1. 激活conda环境（label_studio）
2. 切换到service_new根目录
3. 运行 `python main.py`
4. 显示系统运行日志
5. 等待用户按键退出

**适用场景**:
- 单相机采集
- 简单图像处理
- 开发和调试
- 学习和演示

**环境要求**:
- Python 3.7+
- conda环境已配置
- 依赖包已安装

## 🔧 自定义参数

可以修改脚本添加命令行参数：

```batch
REM 开发模式
python main.py --mode development

REM 生产模式
python main.py --mode production

REM 自定义参数
python main.py --exposure 15000 --gain 12.0

REM 禁用显示
python main.py --no-display

REM 启用图像保存
python main.py --save-images
```

## 📂 相关目录

- **源代码**: ../
- **文档**: ../docs_core/
- **测试**: ../tests_core/
- **异步脚本**: ../scripts_asyncio/
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

### 修改Python路径
如果Python不在PATH中，使用完整路径：
```batch
C:\Python39\python.exe main.py
```

### 添加日志输出
重定向输出到日志文件：
```batch
python main.py > logs\startup.log 2>&1
```

## 🐛 故障排除

### 问题1：找不到conda命令
**解决**: 检查conda安装路径，修改脚本中的activate.bat路径

### 问题2：找不到Python
**解决**: 确保conda环境已激活，或使用完整Python路径

### 问题3：模块导入错误
**解决**: 运行 `../scripts_utils/安装依赖.bat` 安装依赖

### 问题4：相机打开失败
**解决**: 
- 检查相机是否连接
- 检查SDK是否安装
- 检查环境变量MVCAM_COMMON_RUNENV

## 📝 文档维护

- 所有核心系统批处理脚本都应放在此目录
- 脚本应包含清晰的注释
- 脚本应处理错误情况
- 脚本应提供用户反馈
