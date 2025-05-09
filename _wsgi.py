#!/usr/bin/env python
import os
import sys
import json
import traceback
import logging
from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import HTTPException

# 设置编码为UTF-8，解决中文问题
if sys.stdout.encoding != 'UTF-8':
    if sys.version_info.major == 3:
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        reload(sys)
        sys.setdefaultencoding('utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ocr_server.log'), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 限制内存使用，适合1GB内存环境
try:
    import resource
    # 限制内存使用为800MB，保留200MB给系统
    resource.setrlimit(resource.RLIMIT_AS, (800 * 1024 * 1024, -1))
    logger.info("已设置内存限制为800MB")
except ImportError:
    logger.warning("无法导入resource模块，跳过内存限制设置")
except Exception as e:
    logger.warning(f"设置内存限制失败: {str(e)}")

# 创建Flask应用
app = Flask(__name__)

# 全局模型实例
model = None

@app.before_first_request
def initialize_model():
    """在第一个请求之前初始化模型"""
    global model
    try:
        from model import OcrModel
        model = OcrModel()
        logger.info("模型初始化成功")
    except Exception as e:
        logger.error(f"模型初始化失败: {str(e)}")
        logger.error(traceback.format_exc())

@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({"status": "ok"})

@app.route('/predict', methods=['POST'])
def predict():
    """预测接口"""
    global model
    if model is None:
        try:
            from model import OcrModel
            model = OcrModel()
            logger.info("模型初始化成功")
        except Exception as e:
            logger.error(f"模型初始化失败: {str(e)}")
            return Response(
                response=json.dumps({"error": f"模型初始化失败: {str(e)}"}),
                status=500,
                mimetype='application/json; charset=utf-8'
            )
    
    # 解析请求数据
    try:
        data = request.json
        logger.info(f"收到预测请求，数据大小: {len(json.dumps(data))} 字符")
        
        # 调用模型预测
        result = model.predict(data['tasks'])
        
        # 设置响应
        response = {
            'results': result
        }
        
        # 返回JSON响应，明确指定UTF-8编码
        return Response(
            response=json.dumps(response, ensure_ascii=False),
            status=200,
            mimetype='application/json; charset=utf-8'
        )
        
    except Exception as e:
        logger.error(f"预测失败: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            response=json.dumps({"error": f"预测失败: {str(e)}"}, ensure_ascii=False),
            status=500,
            mimetype='application/json; charset=utf-8'
        )

@app.errorhandler(Exception)
def handle_exception(e):
    """处理所有异常"""
    logger.error(f"服务器错误: {str(e)}")
    logger.error(traceback.format_exc())
    
    # 判断是否为HTTP异常
    if isinstance(e, HTTPException):
        return Response(
            response=json.dumps({"error": str(e)}, ensure_ascii=False),
            status=e.code,
            mimetype='application/json; charset=utf-8'
        )
    
    # 处理其他异常
    return Response(
        response=json.dumps({"error": str(e)}, ensure_ascii=False),
        status=500,
        mimetype='application/json; charset=utf-8'
    )

# 主函数入口
if __name__ == '__main__':
    # 获取端口
    port = int(os.environ.get('PORT', 9090))
    
    # 启动服务器
    initialize_model()
    app.run(host='0.0.0.0', port=port, debug=False)
    
# WSGI入口
application = app 