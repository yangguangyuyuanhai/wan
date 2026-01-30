"""
构建离线部署包脚本
下载依赖并创建可部署的包
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


class DeploymentBuilder:
    """部署包构建器"""
    
    def __init__(self, output_dir: str = "dist"):
        self.output_dir = Path(output_dir)
        self.project_root = Path(__file__).parent.parent
        self.deployment_dir = self.output_dir / "service_DAG"
        
    def build(self):
        """构建部署包"""
        print("=" * 60)
        print("开始构建离线部署包")
        print("=" * 60)
        
        # 1. 创建目录结构
        self._create_directories()
        
        # 2. 下载依赖
        self._download_dependencies()
        
        # 3. 复制项目文件
        self._copy_project_files()
        
        # 4. 生成安装脚本
        self._generate_install_scripts()
        
        # 5. 生成README
        self._generate_readme()
        
        print("\n" + "=" * 60)
        print(f"✅ 部署包构建完成: {self.deployment_dir}")
        print("=" * 60)
    
    def _create_directories(self):
        """创建目录结构"""
        print("\n[1/5] 创建目录结构...")
        
        dirs = [
            self.deployment_dir,
            self.deployment_dir / "libs",
            self.deployment_dir / "logs",
            self.deployment_dir / "output",
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {d}")
    
    def _download_dependencies(self):
        """下载所有依赖包"""
        print("\n[2/5] 下载依赖包...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("  ⚠ requirements.txt不存在，跳过")
            return
        
        libs_dir = self.deployment_dir / "libs"
        
        try:
            # 使用pip download下载所有依赖
            cmd = [
                sys.executable, "-m", "pip", "download",
                "-r", str(requirements_file),
                "-d", str(libs_dir),
                "--no-deps"  # 不下载依赖的依赖
            ]
            
            print(f"  执行: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            print(f"  ✓ 依赖已下载到: {libs_dir}")
            
            # 生成冻结的requirements
            self._freeze_requirements(libs_dir)
            
        except subprocess.CalledProcessError as e:
            print(f"  ⚠ 下载失败: {e}")
            print("  提示: 可手动下载依赖包到 libs/ 目录")
    
    def _freeze_requirements(self, libs_dir: Path):
        """生成冻结的requirements文件"""
        frozen_file = self.deployment_dir / "requirements_frozen.txt"
        
        # 获取已安装包的版本
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"],
                capture_output=True,
                text=True,
                check=True
            )
            
            with open(frozen_file, "w") as f:
                f.write("# 冻结的依赖版本\n")
                f.write("# 生成时间: " + str(Path(__file__).stat().st_mtime) + "\n\n")
                f.write(result.stdout)
            
            print(f"  ✓ 已生成: {frozen_file}")
            
        except Exception as e:
            print(f"  ⚠ 生成冻结文件失败: {e}")
    
    def _copy_project_files(self):
        """复制项目文件"""
        print("\n[3/5] 复制项目文件...")
        
        # 要复制的目录
        dirs_to_copy = [
            "core",
            "engine", 
            "plugins",
            "ui",
            "config",
            "tests",
            "docs",
            "deployment"
        ]
        
        for dir_name in dirs_to_copy:
            src = self.project_root / dir_name
            dst = self.deployment_dir / dir_name
            
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"  ✓ {dir_name}/")
        
        # 复制主要文件
        files_to_copy = [
            "main_optimized.py",
            "quick_verify.py",
            "requirements.txt",
            "README.md",
            "pytest.ini"
        ]
        
        for file_name in files_to_copy:
            src = self.project_root / file_name
            dst = self.deployment_dir / file_name
            
            if src.exists():
                shutil.copy2(src, dst)
                print(f"  ✓ {file_name}")
    
    def _generate_install_scripts(self):
        """生成安装脚本"""
        print("\n[4/5] 生成安装脚本...")
        
        # Windows安装脚本
        install_bat = self.deployment_dir / "install.bat"
        with open(install_bat, "w") as f:
            f.write("""@echo off
