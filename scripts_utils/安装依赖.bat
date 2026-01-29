@echo off
chcp 65001 >nul
echo ========================================
echo    依赖安装工具
echo ========================================
echo.
echo 使用环境: label_studio
echo.

echo 正在检查环境...
C:\Users\YRQ\miniconda3\_conda.exe env list | findstr "label_studio"
if errorlevel 1 (
    echo.
    echo ✗ label_studio环境不存在！
    echo.
    set /p create=是否创建环境？(Y/N): 
    if /i "%create%"=="Y" (
        echo 正在创建环境...
        C:\Users\YRQ\miniconda3\_conda.exe create -n label_studio python=3.9 -y
        if errorlevel 1 (
            echo ✗ 环境创建失败！
            pause
            exit /b 1
        )
        echo ✓ 环境创建成功
    ) else (
        echo 取消安装
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo 开始安装依赖包...
echo ========================================
echo.

echo [1/6] 安装PyQt5...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio pip install PyQt5 PyQt5-tools
if errorlevel 1 (
    echo ✗ PyQt5安装失败！
    goto error
)
echo ✓ PyQt5安装完成

echo.
echo [2/6] 安装OpenCV...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio pip install opencv-python
if errorlevel 1 (
    echo ✗ OpenCV安装失败！
    goto error
)
echo ✓ OpenCV安装完成

echo.
echo [3/6] 安装NumPy...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio pip install numpy
if errorlevel 1 (
    echo ✗ NumPy安装失败！
    goto error
)
echo ✓ NumPy安装完成

echo.
echo [4/6] 安装其他依赖...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio pip install pillow
if errorlevel 1 (
    echo ✗ 其他依赖安装失败！
    goto error
)
echo ✓ 其他依赖安装完成

echo.
echo [5/6] 安装YOLO (可选)...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio pip install ultralytics
if errorlevel 1 (
    echo ⚠ YOLO安装失败（可选，不影响其他功能）
) else (
    echo ✓ YOLO安装完成
)

echo.
echo [6/6] 验证安装...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python -c "import PyQt5; import cv2; import numpy; print('所有依赖验证通过')"
if errorlevel 1 (
    echo ✗ 依赖验证失败！
    goto error
)

echo.
echo ========================================
echo ✓ 所有依赖安装完成！
echo ========================================
echo.
echo 您现在可以运行：
echo - 检查环境.bat (验证环境)
echo - 一键启动所有版本.bat (启动系统)
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo ✗ 依赖安装失败！
echo ========================================
echo.
echo 请检查：
echo 1. 网络连接是否正常
echo 2. pip源是否可用
echo 3. 磁盘空间是否充足
echo.
pause
exit /b 1
