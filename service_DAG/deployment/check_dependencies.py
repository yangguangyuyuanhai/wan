"""
依赖检查工具
扫描所有插件的依赖，检查当前环境是否满足
"""
import importlib
import sys
from pathlib import Path
from typing import List, Dict, Set
from service_DAG.core.plugin_manager import PluginManager


class DependencyChecker:
    """依赖检查器"""
    
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.missing_deps: Dict[str, List[str]] = {}
        self.all_deps: Set[str] = set()
    
    def scan_plugins(self, plugins_dir: str) -> None:
        """扫描插件目录"""
        self.plugin_manager.discover_plugins(plugins_dir)
    
    def check_dependencies(self) -> Dict[str, any]:
        """检查所有依赖"""
        results = {
            "total_plugins": 0,
            "total_dependencies": 0,
            "missing_dependencies": {},
            "satisfied": True
        }
        
        for plugin_type in self.plugin_manager.get_available_plugins():
            metadata = self.plugin_manager.get_plugin_metadata(plugin_type)
            results["total_plugins"] += 1
            
            # 获取依赖列表
            dependencies = metadata.get("dependencies", [])
            if not dependencies:
                continue
            
            results["total_dependencies"] += len(dependencies)
            self.all_deps.update(dependencies)
            
            # 检查每个依赖
            missing = []
            for dep in dependencies:
                if not self._check_module(dep):
                    missing.append(dep)
            
            if missing:
                results["missing_dependencies"][plugin_type] = missing
                results["satisfied"] = False
        
        return results
    
    def _check_module(self, module_name: str) -> bool:
        """检查模块是否可导入"""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False
    
    def generate_report(self) -> str:
        """生成依赖报告"""
        results = self.check_dependencies()
        
        report = []
        report.append("=" * 60)
        report.append("依赖检查报告")
        report.append("=" * 60)
        report.append(f"扫描插件数: {results['total_plugins']}")
        report.append(f"总依赖数: {results['total_dependencies']}")
        report.append(f"状态: {'✅ 满足所有依赖' if results['satisfied'] else '❌ 存在缺失依赖'}")
        report.append("")
        
        if results["missing_dependencies"]:
            report.append("缺失依赖详情:")
            report.append("-" * 60)
            for plugin, deps in results["missing_dependencies"].items():
                report.append(f"\n插件: {plugin}")
                for dep in deps:
                    report.append(f"  - {dep}")
            report.append("")
            report.append("安装命令:")
            all_missing = set()
            for deps in results["missing_dependencies"].values():
                all_missing.update(deps)
            report.append(f"pip install {' '.join(all_missing)}")
        else:
            report.append("✅ 所有依赖已满足")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def generate_requirements(self) -> str:
        """生成requirements.txt内容"""
        lines = ["# 自动生成的依赖列表", ""]
        
        for dep in sorted(self.all_deps):
            try:
                mod = importlib.import_module(dep)
                version = getattr(mod, "__version__", "")
                if version:
                    lines.append(f"{dep}=={version}")
                else:
                    lines.append(dep)
            except ImportError:
                lines.append(dep)
        
        return "\n".join(lines)


def main():
    """主函数"""
    checker = DependencyChecker()
    
    # 扫描插件
    plugins_dir = Path(__file__).parent.parent / "plugins"
    if plugins_dir.exists():
        checker.scan_plugins(str(plugins_dir))
    
    # 生成报告
    report = checker.generate_report()
    print(report)
    
    # 保存到文件
    with open("dependency_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n报告已保存到: dependency_report.txt")
    
    # 生成requirements
    requirements = checker.generate_requirements()
    with open("requirements_generated.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    
    print("依赖列表已保存到: requirements_generated.txt")


if __name__ == "__main__":
    main()
