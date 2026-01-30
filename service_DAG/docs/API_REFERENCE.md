# API参考文档

**版本**: 1.0.0  
**更新时间**: 2026-01-30

## 核心模块 (core)

### data_types.py

#### ImageData
```python
@dataclass
class ImageData:
    data: np.ndarray      # 图像数据
    width: int            # 宽度
    height: int           # 高度
    channels: int         # 通道数
    format: str           # 格式 (BGR/RGB/GRAY)
    timestamp: float      # 时间戳
```

#### DetectionData
```python
@dataclass
class DetectionData:
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float                 # 置信度
    class_id: int                     # 类别ID
    class_name: str                   # 类别名称
```

### event_bus.py

#### EventBus
```python
class EventBus:
    def subscribe(self, event_type: str, handler: Callable) -> None
    def unsubscribe(self, event_type: str, handler: Callable) -> None
    def publish(self, event_type: str, data: Dict[str, Any]) -> None
```

**事件类型**:
- `graph.start` - 图开始执行
- `graph.complete` - 图执行完成
- `node.start` - 节点开始执行
- `node.complete` - 节点执行完成
- `node.error` - 节点执行错误

### plugin_manager.py

#### PluginManager
```python
class PluginManager:
    def discover_plugins(self, plugins_dir: str) -> None
    def register_plugin(self, plugin_class: Type[INode]) -> None
    def get_plugin_class(self, plugin_type: str) -> Type[INode]
    def create_plugin_instance(self, plugin_type: str, node_id: str, config: Dict) -> INode
    def get_available_plugins(self) -> List[str]
    def get_plugin_metadata(self, plugin_type: str) -> Dict[str, Any]
```

### metrics.py

#### MetricsCollector
```python
class MetricsCollector:
    def __init__(self, event_bus: EventBus)
    def get_node_metrics(self, node_id: str) -> Dict[str, Any]
    def get_system_metrics(self) -> Dict[str, Any]
    def reset_metrics(self) -> None
```

**返回指标**:
- `count` - 执行次数
- `avg_time` - 平均执行时间
- `min_time` - 最小执行时间
- `max_time` - 最大执行时间
- `error_count` - 错误次数

---

## 执行引擎 (engine)

### node.py

#### INode (接口)
```python
class INode(ABC):
    __plugin_metadata__: Dict[str, Any]  # 插件元数据
    
    def __init__(self, node_id: str, config: Dict[str, Any])
    
    @abstractmethod
    async def run(self, context: ExecutionContext) -> NodeResult
    
    async def initialize(self) -> None
    async def cleanup(self) -> None
```

#### ExecutionContext
```python
@dataclass
class ExecutionContext:
    node_id: str                    # 节点ID
    inputs: Dict[str, Any]          # 输入数据
    global_context: Any             # 全局上下文
    event_bus: Any                  # 事件总线
    execution_id: Optional[str]     # 执行ID
```

#### NodeResult
```python
@dataclass
class NodeResult:
    success: bool                   # 是否成功
    outputs: Dict[str, Any]         # 输出数据
    error: Optional[str]            # 错误信息
    metadata: Dict[str, Any]        # 元数据
    execution_time: Optional[float] # 执行时间
```

### graph.py

#### Graph
```python
class Graph:
    def add_node(self, node: INode) -> None
    def remove_node(self, node_id: str) -> None
    def add_connection(self, from_node: str, from_port: str, 
                      to_node: str, to_port: str) -> None
    def remove_connection(self, from_node: str, from_port: str,
                         to_node: str, to_port: str) -> None
    def validate(self) -> bool
    def get_topological_order(self) -> List[str]
    def get_node(self, node_id: str) -> INode
```

### streaming_executor.py

#### StreamingExecutor
```python
class StreamingExecutor:
    def __init__(self, graph: Graph, event_bus: EventBus, 
                 error_strategy: str = "circuit-break")
    
    async def start(self) -> None
    async def stop(self) -> None
    async def pause(self) -> None
    async def resume(self) -> None
```

