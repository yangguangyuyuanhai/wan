@echo off
REM 安装开机自启动脚本

echo 正在安装开机自启动...

set SCRIPT_DIR=%~dp0
set WATCHDOG_SCRIPT=%SCRIPT_DIR%watchdog.bat
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=DAG_Watchdog.lnk

REM 创建快捷方式到启动文件夹
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%STARTUP_DIR%\%SHORTCUT_NAME%'); $SC.TargetPath = '%WATCHDOG_SCRIPT%'; $SC.WorkingDirectory = '%SCRIPT_DIR%'; $SC.Save()"

if %ERRORLEVEL% EQU 0 (
    echo 开机自启动安装成功！
    echo 快捷方式位置: %STARTUP_DIR%\%SHORTCUT_NAME%
) else (
    echo 安装失败，请以管理员权限运行
)

pause
