# DAG 架构升级说明

## 架构概述

本项目从"模块化单体"升级为"微内核 + DAG + 事件驱动"架构，构建工业级低代码视觉平台引擎。

## 核心架构层次

### 1. 微内核层 (core/)
系统的"底座"，负责插件加载、生命周期管理、内存管理、配置解析。

- `event_bus.py` - 事件总线（系统神经）
- `plugin_manager.py` - 插件加载器（IoC容器）
- `context.py` - 全局上下文容器
- `exceptions.py` - 异常定义
- `types.py` - 数据类型系统

### 2. 编排层 (engine/)
系统的"大脑"，负责解析 DAG 图，计算执行顺序，管理数据流转。

- `graph.py` - 图管理器
- `node.py` - 节点基类（替代Filter）
- `port.py` - 端口定义（输入输出）
- `executor.py` - 异步执行器
- `scheduler.py` - 拓扑调度器

### 3. 插件层 (plugins/)
系统的"手脚"，原 services/ 重构为插件，单一职责。

- `basic/` - 基础插件（相机、存储）
- `algo/` - 算法插件（YOLO、OpenCV）
- `ui/` - 界面插件（显示）

### 4. 配置层 (config/)
流程图定义和系统配置。

- `pipeline.json` - DAG流程图定义
- `system_config.py` - 系统配置

## 关键技术特性

### 数据类型系统
- 强类型端口连接检查
- 运行时类型验证
- 支持 Image, Point, Region, String, Number 等基础类型

### 事件驱动
- 全局事件总线解耦通信
- 支持主题订阅
- 典型事件：sys.startup, node.error, graph.throughput

### DAG 执行
- 拓扑排序
- 环路检测
- Push/Pull 模式支持
- 零拷贝数据传递

### 调试支持
- 单步执行
- 断点调试
- 中间结果预览

### 资源管理
- 上下文管理器
- 自动资源清理
- 异常安全

## 实施路线

### 阶段一：事件总线（已完成）
- 创建 event_bus.py
- 解耦 UI、日志和业务逻辑

### 阶段二：标准化插件接口（进行中）
- 定义 BaseNode 基类
- 重构 services/ 为插件
- 端口定义

### 阶段三：DAG 执行引擎
- 实现 GraphManager
- 拓扑排序
- 端口数据传递

### 阶段四：微内核动态加载
- 实现 PluginLoader
- 扫描目录加载
- 工厂模式注册

## 目录结构

```
service_DAG/
├── core/                   # [微内核]
│   ├── event_bus.py        # 事件总线
│   ├── plugin_manager.py   # 插件加载器
│   ├── context.py          # 全局上下文
│   ├── exceptions.py       # 异常定义
│   └── types.py            # 数据类型系统
├── engine/                 # [DAG引擎]
│   ├── graph.py            # 图管理
│   ├── node.py             # 节点基类
│   ├── port.py             # 端口定义
│   ├── executor.py         # 执行器(Async)
│   └── scheduler.py        # 拓扑调度器
├── plugins/                # [插件层]
│   ├── basic/              # 基础插件
│   │   ├── camera_hik.py
│   │   └── image_save.py
│   ├── algo/               # 算法插件
│   │   ├── yolo_infer.py
│   │   └── opencv_proc.py
│   └── ui/                 # 界面相关插件
│       └── display.py
├── config/                 # [配置]
│   ├── pipeline.json       # 流程图定义
│   └── system_config.py    # 系统配置
├── ui/                     # Qt界面（事件订阅者）
├── main.py                 # 启动入口（启动内核）
└── README_DAG.md           # DAG版本说明
```

## 与原架构对比

| 特性 | 原架构 (service_new) | DAG架构 (service_DAG) |
|------|---------------------|----------------------|
| 架构模式 | 管道-过滤器（线性） | 微内核+DAG（图） |
| 数据流 | 队列传递 | 端口连接 |
| 配置方式 | 硬编码 | JSON定义 |
| 扩展性 | 修改代码 | 插件化 |
| 调试能力 | 有限 | 单步/断点 |
| 类型安全 | 弱类型 | 强类型 |
| 事件通信 | Qt信号槽 | 事件总线 |

## 技术壁垒

完成后的系统将具备：
- 工业级可靠性
- 低代码开发能力
- 可视化流程编辑
- 插件市场生态
- 分布式扩展能力

可作为通用视觉开发平台交付客户。
