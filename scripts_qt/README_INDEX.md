# Qt GUI批处理脚本索引

本目录包含Qt图形界面版本的所有批处理脚本。

## 📜 脚本列表

### 启动脚本
- **启动GUI.bat** - 启动Qt图形界面
  - 自动激活conda环境
  - 切换到service_qt目录
  - 运行run_gui.py
  - 显示启动画面
  - 打开主窗口

## 🚀 使用方法

### 启动Qt GUI
```bash
# 方法1：直接双击
启动GUI.bat

# 方法2：命令行运行
cd scripts_qt
启动GUI.bat

# 方法3：从根目录运行
cd service_new
scripts_qt\启动GUI.bat
```

## 📝 脚本说明

### 启动GUI.bat
**功能**: 启动Qt图形界面版本

**执行流程**:
1. 激活conda环境（label_studio）
2. 切换到service_qt目录
3. 运行 `python run_gui.py`
4. 显示启动画面（2秒）
5. 打开主窗口
6. 等待用户关闭窗口

**适用场景**:
- 需要图形界面操作
- 参数可视化配置
- 实时图像显示
- 演示和展示
- 非技术人员使用

**环境要求**:
- Python 3.7+
- PyQt5已安装
- conda环境已配置
- 依赖包已安装

## 🎨 Qt GUI特性

### 界面功能
- ✅ 海康威视风格界面
- ✅ 实时图像显示
- ✅ 参数可视化配置
- ✅ 检测结果可视化
- ✅ 性能监控面板
- ✅ 日志查看器

### 主要组件
- 相机控制面板
- 图像显示窗口
- 参数配置对话框
- 检测结果列表
- 性能监控图表
- 日志输出窗口

## 🔧 自定义配置

### 修改窗口大小
编辑 `service_qt/main_window.py`:
```python
self.resize(1280, 720)  # 修改为你需要的尺寸
```

### 修改界面风格
编辑 `service_qt/styles.py`:
```python
# 修改颜色主题
PRIMARY_COLOR = "#00D9FF"
BACKGROUND_COLOR = "#1E1E1E"
```

### 禁用启动画面
修改脚本，添加参数：
```batch
python run_gui.py --no-splash
```

## 📂 相关目录

- **源代码**: ../service_qt/
- **文档**: ../docs_qt/
- **测试**: ../tests_qt/
- **核心脚本**: ../scripts_core/
- **异步脚本**: ../scripts_asyncio/
- **工具脚本**: ../scripts_utils/

## 🔗 相关脚本

- **一键启动**: ../scripts_utils/一键启动所有版本.bat
- **环境检查**: ../scripts_utils/检查环境.bat
- **安装依赖**: ../scripts_utils/安装依赖.bat

## 📝 脚本维护

### 修改conda环境
如果使用不同的conda环境，修改脚本中的环境名称：
```batch
call C:\Users\YRQ\miniconda3\Scripts\activate.bat 你的环境名
```

### 修改工作目录
如果需要从不同位置运行，修改脚本中的目录切换：
```batch
cd /d %~dp0..\service_qt
```

### 添加调试模式
添加调试参数：
```batch
python run_gui.py --debug
```

## 🐛 故障排除

### 问题1：找不到PyQt5
**解决**: 
```bash
pip install PyQt5
# 或
conda install pyqt
```

### 问题2：界面显示异常
**解决**:
- 检查显示器分辨率
- 检查DPI缩放设置
- 尝试不同的Qt样式

### 问题3：图像显示卡顿
**解决**:
- 降低显示帧率
- 减小显示窗口大小
- 关闭不必要的特效

### 问题4：启动画面不显示
**解决**:
- 检查图像资源文件
- 检查Qt版本兼容性
- 查看错误日志

## 💡 使用技巧

### 快捷键
- `Ctrl+O` - 打开相机
- `Ctrl+S` - 保存配置
- `Ctrl+Q` - 退出程序
- `F11` - 全屏模式

### 界面布局
- 可拖动面板调整大小
- 可隐藏/显示各个面板
- 支持保存布局配置

### 参数配置
- 实时预览参数效果
- 支持参数模板保存
- 支持批量参数导入

## 📊 性能优化

### 显示优化
- 限制显示帧率（默认30fps）
- 使用硬件加速
- 减少不必要的重绘

### 内存优化
- 及时释放图像缓存
- 限制历史记录数量
- 定期清理日志

## 📝 文档维护

- 所有Qt GUI批处理脚本都应放在此目录
- 脚本应包含清晰的注释
- 脚本应处理错误情况
- 脚本应提供用户友好的提示
