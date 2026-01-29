@echo off
chcp 65001 >nul
echo ========================================
echo    系统快速测试
echo ========================================
echo.
echo 使用环境: label_studio
echo.

echo [1/2] 测试后端模块...
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python test_system.py
if errorlevel 1 (
    echo.
    echo ✗ 后端模块测试失败！
    pause
    exit /b 1
)

echo.
echo [2/2] 测试Qt前端模块...
cd service_qt
C:\Users\YRQ\miniconda3\_conda.exe run -n label_studio python test_qt.py
if errorlevel 1 (
    echo.
    echo ✗ Qt前端测试失败！
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ========================================
echo ✓ 所有测试通过！系统可以正常运行
echo ========================================
pause
