@echo off
chcp 65001 >nul
echo ============================================================
echo Service_new 模块导入测试
echo ============================================================
echo.

REM 激活conda环境并运行测试
call C:\Users\YRQ\miniconda3\Scripts\activate.bat label_studio
python test_imports.py

echo.
echo 测试完成，按任意键退出...
pause >nul
