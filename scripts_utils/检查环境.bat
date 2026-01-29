@echo off
chcp 65001 >nul
echo ========================================
echo    环境检查工具
echo ========================================
echo.

echo [1/5] 检查Conda...
C:\Users\YRQ\miniconda3\_conda.exe --version
if errorlevel 1 (
    echo ✗ Conda未找到！
    goto error
) else (
    echo ✓ Conda已安装
)

echo.
echo [2/5] 检查label_studio环境...
C:\Users\YRQ\miniconda3\_conda.exe env list | findstr "label_studio"
if errorlevel 1 (
    echo ✗ label_studio环境不存在！
    echo.
    echo 请创建环境：
    echo conda create -n label_studio python=3.9
    goto error
) else (
    echo ✓ label_studio环境存在
)

echo.
echo [3/5] 检查Python版本...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python --version
if errorlevel 1 (
    echo ✗ Python检查失败！
    goto error
) else (
    echo ✓ Python可用
)

echo.
echo [4/5] 检查PyQt5...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python -c "from PyQt5.QtCore import PYQT_VERSION_STR; print('PyQt5版本:', PYQT_VERSION_STR)"
if errorlevel 1 (
    echo ✗ PyQt5未安装！
    echo.
    echo 请安装：
    echo conda run -n label_studio pip install PyQt5
    goto error
) else (
    echo ✓ PyQt5已安装
)

echo.
echo [5/5] 检查OpenCV...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python -c "import cv2; print('OpenCV版本:', cv2.__version__)"
if errorlevel 1 (
    echo ✗ OpenCV未安装！
    echo.
    echo 请安装：
    echo conda run -n label_studio pip install opencv-python
    goto error
) else (
    echo ✓ OpenCV已安装
)

echo.
echo ========================================
echo ✓ 环境检查完成！所有依赖已就绪
echo ========================================
echo.
echo 您可以运行：
echo - 一键启动所有版本.bat (启动菜单)
echo - service_qt\启动GUI.bat (Qt界面)
echo - 启动同步版本.bat (命令行版本)
echo - service_asyncio\启动异步版本.bat (多相机版本)
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo ✗ 环境检查失败！请按照提示修复
echo ========================================
pause
exit /b 1
