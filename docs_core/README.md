# 工业视觉系统 - 管道-过滤器架构

> 基于微服务设计的工业相机图像采集与处理系统

## 🎯 项目简介

这是一个完整的工业视觉系统，采用**管道-过滤器架构**和**微服务设计模式**，实现了从相机图像采集到YOLO目标检测、OpenCV图像处理、实时显示和数据存储的完整流程。

### 核心特性

- ✅ **管道-过滤器架构** - 模块化、可扩展、易维护
- ✅ **微服务设计** - 每个功能独立服务，松耦合
- ✅ **异步处理** - 高性能并发处理
- ✅ **配置化管理** - 灵活的参数配置系统
- ✅ **完整日志** - 多级别、多输出的日志系统
- ✅ **性能监控** - 实时性能统计和分析
- ✅ **上帝类设计** - 统一的系统管理入口

---

## 📁 项目结构

```
F:\MVS\
├── main.py                    # 主程序（上帝类）
├── scheduler.py               # 调度器
├── pipeline_core.py           # 管道核心
├── pipeline_config.py         # 配置管理
├── logger_config.py           # 日志模块
├── requirements.txt           # 依赖列表
│
├── services/                  # 微服务目录
│   ├── __init__.py
│   ├── camera_service.py      # 相机采集服务
│   ├── preprocess_service.py  # 图像预处理服务
│   ├── yolo_service.py        # YOLO检测服务
│   ├── opencv_service.py      # OpenCV处理服务
│   ├── display_service.py     # 图像显示服务
│   └── storage_service.py     # 数据存储服务
│
├── logs/                      # 日志目录（自动创建）
│   ├── CameraApp_detail.log
│   ├── CameraApp_error.log
│   └── CameraApp_daily.log
│
├── output/                    # 输出目录（自动创建）
│   ├── images/                # 保存的图像
│   └── detections.json        # 检测结果
│
├── models/                    # 模型目录
│   └── yolov8n.pt            # YOLO模型
│
└── docs/                      # 文档目录
    ├── 系统架构说明.md
    ├── 快速开始.md
    └── 二次开发指南.md
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量（Windows）

```cmd
setx MVCAM_COMMON_RUNENV "F:\MVS"
```

### 3. 运行系统

```bash
# 开发模式（默认）
python main.py

# 生产模式
python main.py --mode production

# 调试模式
python main.py --mode debug
```

### 4. 自定义参数

```bash
# 设置相机参数
python main.py --exposure 15000 --gain 12.0

# 设置YOLO参数
python main.py --yolo-model ./models/yolov8n.pt --confidence 0.6

# 禁用显示
python main.py --no-display

# 启用图像保存
python main.py --save-images
```

---

## 🏗️ 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         Main.py                              │
│                        (上帝类)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Scheduler (调度器)                      │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │           Pipeline (管道)                      │  │   │
│  │  │                                                 │  │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │  │   │
│  │  │  │ Camera   │→ │Preprocess│→ │  YOLO    │    │  │   │
│  │  │  │ Service  │  │ Service  │  │ Service  │    │  │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘    │  │   │
│  │  │       ↓              ↓              ↓         │  │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │  │   │
│  │  │  │ OpenCV   │→ │ Display  │→ │ Storage  │    │  │   │
│  │  │  │ Service  │  │ Service  │  │ Service  │    │  │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘    │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
相机采集 → 预处理 → YOLO检测 → OpenCV处理 → 显示 → 存储
```

---

## 📦 微服务说明

### 1. Camera Service - 相机采集服务
- 枚举和打开工业相机
- 配置相机参数（曝光、增益、帧率）
- 持续采集图像帧

### 2. Preprocess Service - 图像预处理服务
- 图像格式转换（Mono8 → BGR）
- 图像调整大小
- 降噪、锐化
- 亮度/对比度调整

### 3. YOLO Service - 目标检测服务
- 加载YOLO模型（YOLOv5/YOLOv8）
- 目标检测和识别
- 结果解析和过滤

