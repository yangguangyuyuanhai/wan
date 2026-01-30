# 用户手册

**版本**: 1.0.0  
**更新时间**: 2026-01-30

## 快速开始

### 安装

```bash
cd /home/fengze/yolo919/MVS/service_DAG

# 安装依赖
pip install -r requirements.txt

# 验证安装
python quick_verify.py
```

### 运行系统

```bash
# 使用默认配置
python main_optimized.py

# 指定配置文件
python main_optimized.py --config config/milestone3_pipeline.json

# 设置日志级别
python main_optimized.py --log-level DEBUG
```

## 配置流水线

### 配置文件格式

```json
{
  "name": "my_pipeline",
  "version": "1.0.0",
  "description": "我的视觉处理流水线",
  "nodes": [
    {
      "id": "camera",
      "type": "camera_hik",
      "config": {
        "exposure_time": 10000,
        "gain": 10.0,
        "frame_rate": 30.0
      }
    },
    {
      "id": "display",
      "type": "display",
      "config": {
        "window_name": "Camera View",
        "show_fps": true
      }
    }
  ],
  "connections": [
    {
      "from_node": "camera",
      "from_port": "image",
      "to_node": "display",
      "to_port": "image"
    }
  ]
}
```

### 可用节点类型

#### 1. camera_hik - 海康相机采集
```json
{
  "type": "camera_hik",
  "config": {
    "exposure_time": 10000,    // 曝光时间（微秒）
    "gain": 10.0,              // 增益（dB）
    "frame_rate": 30.0,        // 帧率
    "trigger_mode": false      // 触发模式
  }
}
```

#### 2. preprocess - 图像预处理
```json
{
  "type": "preprocess",
  "config": {
    "convert_to_bgr": true,
    "resize_enabled": true,
    "resize_width": 640,
    "resize_height": 480,
    "denoise_enabled": false,
    "sharpen_enabled": false
  }
}
```

#### 3. yolo_v8 - YOLO检测
```json
{
  "type": "yolo_v8",
  "config": {
    "model_path": "./models/yolov8n.pt",
    "confidence_threshold": 0.5,
    "device": "cpu"
  }
}
```

#### 4. opencv_process - OpenCV处理
```json
{
  "type": "opencv_process",
  "config": {
    "edge_detection_enabled": true,
    "canny_threshold1": 50,
    "canny_threshold2": 150,
    "contour_detection_enabled": true
  }
}
```

#### 5. display - 图像显示
```json
{
  "type": "display",
  "config": {
    "window_name": "Display",
    "show_fps": true,
    "display_fps_limit": 30
  }
}
```

#### 6. image_writer - 图像保存
```json
{
  "type": "image_writer",
  "config": {
    "save_images": true,
    "save_path": "./output",
    "save_format": "jpg",
    "save_interval": 30,
    "disk_monitor_enabled": true
  }
}
```

## 监控性能

### 查看日志

```bash
# 系统日志
tail -f logs/system.log

# 性能日志
tail -f logs/performance.log

# 错误日志
tail -f logs/error.log
```

### 使用监控界面

```bash
# 启动Qt监控界面
python test_qt_integration.py
```

监控界面显示：
- 实时FPS
- 节点执行时间
- 错误统计
- 性能曲线图

## 常见问题

### Q: 找不到相机
**A**: 检查以下项目：
1. 相机是否连接
2. 驱动是否安装
3. 环境变量是否设置

```bash
# Windows设置环境变量
setx MVCAM_COMMON_RUNENV "F:\MVS"
```

### Q: YOLO加载失败
**A**: 确保：
1. 模型文件存在
2. ultralytics已安装
3. 路径配置正确

```bash
pip install ultralytics
```

### Q: 系统运行缓慢
**A**: 优化建议：
1. 降低图像分辨率
2. 减少处理节点
3. 使用GPU加速
4. 调整队列大小

### Q: 磁盘空间不足
**A**: 系统会自动：
1. 监控磁盘空间
2. 清理旧文件
3. 停止保存（空间严重不足时）

配置清理策略：
```json
{
  "disk_monitor_enabled": true,
  "max_files_count": 500,
  "max_days_keep": 3,
  "auto_cleanup_enabled": true
}
```

## 性能调优

### 1. 相机参数

```json
{
  "exposure_time": 10000,  // 降低可提高帧率
  "frame_rate": 30.0,      // 根据需求调整
  "gain": 10.0             // 低光环境增加
}
```

### 2. YOLO参数

```json
{
  "device": "cuda",              // 使用GPU
  "confidence_threshold": 0.6,   // 提高阈值减少误检
  "use_half_precision": true     // 半精度加速
}
```

### 3. 系统参数

```bash
# 调整队列大小
python main_optimized.py --queue-size 20

# 禁用显示提升性能
python main_optimized.py --no-display
```

## 故障排查

### 检查系统状态

```bash
# 运行验证脚本
python quick_verify.py

# 运行测试
pytest tests/unit/ -v
```

### 查看详细日志

```bash
# 启用DEBUG日志
python main_optimized.py --log-level DEBUG
```

### 性能分析

```bash
# 运行性能测试
python test_monitoring.py
```

## 高级功能

### 1. 配置热重载

系统支持运行时更新配置（仅配置参数，不包括图结构）

### 2. 错误恢复策略

在配置中设置：
```json
{
  "execution_config": {
    "error_strategy": "skip",  // skip/retry/circuit-break
    "max_retries": 3
  }
}
```

### 3. 性能监控

系统自动收集：
- 节点执行时间
- 系统FPS
- 错误率
- 队列状态

## 最佳实践

### 1. 开发环境

```bash
# 使用测试配置
python main_optimized.py --config config/test_pipeline.json

# 启用详细日志
python main_optimized.py --log-level DEBUG
```

### 2. 生产环境

```bash
# 使用生产配置
python main_optimized.py --config config/production.json

# 精简日志
python main_optimized.py --log-level INFO

# 禁用显示
python main_optimized.py --no-display
```

### 3. 性能优化

- 使用GPU加速YOLO
- 降低图像分辨率
- 调整队列大小
- 禁用不必要的节点

## 技术支持

### 文档

- [开发者指南](./DEVELOPER_GUIDE.md)
- [系统架构](../DAG_ARCHITECTURE.md)
- [API参考](./API_REFERENCE.md)

### 日志位置

```
logs/
├── system.log       # 系统日志
├── performance.log  # 性能日志
└── error.log        # 错误日志
```

### 配置示例

```
config/
├── pipeline.json              # 基础配置
├── mvp_pipeline.json          # MVP配置
└── milestone3_pipeline.json   # 完整配置
```

---

**文档维护**: Kiro AI Assistant  
**最后更新**: 2026-01-30
