@echo off
REM 设置代码页为UTF-8
chcp 65001 > nul

echo 停止中文OCR服务
echo ================

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 检查PID文件是否存在
if not exist "ocr_server.pid" (
    echo 未找到PID文件，服务可能未运行
    exit /b 0
)

REM 获取PID
set /p PID=<ocr_server.pid

REM 检查进程是否存在
tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
if %ERRORLEVEL% NEQ 0 (
    echo 进程 %PID% 不存在，服务可能已停止
    del /f ocr_server.pid
    exit /b 0
)

REM 尝试停止进程
echo 正在停止进程 %PID%...
taskkill /PID %PID% /T /F

REM 检查是否成功停止
timeout /t 2 /nobreak > nul
tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
if %ERRORLEVEL% NEQ 0 (
    echo 服务已停止
) else (
    echo 警告: 无法停止进程 %PID%，请手动终止
)

REM 删除PID文件
del /f ocr_server.pid
echo OCR服务已停止 