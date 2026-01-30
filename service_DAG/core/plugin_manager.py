# -*- coding: utf-8 -*-
"""
插件管理器 (Plugin Manager)
动态插件加载器，扫描plugins目录并加载插件类

响应需求：需求 1（微内核层）
响应任务：任务 5 - 实现插件管理器
响应建议：new_change.md - 增强单机离线部署，支持依赖检查
"""

import os
import sys
import importlib
import importlib.util
import inspect
from typing import Dict, Type, List, Optional, Set
from pathlib import Path

from core.exceptions import PluginLoadError, PluginNotFoundError


# ==================== 插件管理器 ====================

class PluginManager:
    """
    插件管理器
    
    负责：
    1. 扫描插件目录
    2. 动态加载插件类
    3. 验证插件接口
    4. 管理插件元数据
    5. 检查插件依赖（单机离线部署）
    """
    
    def __init__(self, plugin_dirs: List[str], logger=None):
        """
        初始化插件管理器
        
        Args:
            plugin_dirs: 插件目录列表
            logger: 日志记录器（可选）
        """
        self.plugin_dirs = plugin_dirs
        self.logger = logger
        
        # 插件注册表
        self.plugins: Dict[str, Type] = {}  # plugin_type -> plugin_class
        self.plugin_metadata: Dict[str, Dict] = {}  # plugin_type -> metadata
        
        # 依赖管理
        self.plugin_dependencies: Dict[str, List[str]] = {}  # plugin_type -> [dependencies]
        self.missing_dependencies: Dict[str, List[str]] = {}  # plugin_type -> [missing_deps]
    
    # ==================== 插件发现 ====================
    
    def discover_plugins(self) -> int:
        """
        发现所有插件
        
        扫描插件目录，加载所有符合接口的插件类
        
        Returns:
            发现的插件数量
        """
        self._log("info", "开始扫描插件...")
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                self._log("warning", f"插件目录不存在: {plugin_dir}")
                continue
            
            self._scan_directory(plugin_dir)
        
        self._log("info", f"发现 {len(self.plugins)} 个插件")
        
        # 检查依赖
        self._check_all_dependencies()
        
        return len(self.plugins)
    
    def _scan_directory(self, directory: str):
        """
        扫描目录中的插件
        
        Args:
            directory: 目录路径
        """
        for root, dirs, files in os.walk(directory):
            # 跳过 __pycache__ 等目录
            dirs[:] = [d for d in dirs if not d.startswith('__')]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('_'):
                    module_path = os.path.join(root, file)
                    self._load_plugin_module(module_path, directory)
    
    def _load_plugin_module(self, module_path: str, base_dir: str):
        """
        加载插件模块
        
        使用安全加载模式：捕获所有异常，不让坏插件导致程序闪退
        
        Args:
            module_path: 模块文件路径
            base_dir: 基础目录
        """
        try:
            # 构建模块名
            rel_path = os.path.relpath(module_path, base_dir)
            module_name = rel_path.replace(os.sep, '.').replace('.py', '')
            
            # 动态导入
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                self._log("error", f"无法创建模块规范: {module_path}")
                return
            
            module = importlib.util.module_from_spec(spec)
            
            # 保护 sys.path：插件加载失败不影响主进程
            old_path = sys.path.copy()
            try:
                spec.loader.exec_module(module)
            finally:
                sys.path = old_path
            
            # 查找 INode 实现
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if self._is_plugin_class(obj):
                    self._register_plugin(obj)
                    
        except ImportError as e:
            # 依赖缺失
            self._log("error", f"加载插件失败（依赖缺失）{module_path}: {e}")
        except Exception as e:
            # 其他异常
            self._log("error", f"加载插件失败 {module_path}: {e}")
    
    def _is_plugin_class(self, cls) -> bool:
        """
        判断是否为插件类
        
        检查是否实现 INode 接口
        
        Args:
            cls: 类对象
            
        Returns:
            是否为插件类
        """
        # 检查是否有必需的方法和属性
        required_methods = ['get_metadata', 'get_ports', 'run', 'validate_config']
        required_attrs = ['__plugin_metadata__']
        
        for method in required_methods:
            if not hasattr(cls, method):
                return False
        
        for attr in required_attrs:
            if not hasattr(cls, attr):
                return False
        
        return True
    
    # ==================== 插件注册 ====================
    
    def _register_plugin(self, plugin_class: Type):
        """
        注册插件
        
        Args:
            plugin_class: 插件类
        """
        try:
            # 读取元数据
            metadata = plugin_class.__plugin_metadata__
            plugin_type = metadata['type']
            
            # 验证元数据完整性
            required_fields = ['type', 'name', 'version', 'author', 'description', 'category']
            for field in required_fields:
                if field not in metadata:
                    self._log("warning", f"插件 {plugin_type} 缺少元数据字段: {field}")
            
            # 注册插件
            self.plugins[plugin_type] = plugin_class
            self.plugin_metadata[plugin_type] = metadata
            
            # 提取依赖信息
            dependencies = metadata.get('dependencies', [])
            self.plugin_dependencies[plugin_type] = dependencies
            
            self._log("info", f"注册插件: {plugin_type} ({metadata.get('name', 'Unknown')})")
            
        except Exception as e:
            self._log("error", f"注册插件失败: {e}")
    
    # ==================== 依赖管理 ====================
    
    def _check_all_dependencies(self):
        """
        检查所有插件的依赖
        
        验证依赖的 Python 包是否存在
        """
        self._log("info", "检查插件依赖...")
        
        for plugin_type, dependencies in self.plugin_dependencies.items():
            missing = self._check_dependencies(dependencies)
            if missing:
                self.missing_dependencies[plugin_type] = missing
                self._log("warning", f"插件 {plugin_type} 缺少依赖: {missing}")
        
        if self.missing_dependencies:
            self._log("warning", f"共有 {len(self.missing_dependencies)} 个插件缺少依赖")
        else:
            self._log("info", "所有插件依赖检查通过")
    
    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        检查依赖列表
        
        Args:
            dependencies: 依赖包列表
            
        Returns:
            缺失的依赖列表
        """
        missing = []
        
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)
        
        return missing
    
    def generate_dependency_report(self) -> Dict[str, Any]:
        """
        生成依赖报告
        
        列出所有插件的依赖，用于打包
        
        Returns:
            依赖报告字典
        """
        all_dependencies = set()
        for deps in self.plugin_dependencies.values():
            all_dependencies.update(deps)
        
        return {
            'total_plugins': len(self.plugins),
            'plugins_with_dependencies': len(self.plugin_dependencies),
            'all_dependencies': sorted(list(all_dependencies)),
            'missing_dependencies': self.missing_dependencies,
            'plugin_dependencies': self.plugin_dependencies
        }
    
    # ==================== 插件查询 ====================
    
    def get_plugin(self, plugin_type: str) -> Optional[Type]:
        """
        获取插件类
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            插件类，如果不存在返回 None
        """
        return self.plugins.get(plugin_type)
    
    def get_plugin_metadata(self, plugin_type: str) -> Optional[Dict]:
        """
        获取插件元数据
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            元数据字典，如果不存在返回 None
        """
        return self.plugin_metadata.get(plugin_type)
    
    def list_plugins(self) -> List[Dict]:
        """
        列出所有插件
        
        Returns:
            插件信息列表
        """
        return [
            {
                'type': ptype,
                **metadata,
                'has_missing_dependencies': ptype in self.missing_dependencies
            }
            for ptype, metadata in self.plugin_metadata.items()
        ]
    
    def list_plugins_by_category(self, category: str) -> List[Dict]:
        """
        按类别列出插件
        
        Args:
            category: 类别名称
            
        Returns:
            插件信息列表
        """
        return [
            plugin for plugin in self.list_plugins()
            if plugin.get('category') == category
        ]
    
    # ==================== 插件实例化 ====================
    
    def create_plugin_instance(self, plugin_type: str, node_id: str, config: Dict):
        """
        创建插件实例
        
        Args:
            plugin_type: 插件类型
            node_id: 节点ID
            config: 配置
            
        Returns:
            插件实例
            
        Raises:
            PluginNotFoundError: 插件不存在
            PluginLoadError: 插件加载失败
        """
        plugin_class = self.get_plugin(plugin_type)
        
        if plugin_class is None:
            raise PluginNotFoundError(
                f"插件不存在: {plugin_type}",
                {'plugin_type': plugin_type}
            )
        
        # 检查依赖
        if plugin_type in self.missing_dependencies:
            raise PluginLoadError(
                f"插件缺少依赖: {plugin_type}",
                {
                    'plugin_type': plugin_type,
                    'missing_dependencies': self.missing_dependencies[plugin_type]
                }
            )
        
        try:
            # 创建实例
            instance = plugin_class(node_id=node_id, config=config)
            return instance
        except Exception as e:
            raise PluginLoadError(
                f"创建插件实例失败: {plugin_type}",
                {'plugin_type': plugin_type, 'error': str(e)}
            )
    
    # ==================== 版本管理 ====================
    
    def check_version_compatibility(self, plugin_type: str, required_version: str) -> bool:
        """
        检查插件版本兼容性
        
        Args:
            plugin_type: 插件类型
            required_version: 要求的版本
            
        Returns:
            是否兼容
        """
        metadata = self.get_plugin_metadata(plugin_type)
        if metadata is None:
            return False
        
        plugin_version = metadata.get('version', '0.0.0')
        
        # 简单的版本比较（可以使用 packaging 库进行更复杂的比较）
        return plugin_version >= required_version
    
    # ==================== 辅助方法 ====================
    
    def _log(self, level: str, message: str):
        """
        记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
        """
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[PluginManager] [{level.upper()}] {message}")
    
    def __str__(self):
        return f"PluginManager(plugins={len(self.plugins)}, dirs={len(self.plugin_dirs)})"
    
    def __repr__(self):
        return self.__str__()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("插件管理器测试")
    print("=" * 60)
    
    # 创建插件管理器
    print("\n1. 创建插件管理器")
    print("-" * 60)
    
    # 假设插件目录
    plugin_dirs = ["plugins"]
    manager = PluginManager(plugin_dirs)
    print(f"插件管理器: {manager}")
    
    # 发现插件
    print("\n2. 发现插件")
    print("-" * 60)
    count = manager.discover_plugins()
    print(f"发现 {count} 个插件")
    
    # 列出插件
    print("\n3. 列出所有插件")
    print("-" * 60)
    plugins = manager.list_plugins()
    for plugin in plugins:
        print(f"  - {plugin['type']}: {plugin.get('name', 'Unknown')}")
    
    # 生成依赖报告
    print("\n4. 生成依赖报告")
    print("-" * 60)
    report = manager.generate_dependency_report()
    print(f"总插件数: {report['total_plugins']}")
    print(f"所有依赖: {report['all_dependencies']}")
    if report['missing_dependencies']:
        print(f"缺失依赖: {report['missing_dependencies']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
