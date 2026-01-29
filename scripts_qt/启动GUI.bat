@echo off
chcp 65001 >nul
echo ========================================
echo    工业视觉系统 - Qt GUI
echo ========================================
echo.
echo 使用环境: label_studio
echo.

REM 切换到service_qt目录
cd /d %~dp0..\service_qt

echo 正在启动GUI界面...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python run_gui.py

if errorlevel 1 (
    echo.
    echo 启动失败！请检查：
    echo 1. Conda环境 label_studio 是否存在
    echo 2. 依赖包是否已安装 ^(pip install -r requirements_qt.txt^)
    echo.
    pause
)
