@echo off
REM 守护进程脚本 - 监控主程序运行状态
REM 主程序崩溃时自动重启

setlocal enabledelayedexpansion

set MAIN_SCRIPT=main_optimized.py
set PYTHON_EXE=python
set MAX_RESTARTS=10
set RESTART_DELAY=5
set HEARTBEAT_FILE=heartbeat.txt
set HEARTBEAT_TIMEOUT=60
set LOG_FILE=logs\watchdog.log

set RESTART_COUNT=0

echo [%date% %time%] 守护进程启动 >> %LOG_FILE%

:MONITOR_LOOP
    REM 检查心跳文件
    if exist %HEARTBEAT_FILE% (
        REM 获取文件修改时间
        for %%F in (%HEARTBEAT_FILE%) do set FILE_TIME=%%~tF
        
        REM 简化检查：如果文件存在就认为程序运行正常
        echo [%date% %time%] 程序运行正常 >> %LOG_FILE%
        timeout /t 10 /nobreak >nul
        goto MONITOR_LOOP
    )
    
    REM 心跳文件不存在，检查进程
    tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        REM Python进程存在但无心跳，可能假死
        echo [%date% %time%] 警告：检测到程序假死 >> %LOG_FILE%
        taskkill /F /IM python.exe >nul 2>&1
    )
    
    REM 检查重启次数
    if !RESTART_COUNT! GEQ %MAX_RESTARTS% (
        echo [%date% %time%] 错误：达到最大重启次数，停止守护 >> %LOG_FILE%
        goto END
    )
    
    REM 重启程序
    set /a RESTART_COUNT+=1
    echo [%date% %time%] 启动程序 (第 !RESTART_COUNT! 次) >> %LOG_FILE%
    
    start /B %PYTHON_EXE% %MAIN_SCRIPT%
    
    REM 等待后继续监控
    timeout /t %RESTART_DELAY% /nobreak >nul
    goto MONITOR_LOOP

:END
echo [%date% %time%] 守护进程退出 >> %LOG_FILE%
endlocal
