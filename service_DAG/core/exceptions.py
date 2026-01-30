# -*- coding: utf-8 -*-
"""
异常定义
定义系统中使用的所有异常类型
"""


class CoreException(Exception):
    """核心异常基类"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class PluginException(CoreException):
    """插件相关异常"""
    pass


class PluginLoadError(PluginException):
    """插件加载失败"""
    pass


class PluginNotFoundError(PluginException):
    """插件未找到"""
    pass


class PluginVersionError(PluginException):
    """插件版本不兼容"""
    pass


class GraphException(CoreException):
    """图相关异常"""
    pass


class GraphCycleError(GraphException):
    """图中存在环路"""
    pass


class CycleDetectedError(GraphException):
    """检测到循环（别名）"""
    pass


class GraphConnectionError(GraphException):
    """图连接错误"""
    pass


class GraphValidationError(GraphException):
    """图验证失败"""
    pass


class TypeException(CoreException):
    """类型相关异常"""
    pass


class TypeMismatchError(TypeException):
    """类型不匹配"""
    pass


class TypeValidationError(TypeException):
    """类型验证失败"""
    pass


class ResourceException(CoreException):
    """资源相关异常"""
    pass


class ResourceNotFoundError(ResourceException):
    """资源未找到"""
    pass


class ResourceExhaustedError(ResourceException):
    """资源耗尽"""
    pass


class ResourceLeakError(ResourceException):
    """资源泄漏"""
    pass


class ExecutionException(CoreException):
    """执行相关异常"""
    pass


class NodeExecutionError(ExecutionException):
    """节点执行失败"""
    pass


class TimeoutError(ExecutionException):
    """执行超时"""
    pass


class ConfigException(CoreException):
    """配置相关异常"""
    pass


class ConfigValidationError(ConfigException):
    """配置验证失败"""
    pass


class ConfigNotFoundError(ConfigException):
    """配置未找到"""
    pass


if __name__ == "__main__":
    # 测试异常
    print("异常系统测试\n")
    
    try:
        raise PluginLoadError("无法加载插件", {"plugin": "YoloNode", "reason": "文件不存在"})
    except CoreException as e:
        print(f"捕获异常: {e}")
        print(f"详细信息: {e.details}")
    
    try:
        raise GraphCycleError("检测到环路", {"nodes": ["A", "B", "C"]})
    except CoreException as e:
        print(f"\n捕获异常: {e}")
    
    print("\n测试完成")
