# -*- coding: utf-8 -*-
"""
系统测试脚本
测试所有模块是否能正常导入和初始化
"""

import sys
import traceback

def test_module(module_path, class_name=None):
    """测试模块导入"""
    try:
        parts = module_path.rsplit('.', 1)
        if len(parts) == 2:
            module_name, obj_name = parts
            module = __import__(module_name, fromlist=[obj_name])
            obj = getattr(module, obj_name)
            print(f"✓ {module_path}")
            return True
        else:
            __import__(module_path)
            print(f"✓ {module_path}")
            return True
    except Exception as e:
        print(f"✗ {module_path}: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("系统模块测试")
    print("=" * 60)
    
    results = []
    
    # 测试配置模块
    print("\n【配置模块】")
    results.append(test_module("pipeline_config.PipelineConfig"))
    results.append(test_module("pipeline_config.PresetConfigs"))
    results.append(test_module("logger_config.CameraLogger"))
    
    # 测试核心模块
    print("\n【核心模块】")
    results.append(test_module("pipeline_core.DataPacket"))
    results.append(test_module("pipeline_core.Filter"))
    results.append(test_module("pipeline_core.Pipeline"))
    
    # 测试调度器
    print("\n【调度器】")
    results.append(test_module("scheduler.PipelineScheduler"))
    
    # 测试服务模块
    print("\n【微服务】")
    results.append(test_module("services.camera_service.CameraService"))
    results.append(test_module("services.preprocess_service.PreprocessService"))
    results.append(test_module("services.yolo_service.YOLOService"))
    results.append(test_module("services.opencv_service.OpenCVService"))
    results.append(test_module("services.display_service.DisplayService"))
    results.append(test_module("services.storage_service.StorageService"))
    
    # 统计结果
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有模块测试通过！")
        return 0
    else:
        print(f"✗ {total - passed} 个模块测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
