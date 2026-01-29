@echo off
chcp 65001 >nul
echo ============================================================
echo Qt GUI版本测试
echo ============================================================
echo.

REM 激活conda环境并运行测试
call C:\Users\YRQ\miniconda3\Scripts\activate.bat label_studio

echo 【测试1】Qt模块导入测试
echo ------------------------------------------------------------
python test_qt.py
echo.

echo 【测试2】GUI启动测试
echo ------------------------------------------------------------
python test_gui_startup.py
echo.

echo ============================================================
echo 测试完成
echo ============================================================
echo.
echo 按任意键退出...
pause >nul
