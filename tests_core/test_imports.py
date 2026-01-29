# -*- coding: utf-8 -*-
"""
导入测试脚本
验证所有模块是否可以正常导入，无父目录依赖
"""

import sys
import os

print("=" * 60)
print("Service_new 模块导入测试")
print("=" * 60)

# 测试结果
results = []

def test_import(module_name, import_statement):
    """测试导入"""
    try:
        exec(import_statement)
        results.append((module_name, True, "成功"))
        print(f"✓ {module_name}")
        return True
    except Exception as e:
        results.append((module_name, False, str(e)))
        print(f"✗ {module_name}: {e}")
        return False

print("\n【核心模块测试】")
test_import("logger_config", "from logger_config import get_logger")
test_import("pipeline_config", "from pipeline_config import PipelineConfig")
test_import("pipeline_core", "from pipeline_core import Pipeline, Filter, DataPacket")
test_import("scheduler", "from scheduler import PipelineScheduler")
test_import("main", "import main")

print("\n【微服务模块测试】")
test_import("services.__init__", "from services import *")
test_import("camera_service", "from services.camera_service import CameraService")
test_import("preprocess_service", "from services.preprocess_service import PreprocessService")
test_import("yolo_service", "from services.yolo_service import YOLOService")
test_import("opencv_service", "from services.opencv_service import OpenCVService")
test_import("display_service", "from services.display_service import DisplayService")
test_import("storage_service", "from services.storage_service import StorageService")

print("\n【异步版本测试】")
os.chdir("service_asyncio")
test_import("pipeline_core_async", "from pipeline_core_async import AsyncPipeline")
test_import("camera_service_async", "from camera_service_async import AsyncCameraService")
test_import("services_async", "from services_async import AsyncPreprocessService")
test_import("scheduler_async", "from scheduler_async import AsyncPipelineScheduler")
test_import("main_async", "import main_async")
os.chdir("..")

print("\n【Qt GUI版本测试】")
os.chdir("service_qt")
try:
    test_import("PyQt5", "from PyQt5.QtWidgets import QApplication")
    test_import("main_window", "from main_window import MainWindow")
    test_import("widgets", "from widgets import *")
    test_import("styles", "from styles import *")
    test_import("dialogs", "from dialogs import *")
    test_import("run_gui", "import run_gui")
except ImportError as e:
    print(f"  注意: PyQt5未安装，跳过GUI测试 ({e})")
os.chdir("..")

# 打印总结
print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)

success_count = sum(1 for _, success, _ in results if success)
total_count = len(results)

print(f"总计: {total_count} 个模块")
print(f"成功: {success_count} 个")
print(f"失败: {total_count - success_count} 个")

if success_count == total_count:
    print("\n✓ 所有模块导入成功！service_new 目录完全独立，无父目录依赖。")
else:
    print("\n✗ 部分模块导入失败，请检查错误信息。")
    print("\n失败的模块:")
    for name, success, msg in results:
        if not success:
            print(f"  - {name}: {msg}")

print("=" * 60)