REM 离线安装脚本

echo ========================================
echo 安装 DAG 工业视觉系统
echo ========================================

REM 检查Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [1/3] 安装依赖包...
python -m pip install --no-index --find-links=libs -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo 警告: 部分依赖安装失败
)

echo.
echo [2/3] 验证安装...
python quick_verify.py

echo.
echo [3/3] 创建日志目录...
if not exist logs mkdir logs
if not exist output mkdir output

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 运行系统: python main_optimized.py
echo 查看文档: docs\\USER_MANUAL.md
echo.
pause
""")
        print(f"  ✓ {install_bat.name}")
        
        # Linux安装脚本
        install_sh = self.deployment_dir / "install.sh"
        with open(install_sh, "w") as f:
            f.write("""#!/bin/bash
# 离线安装脚本

echo "========================================"
echo "安装 DAG 工业视觉系统"
echo "========================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

echo ""
echo "[1/3] 安装依赖包..."
python3 -m pip install --no-index --find-links=libs -r requirements.txt

echo ""
echo "[2/3] 验证安装..."
python3 quick_verify.py

echo ""
echo "[3/3] 创建目录..."
mkdir -p logs output

echo ""
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "运行系统: python3 main_optimized.py"
echo "查看文档: docs/USER_MANUAL.md"
""")
        install_sh.chmod(0o755)
        print(f"  ✓ {install_sh.name}")
    
    def _generate_readme(self):
        """生成部署包README"""
        print("\n[5/5] 生成README...")
        
        readme = self.deployment_dir / "README_INSTALL.txt"
        with open(readme, "w", encoding="utf-8") as f:
            f.write("""
========================================
DAG 工业视觉系统 - 离线部署包
========================================

版本: 1.0.0
构建时间: 2026-01-30

----------------------------------------
快速安装
----------------------------------------

Windows:
  1. 双击运行 install.bat
  2. 等待安装完成
  3. 运行: python main_optimized.py

Linux:
  1. chmod +x install.sh
  2. ./install.sh
  3. python3 main_optimized.py

----------------------------------------
目录结构
----------------------------------------

service_DAG/
├── core/           # 核心模块
├── engine/         # 执行引擎
├── plugins/        # 插件系统
├── config/         # 配置文件
├── libs/           # 依赖包（离线）
├── docs/           # 文档
├── deployment/     # 部署工具
├── install.bat     # Windows安装脚本
├── install.sh      # Linux安装脚本
└── main_optimized.py  # 主程序

----------------------------------------
环境要求
----------------------------------------

- Python 3.8+
- Windows 10/11 或 Linux
- 2GB+ 磁盘空间
- 4GB+ 内存

----------------------------------------
文档
----------------------------------------

- 用户手册: docs/USER_MANUAL.md
- 开发指南: docs/DEVELOPER_GUIDE.md
- 部署指南: deployment/README_DEPLOYMENT.md
- API参考: docs/API_REFERENCE.md

----------------------------------------
故障排查
----------------------------------------

1. 安装失败
   - 检查Python版本
   - 手动安装: pip install -r requirements.txt

2. 验证失败
   - 运行: python quick_verify.py
   - 查看错误信息

3. 运行失败
   - 查看日志: logs/system.log
   - 检查配置: config/pipeline.json

----------------------------------------
技术支持
----------------------------------------

- 查看文档目录
- 运行验证脚本
- 检查日志文件

========================================
""")
        print(f"  ✓ {readme.name}")


def main():
    """主函数"""
    builder = DeploymentBuilder()
    builder.build()
    
    print("\n提示:")
    print("  1. 将 dist/service_DAG/ 目录打包为 zip")
    print("  2. 在目标机器上解压")
    print("  3. 运行 install.bat (Windows) 或 install.sh (Linux)")


if __name__ == "__main__":
    main()
