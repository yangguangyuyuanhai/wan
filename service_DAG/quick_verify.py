#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证脚本
验证所有关键组件是否可以正常导入和工作
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有关键模块导入"""
    print("=" * 60)
    print("测试模块导入")
    print("=" * 60)
    
    tests = []
    
    # 核心模块
    try:
        from core.data_types import ImageType, BBoxType, DetectionListType
        tests.append(("core.data_types", True, None))
    except Exception as e:
        tests.append(("core.data_types", False, str(e)))
    
    try:
        from core.event_bus import get_event_bus
        tests.append(("core.event_bus", True, None))
    except Exception as e:
        tests.append(("core.event_bus", False, str(e)))
    
    try:
        from core.context import GlobalContext
        tests.append(("core.context", True, None))
    except Exception as e:
        tests.append(("core.context", False, str(e)))
    
    try:
        from core.plugin_manager import PluginManager
        tests.append(("core.plugin_manager", True, None))
    except Exception as e:
        tests.append(("core.plugin_manager", False, str(e)))
    
    # 引擎模块
    try:
        from engine.node import INode, NodeResult, ExecutionContext
        tests.append(("engine.node", True, None))
    except Exception as e:
        tests.append(("engine.node", False, str(e)))
    
    try:
        from engine.graph import Graph
        tests.append(("engine.graph", True, None))
    except Exception as e:
        tests.append(("engine.graph", False, str(e)))
    
    try:
        from engine.streaming_executor import StreamingExecutor
        tests.append(("engine.streaming_executor", True, None))
    except Exception as e:
        tests.append(("engine.streaming_executor", False, str(e)))
    
    # 插件模块
    try:
        from plugins.algo.preprocess import PreprocessNode
        tests.append(("plugins.algo.preprocess", True, None))
    except Exception as e:
        tests.append(("plugins.algo.preprocess", False, str(e)))
    
    try:
        from plugins.algo.yolo_infer import YoloInferenceNode
        tests.append(("plugins.algo.yolo_infer", True, None))
    except Exception as e:
        tests.append(("plugins.algo.yolo_infer", False, str(e)))
    
    try:
        from plugins.algo.opencv_proc import OpenCVProcessNode
        tests.append(("plugins.algo.opencv_proc", True, None))
    except Exception as e:
        tests.append(("plugins.algo.opencv_proc", False, str(e)))
    
    try:
        from plugins.io.image_save import ImageWriterNode
        tests.append(("plugins.io.image_save", True, None))
    except Exception as e:
        tests.append(("plugins.io.image_save", False, str(e)))
    
    # 输出结果
    success_count = 0
    for module, success, error in tests:
        if success:
            print(f"✓ {module}")
            success_count += 1
        else:
            print(f"✗ {module}: {error}")
    
    print(f"\n导入测试: {success_count}/{len(tests)} 通过")
    return success_count == len(tests)


def test_node_result():
    """测试NodeResult字段"""
    print("\n" + "=" * 60)
    print("测试NodeResult字段")
    print("=" * 60)
    
    try:
        from engine.node import NodeResult
        
        # 测试正确的字段
        result = NodeResult(
            success=True,
            outputs={"test": "data"},
            error=None,
            metadata={"key": "value"}
        )
        
        assert hasattr(result, 'success'), "缺少success字段"
        assert hasattr(result, 'outputs'), "缺少outputs字段"
        assert hasattr(result, 'error'), "缺少error字段"
        assert hasattr(result, 'metadata'), "缺少metadata字段"
        
        assert result.outputs == {"test": "data"}, "outputs字段值错误"
        
        print("✓ NodeResult字段正确")
        return True
        
    except Exception as e:
        print(f"✗ NodeResult测试失败: {e}")
        return False


def test_execution_context():
    """测试ExecutionContext字段"""
    print("\n" + "=" * 60)
    print("测试ExecutionContext字段")
    print("=" * 60)
    
    try:
        from engine.node import ExecutionContext
        from core.context import GlobalContext
        from core.event_bus import get_event_bus
        
        # 测试正确的字段
        context = ExecutionContext(
            node_id="test_node",
            inputs={"image": "test_data"},
            global_context=GlobalContext(),
            event_bus=get_event_bus()
        )
        
        assert hasattr(context, 'node_id'), "缺少node_id字段"
        assert hasattr(context, 'inputs'), "缺少inputs字段"
        assert hasattr(context, 'global_context'), "缺少global_context字段"
        assert hasattr(context, 'event_bus'), "缺少event_bus字段"
        
        assert context.inputs == {"image": "test_data"}, "inputs字段值错误"
        
        print("✓ ExecutionContext字段正确")
        return True
        
    except Exception as e:
        print(f"✗ ExecutionContext测试失败: {e}")
        return False


def test_plugin_interface():
    """测试插件接口一致性"""
    print("\n" + "=" * 60)
    print("测试插件接口一致性")
    print("=" * 60)
    
    try:
        from plugins.algo.preprocess import PreprocessNode
        from engine.node import INode
        
        # 创建插件实例
        node = PreprocessNode("test_preprocess", {
            "convert_to_bgr": True,
            "resize_enabled": False
        })
        
        # 检查是否实现了必需的方法
        assert hasattr(node, 'get_metadata'), "缺少get_metadata方法"
        assert hasattr(node, 'get_ports'), "缺少get_ports方法"
        assert hasattr(node, 'validate_config'), "缺少validate_config方法"
        assert hasattr(node, 'initialize'), "缺少initialize方法"
        assert hasattr(node, 'run'), "缺少run方法"
        assert hasattr(node, 'cleanup'), "缺少cleanup方法"
        
        print("✓ 插件接口一致性正确")
        return True
        
    except Exception as e:
        print(f"✗ 插件接口测试失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DAG系统快速验证")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(("模块导入", test_imports()))
    results.append(("NodeResult字段", test_node_result()))
    results.append(("ExecutionContext字段", test_execution_context()))
    results.append(("插件接口", test_plugin_interface()))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for test_name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {test_name}")
    
    print(f"\n总体结果: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有验证通过！系统可以正常运行。")
        return 0
    else:
        print("\n⚠️  部分验证失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
