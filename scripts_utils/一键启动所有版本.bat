@echo off
chcp 65001 >nul
echo ========================================
echo    工业视觉系统 - 启动菜单
echo ========================================
echo.
echo 请选择要启动的版本：
echo.
echo [1] Qt GUI界面版本 (推荐)
echo [2] 同步版本 (命令行)
echo [3] 异步版本 (多相机)
echo [4] 运行系统测试
echo [5] 退出
echo.
set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" goto gui
if "%choice%"=="2" goto sync
if "%choice%"=="3" goto async
if "%choice%"=="4" goto test
if "%choice%"=="5" goto end

echo 无效选项！
pause
goto end

:gui
echo.
echo 正在启动Qt GUI界面...
cd /d %~dp0..
call scripts_qt\启动GUI.bat
goto end

:sync
echo.
echo 正在启动同步版本...
cd /d %~dp0..
call scripts_core\启动同步版本.bat
goto end

:async
echo.
echo 正在启动异步版本...
cd /d %~dp0..
call scripts_asyncio\启动异步版本.bat
goto end

:test
echo.
echo 正在运行系统测试...
cd /d %~dp0
call 快速测试.bat
goto end

:end
