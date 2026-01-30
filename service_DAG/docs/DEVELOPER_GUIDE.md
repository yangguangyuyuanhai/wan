# 开发者指南

**版本**: 1.0.0  
**更新时间**: 2026-01-30

## 目录

1. [快速开始](#快速开始)
2. [创建新插件](#创建新插件)
3. [扩展数据类型](#扩展数据类型)
4. [代码风格](#代码风格)
5. [测试指南](#测试指南)

## 快速开始

### 环境准备

```bash
cd /home/fengze/yolo919/MVS/service_DAG

# 安装依赖
pip install -r requirements.txt

# 运行验证
python quick_verify.py
```

### 项目结构

```
service_DAG/
├── core/           # 核心基础设施
├── engine/         # 执行引擎
├── plugins/        # 插件系统
├── ui/             # 用户界面
├── tests/          # 测试
└── config/         # 配置
```

## 创建新插件

### 1. 插件模板

```python
# plugins/your_category/your_plugin.py
from engine.node import INode, NodeMetadata, ExecutionContext, NodeResult
from engine.port import InputPort, OutputPort
from core.data_types import ImageType

class YourPluginNode(INode):
    """你的插件描述"""
    
    # 插件元数据（必需）
    __plugin_metadata__ = {
        "type": "your_plugin",
        "name": "你的插件名称",
        "version": "1.0.0",
        "author": "你的名字",
        "description": "插件功能描述",
        "category": "algo",  # basic/algo/io/ui
        "dependencies": ["numpy", "opencv-python"]
    }
    
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        
        # 定义输入输出端口
        self._input_ports = [
            InputPort("image", ImageType, required=True)
        ]
        self._output_ports = [
            OutputPort("result", ImageType)
        ]
    
    def get_metadata(self) -> NodeMetadata:
        return NodeMetadata(
            name=self.__plugin_metadata__["name"],
            version=self.__plugin_metadata__["version"],
            author=self.__plugin_metadata__["author"],
            description=self.__plugin_metadata__["description"],
            category=self.__plugin_metadata__["category"]
        )
    
    def get_ports(self):
        return self._input_ports, self._output_ports
    
    def validate_config(self) -> bool:
        # 验证配置参数
        return True
    
    async def initialize(self) -> bool:
        # 初始化资源
        return True
    
    async def run(self, context: ExecutionContext) -> NodeResult:
        # 获取输入（注意：使用context.inputs）
        input_data = context.inputs.get("image")
        
        # 处理数据
        result = self._process(input_data)
        
        # 返回结果（注意：使用outputs字段）
        return NodeResult(
            success=True,
            outputs={"result": result},
            metadata={"node_id": self.node_id}
        )
    
    async def cleanup(self) -> None:
        # 清理资源
        pass
    
    def input_data_processed_hook(self, input_name: str) -> None:
        pass
    
    def _process(self, data):
        # 你的处理逻辑
        return data
```

### 2. 关键注意事项

#### ✅ 正确的字段名

```python
# ✓ 正确
context.inputs.get("image")
NodeResult(success=True, outputs={...}, error=None)

# ✗ 错误
context.input_data.get("image")  # 错误！
NodeResult(success=True, output_data={...})  # 错误！
```

#### ✅ 错误处理

```python
async def run(self, context: ExecutionContext) -> NodeResult:
    try:
        # 处理逻辑
        result = self._process(data)
        return NodeResult(success=True, outputs={"result": result})
    except Exception as e:
        return NodeResult(
            success=False,
            outputs={},
            error=f"处理失败: {e}"
        )
```

### 3. 注册插件

在 `plugins/your_category/__init__.py` 中：

```python
from .your_plugin import YourPluginNode

__all__ = ['YourPluginNode']
```

## 扩展数据类型

### 1. 创建新数据类型

```python
# core/data_types.py
from dataclasses import dataclass
import numpy as np

@dataclass
class YourDataType(BaseDataType):
    """你的数据类型"""
    data: Any
    
    def validate(self) -> bool:
        # 验证数据
        return self.data is not None
    
    def copy(self):
        # 复制数据
        return YourDataType(data=copy.deepcopy(self.data))
```

### 2. 注册数据类型

```python
from core.data_types import TypeRegistry

registry = TypeRegistry()
registry.register("your_type", YourDataType)
```

## 代码风格

### Python风格

- 遵循 PEP 8
- 使用类型提示
- 添加docstring
- 4空格缩进

### 命名规范

```python
# 类名：大驼峰
class CameraSourceNode:
    pass

# 函数/方法：小写+下划线
def process_image(image):
    pass

# 常量：大写+下划线
MAX_QUEUE_SIZE = 10

# 私有方法：前缀下划线
def _internal_method(self):
    pass
```

### 注释规范

```python
def process_image(image: np.ndarray) -> np.ndarray:
    """
    处理图像
    
    Args:
        image: 输入图像
        
    Returns:
        处理后的图像
        
    Raises:
        ValueError: 图像格式错误
    """
    pass
```

## 测试指南

### 1. 单元测试

```python
# tests/unit/test_your_plugin.py
import pytest
from plugins.your_category.your_plugin import YourPluginNode

class TestYourPlugin:
    def test_create_node(self):
        node = YourPluginNode("test", {})
        assert node is not None
    
    def test_validate_config(self):
        node = YourPluginNode("test", {"param": "value"})
        assert node.validate_config() is True
    
    @pytest.mark.asyncio
    async def test_run(self):
        node = YourPluginNode("test", {})
        await node.initialize()
        
        context = ExecutionContext(
            node_id="test",
            inputs={"image": test_data},
            global_context=GlobalContext(),
            event_bus=get_event_bus()
        )
        
        result = await node.run(context)
        assert result.success is True
```

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v -m integration

# 查看覆盖率
pytest tests/ --cov=. --cov-report=html
```

## 最佳实践

### 1. 性能优化

```python
# CPU密集任务使用线程池
import concurrent.futures

self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

async def run(self, context):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        self.executor,
        self._cpu_intensive_task,
        data
    )
```

### 2. 资源管理

```python
async def initialize(self):
    # 初始化资源
    self.resource = open_resource()
    return True

async def cleanup(self):
    # 清理资源
    if hasattr(self, 'resource'):
        self.resource.close()
```

### 3. 错误处理

```python
# 使用自定义异常
from core.exceptions import NodeExecutionError

if not valid:
    raise NodeExecutionError("验证失败")
```

## 调试技巧

### 1. 日志

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 2. 事件监听

```python
from core.event_bus import get_event_bus

event_bus = get_event_bus()
event_bus.subscribe('node.error', lambda e: print(f"错误: {e}"))
```

### 3. 性能分析

```python
import time

start = time.time()
# 你的代码
duration = time.time() - start
print(f"耗时: {duration:.3f}s")
```

## 常见问题

### Q: 如何访问输入数据？
A: 使用 `context.inputs.get("port_name")`

### Q: 如何返回输出？
A: 使用 `NodeResult(success=True, outputs={"port": data})`

### Q: 如何处理错误？
A: 返回 `NodeResult(success=False, outputs={}, error="错误信息")`

### Q: 如何避免GIL阻塞？
A: 使用 `run_in_executor` 执行CPU密集任务

## 参考资料

- [系统架构说明](../DAG_ARCHITECTURE.md)
- [API文档](./API_REFERENCE.md)
- [用户手册](./USER_MANUAL.md)

---

**文档维护**: Kiro AI Assistant  
**最后更新**: 2026-01-30
