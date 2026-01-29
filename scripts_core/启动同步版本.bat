@echo off
chcp 65001 >nul
echo ========================================
echo    工业视觉系统 - 同步版本
echo ========================================
echo.
echo 使用环境: label_studio
echo 运行模式: 开发模式
echo.

REM 切换到service_new根目录
cd /d %~dp0..

echo 正在启动系统...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python main.py

if errorlevel 1 (
    echo.
    echo 启动失败！请检查：
    echo 1. Conda环境 label_studio 是否存在
    echo 2. 相机设备是否连接
    echo 3. 依赖包是否已安装
    echo.
    pause
)
