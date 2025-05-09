#!/bin/bash

set -e

# 设置脚本字符编码为UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "停止中文OCR服务"
echo "================"

# 检查PID文件是否存在
if [ ! -f "ocr_server.pid" ]; then
    echo "未找到PID文件，服务可能未运行"
    exit 0
fi

# 获取PID
PID=$(cat ocr_server.pid)

# 检查进程是否存在
if [ -z "$(ps -p $PID -o pid=)" ]; then
    echo "进程 $PID 不存在，服务可能已停止"
    rm -f ocr_server.pid
    exit 0
fi

# 尝试优雅停止
echo "正在停止进程 $PID..."
kill -15 $PID

# 等待最多5秒钟
for i in {1..5}; do
    if [ -z "$(ps -p $PID -o pid=)" ]; then
        echo "服务已停止"
        rm -f ocr_server.pid
        exit 0
    fi
    sleep 1
done

# 如果进程仍在运行，强制停止
if [ -n "$(ps -p $PID -o pid=)" ]; then
    echo "服务未响应，强制停止..."
    kill -9 $PID
    
    if [ -z "$(ps -p $PID -o pid=)" ]; then
        echo "服务已强制停止"
    else
        echo "无法停止服务，请手动终止进程 $PID"
    fi
fi

# 删除PID文件
rm -f ocr_server.pid
echo "OCR服务已停止" 