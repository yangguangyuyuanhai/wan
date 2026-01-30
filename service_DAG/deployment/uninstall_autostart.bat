@echo off
REM 卸载开机自启动脚本

echo 正在卸载开机自启动...

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=DAG_Watchdog.lnk

if exist "%STARTUP_DIR%\%SHORTCUT_NAME%" (
    del "%STARTUP_DIR%\%SHORTCUT_NAME%"
    echo 开机自启动已卸载
) else (
    echo 未找到自启动项
)

pause
