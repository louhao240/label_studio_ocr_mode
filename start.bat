@echo off
REM 设置代码页为UTF-8
chcp 65001 > nul

echo 启动中文OCR服务
echo ================

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 检查端口是否被占用
set PORT=9090
netstat -ano | findstr ":%PORT%" > nul
if %ERRORLEVEL% EQU 0 (
    echo 错误: 端口 %PORT% 已被占用，请停止占用该端口的程序或修改配置文件的端口设置
    exit /b 1
)

REM 判断是否要使用已有的虚拟环境
if "%1"=="--use-venv" (
    if not "%2"=="" (
        echo 使用指定的Python虚拟环境: %2
        set VENV_PATH=%2
        call "%VENV_PATH%\Scripts\activate.bat"
    ) else (
        echo 错误: 需要指定虚拟环境路径
        exit /b 1
    )
) else (
    REM 检查是否有虚拟环境
    if not exist "venv" (
        echo 创建Python虚拟环境...
        python -m venv venv
    )

    REM 激活虚拟环境
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
    
    REM 安装依赖
    echo 安装依赖...
    pip install -r requirements.txt
)

REM 创建模型目录
if not exist "models" (
    echo 创建模型目录结构...
    mkdir models\det
    mkdir models\rec
)

REM 获取Python可执行文件路径
where python > python_path.txt
set /p PYTHON_PATH=<python_path.txt
del python_path.txt

REM 启动服务
echo 启动OCR服务，端口: %PORT%
start /b "" "%PYTHON_PATH%" _wsgi.py > ocr_server.log 2>&1

REM 获取进程ID
timeout /t 1 /nobreak > nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%"') do (
    set PID=%%a
    goto :found_pid
)

:found_pid
if "%PID%"=="" (
    echo 警告: 无法获取进程ID，服务可能未正确启动
) else (
    echo %PID% > ocr_server.pid
    echo 服务已启动，PID: %PID%
)

echo 日志文件: %SCRIPT_DIR%ocr_server.log
echo.
echo 使用方法:
echo - 在Label Studio中创建项目，选择图像分类任务类型
echo - 导入标签模板: %SCRIPT_DIR%chinese-ocr-template.xml
echo - 在项目设置 -^> ML后端 中添加URL: http://localhost:%PORT%
echo.
echo 停止服务: stop.bat 