### 4. OpenCV Service - 图像处理服务
- 边缘检测（Canny）
- 轮廓检测
- 形态学操作
- 特征提取

### 5. Display Service - 显示服务
- 实时图像显示
- 绘制检测框和标签
- 显示FPS、帧号等信息
- 按键交互

### 6. Storage Service - 存储服务
- 保存图像（JPG/PNG/BMP）
- 保存检测结果（JSON）
- 按条件保存（间隔/检测到目标）

---

## ⚙️ 配置说明

### 运行模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **development** | 详细日志、启用显示 | 开发调试 |
| **production** | 精简日志、禁用显示、启用保存 | 生产部署 |
| **debug** | 最详细日志、限制帧数 | 问题排查 |

### 主要配置

```python
# 相机配置
exposure_time = 10000      # 曝光时间（微秒）
gain = 10.0                # 增益（dB）
frame_rate = 30.0          # 帧率（fps）

# YOLO配置
model_path = "./models/yolov8n.pt"
confidence_threshold = 0.5
device = "cpu"             # cpu/cuda

# 显示配置
show_fps = True
show_detections = True
display_fps_limit = 30

# 存储配置
save_images = True
save_on_detection = True
save_format = "jpg"
```

---

## 📊 性能监控

系统会定期输出性能统计：

```
==================================================
管道统计: VisionPipeline
==================================================
运行状态: 运行中
输入队列: 2
输出队列: 1

过滤器统计:

  [PreprocessService]
    处理帧数: 1000
    平均耗时: 5.23ms
    错误率: 0.00%

  [YOLOService]
    处理帧数: 1000
    平均耗时: 45.67ms
    错误率: 0.20%
==================================================
```

---

## 📝 日志系统

### 日志文件

- `CameraApp_detail.log` - 所有日志（DEBUG级别）
- `CameraApp_error.log` - 仅错误日志
- `CameraApp_daily.log` - 按日期轮转（保留30天）

### 日志级别

- **DEBUG** - 详细调试信息
- **INFO** - 一般信息
- **WARNING** - 警告信息
- **ERROR** - 错误信息
- **CRITICAL** - 严重错误

---

## 🔧 开发指南

### 添加新的过滤器

1. 创建服务类（继承Filter）
2. 实现process方法
3. 添加配置类
4. 在scheduler中注册

详见：`系统架构说明.md`

---

## 📚 文档

- **快速开始.md** - 5分钟快速上手
- **系统架构说明.md** - 完整架构文档
- **二次开发指南.md** - 开发指南

---

## 🐛 故障排查

### 常见问题

1. **找不到相机** - 检查连接、驱动、环境变量
2. **YOLO加载失败** - 检查模型文件、安装ultralytics
3. **显示无响应** - 按q键退出或使用--no-display
4. **帧率低** - 禁用YOLO或减小图像分辨率

详见：`快速开始.md`

---

## 📦 依赖

### 必需
- Python 3.6+
- numpy
- opencv-python

### 可选
- ultralytics（YOLOv8）
- torch + torchvision（YOLOv5）

---

## 🎯 使用场景

### 工业检测
- 产品缺陷检测
- 尺寸测量
- 质量控制

### 目标识别
- 物体识别
- 人员检测
- 车辆识别

### 图像处理
- 边缘检测
- 轮廓提取
- 特征分析

---

## 📞 技术支持

### 查看文档
- 系统架构说明.md
- 快速开始.md
- 二次开发指南.md

### 查看日志
```bash
type logs\CameraApp_detail.log
```

### 获取帮助
```bash
python main.py --help
```

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 👨‍💻 作者

Kiro AI Assistant

---

## 🎉 开始使用

```bash
# 克隆或下载项目
cd F:\MVS

# 安装依赖
pip install -r requirements.txt

# 运行系统
python main.py

# 查看帮助
python main.py --help
```

**祝你使用愉快！** 🚀
