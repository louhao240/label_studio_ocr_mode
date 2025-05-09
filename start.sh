#!/bin/bash

set -e

# 设置脚本字符编码为UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "启动中文OCR服务"
echo "================"

# 检查端口是否被占用
PORT=9090
if [ -n "$(lsof -i:$PORT)" ]; then
    echo "错误: 端口 $PORT 已被占用，请停止占用该端口的程序或修改配置文件的端口设置"
    exit 1
fi

# 判断是否要使用已有的虚拟环境
if [ -n "$1" ] && [ "$1" = "--use-venv" ] && [ -n "$2" ]; then
    echo "使用指定的Python虚拟环境: $2"
    VENV_PATH="$2"
    source "$VENV_PATH/bin/activate"
else
    # 检查是否有虚拟环境
    if [ ! -d "venv" ]; then
        echo "创建Python虚拟环境..."
        python3 -m venv venv
    fi

    # 激活虚拟环境
    echo "激活虚拟环境..."
    source venv/bin/activate
    
    # 安装依赖
    echo "安装依赖..."
    pip install -r requirements.txt
fi

# 创建模型目录
if [ ! -d "models" ]; then
    echo "创建模型目录结构..."
    mkdir -p models/det
    mkdir -p models/rec
fi

# 启动服务
echo "启动OCR服务，端口: $PORT"
nohup gunicorn -w 1 -b 0.0.0.0:$PORT _wsgi:application > ocr_server.log 2>&1 &

# 保存PID
echo $! > ocr_server.pid
echo "服务已启动，PID: $(cat ocr_server.pid)"
echo "日志文件: $SCRIPT_DIR/ocr_server.log"
echo ""
echo "使用方法:"
echo "- 在Label Studio中创建项目，选择图像分类任务类型"
echo "- 导入标签模板: $SCRIPT_DIR/chinese-ocr-template.xml"
echo "- 在项目设置 -> ML后端 中添加URL: http://localhost:$PORT"
echo ""
echo "停止服务: ./stop.sh" 