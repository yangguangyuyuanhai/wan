#!/usr/bin/env python3
"""
启动DAG可视化编辑器
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ui.dag_editor.editor_window import main

if __name__ == "__main__":
    main()