**错误策略**:
- `circuit-break` - 遇错停止整个图
- `skip` - 跳过失败节点
- `retry` - 重试失败节点

---

## 插件开发

### 创建插件

```python
from service_DAG.engine.node import INode, NodeResult, ExecutionContext

class MyPlugin(INode):
    __plugin_metadata__ = {
        "type": "my_plugin",
        "name": "My Plugin",
        "version": "1.0.0",
        "description": "Plugin description"
    }
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        # 获取输入
        input_data = context.inputs.get("input_port")
        
        # 处理逻辑
        result = self.process(input_data)
        
        # 返回结果
        return NodeResult(
            success=True,
            outputs={"output_port": result}
        )
    
    def process(self, data):
        # 实现处理逻辑
        return data
```

### 插件元数据

```python
__plugin_metadata__ = {
    "type": "plugin_type",        # 插件类型（唯一标识）
    "name": "Plugin Name",        # 显示名称
    "version": "1.0.0",           # 版本号
    "description": "...",         # 描述
    "author": "Author Name",      # 作者（可选）
    "dependencies": []            # 依赖库（可选）
}
```

---

## 配置文件格式

### 流水线配置

```json
{
  "name": "pipeline_name",
  "version": "1.0.0",
  "description": "Pipeline description",
  "nodes": [
    {
      "id": "node_id",
      "type": "plugin_type",
      "config": {
        "param1": "value1",
        "param2": 123
      }
    }
  ],
  "connections": [
    {
      "from_node": "source_node_id",
      "from_port": "output_port",
      "to_node": "target_node_id",
      "to_port": "input_port"
    }
  ]
}
```

---

## 事件系统

### 标准事件

#### 图级别事件
- `graph.start` - 图开始执行
- `graph.complete` - 图执行完成
- `graph.error` - 图执行错误
- `graph.stop` - 图停止

#### 节点级别事件
- `node.start` - 节点开始执行
- `node.complete` - 节点执行完成
- `node.error` - 节点执行错误

#### 性能事件
- `metrics.node` - 节点性能指标
- `metrics.system` - 系统性能指标

#### 日志事件
- `log.debug` - 调试日志
- `log.info` - 信息日志
- `log.warning` - 警告日志
- `log.error` - 错误日志

---

## 使用示例

### 基本使用

```python
from service_DAG.core.plugin_manager import PluginManager
from service_DAG.engine.graph import Graph
from service_DAG.engine.streaming_executor import StreamingExecutor
from service_DAG.core.async_event_bus import AsyncEventBus

# 初始化
manager = PluginManager()
manager.discover_plugins("plugins")

# 构建图
graph = Graph()
node1 = manager.create_plugin_instance("camera_hik", "camera", {})
node2 = manager.create_plugin_instance("display", "display", {})

graph.add_node(node1)
graph.add_node(node2)
graph.add_connection("camera", "image", "display", "image")

# 执行
event_bus = AsyncEventBus()
executor = StreamingExecutor(graph, event_bus)

await executor.start()
# ... 运行 ...
await executor.stop()
```

### 订阅事件

```python
from service_DAG.core.event_bus import EventBus

event_bus = EventBus()

def on_node_complete(data):
    print(f"Node {data['node_id']} completed")

event_bus.subscribe("node.complete", on_node_complete)
```

### 性能监控

```python
from service_DAG.core.metrics import MetricsCollector

metrics = MetricsCollector(event_bus)

# 获取节点指标
node_metrics = metrics.get_node_metrics("node_id")
print(f"Average time: {node_metrics['avg_time']}")

# 获取系统指标
system_metrics = metrics.get_system_metrics()
print(f"System FPS: {system_metrics['fps']}")
```

---

**文档维护**: Kiro AI Assistant  
**最后更新**: 2026-01-30
