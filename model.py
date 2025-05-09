import os
import gc
import time
import json
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image
from io import BytesIO
import base64
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OcrModel:
    def __init__(self):
        self.model = None
        self.labels = None
        self.load_config()
        self.load_model()
        
    def load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.labels = config.get('labels', {
                        'default': '文本',
                        'title': '标题',
                        'paragraph': '段落',
                        'table': '表格',
                        'number': '数字',
                        'date': '日期'
                    })
                    logger.info("配置文件加载成功")
            else:
                logger.warning("配置文件不存在，使用默认标签")
                self.labels = {
                    'default': '文本',
                    'title': '标题',
                    'paragraph': '段落',
                    'table': '表格',
                    'number': '数字',
                    'date': '日期'
                }
        except Exception as e:
            logger.error(f"加载配置文件出错: {str(e)}")
            self.labels = {
                'default': '文本',
                'title': '标题',
                'paragraph': '段落',
                'table': '表格',
                'number': '数字',
                'date': '日期'
            }
    
    def load_model(self):
        """加载OCR模型，使用轻量级配置"""
        try:
            # 使用极简配置和轻量级模型
            self.model = PaddleOCR(
                use_angle_cls=False,  # 禁用方向分类，节省内存
                lang="ch",  # 中文模型
                use_gpu=False,  # 禁用GPU
                enable_mkldnn=False,  # 禁用MKL-DNN加速
                cpu_threads=1,  # 限制CPU线程数为1
                det_model_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "det"),
                rec_model_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "rec"),
                det_limit_side_len=960,  # 限制检测图像尺寸
                det_limit_type='max',
                rec_batch_num=1,  # 限制识别批次大小
                max_text_length=25,  # 限制最大文本长度
                use_space_char=True  # 启用空格字符识别
            )
            logger.info("OCR模型加载成功")
        except Exception as e:
            logger.error(f"OCR模型加载失败: {str(e)}")
            raise
    
    def _get_text_type(self, text, confidence):
        """根据文本内容和置信度智能判断文本类型"""
        # 纯数字判断
        if text.replace('.', '').isdigit():
            return self.labels.get('number', '数字')
        
        # 日期格式判断
        date_patterns = ['-', '/', '年', '月', '日']
        if any(p in text for p in date_patterns) and sum(c.isdigit() for c in text) > len(text) * 0.3:
            return self.labels.get('date', '日期')
        
        # 表格相关判断
        table_indicators = ['表', '项目', '序号', '合计', '小计']
        if any(indicator in text for indicator in table_indicators):
            return self.labels.get('table', '表格')
        
        # 标题判断
        if len(text) < 20 and confidence > 0.85:
            return self.labels.get('title', '标题')
        
        # 段落判断
        if len(text) > 15:
            return self.labels.get('paragraph', '段落')
        
        # 默认文本
        return self.labels.get('default', '文本')

    def _preprocess_image(self, image_bytes):
        """预处理图像，调整大图像尺寸以节省内存"""
        try:
            img = Image.open(BytesIO(image_bytes))
            
            # 降低大图像的分辨率，最大边长限制在2000像素
            max_size = 2000
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 转回BytesIO对象
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=95)
                return buffer.getvalue()
            
            return image_bytes
        except Exception as e:
            logger.error(f"图像预处理失败: {str(e)}")
            return image_bytes
    
    def _convert_regions_to_image(self, image_data, regions):
        """
        根据regions裁剪原始图像
        image_data: base64编码的图像数据
        regions: Label Studio传递的区域坐标
        """
        try:
            # 解码图像
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            image = Image.open(BytesIO(image_bytes))
            
            result = []
            for region in regions:
                try:
                    x, y, width, height = region['x'], region['y'], region['width'], region['height']
                    
                    # 计算实际像素位置
                    img_width, img_height = image.size
                    x_pixel = int(x / 100.0 * img_width)
                    y_pixel = int(y / 100.0 * img_height)
                    width_pixel = int(width / 100.0 * img_width)
                    height_pixel = int(height / 100.0 * img_height)
                    
                    # 裁剪并确保边界不超出图像
                    right = min(x_pixel + width_pixel, img_width)
                    bottom = min(y_pixel + height_pixel, img_height)
                    
                    if right <= x_pixel or bottom <= y_pixel:
                        continue  # 跳过无效的裁剪
                    
                    cropped = image.crop((x_pixel, y_pixel, right, bottom))
                    result.append({
                        'region': region,
                        'image': cropped
                    })
                except Exception as e:
                    logger.error(f"处理单个区域失败: {str(e)}")
            
            return result
        except Exception as e:
            logger.error(f"转换区域到图像失败: {str(e)}")
            return []
    
    def predict(self, tasks, **kwargs):
        """
        模型预测入口
        tasks: Label Studio传递的任务数据
        """
        results = []
        start_time = time.time()
        
        for task in tasks:
            try:
                # 1. 解析任务数据
                image_data = task['data']['image']
                regions = task.get('predictions', [{}])[0].get('result', [])
                
                # 如果没有region，整个图像作为一个区域
                if not regions:
                    img_data = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
                    # 预处理大图像
                    img_data = self._preprocess_image(img_data)
                    ocr_result = self.model.ocr(img_data, cls=False)
                    
                    if not ocr_result or len(ocr_result) == 0 or len(ocr_result[0]) == 0:
                        results.append({
                            'result': [],
                            'model_version': 'PaddleOCR Lightweight Chinese'
                        })
                        continue
                    
                    all_texts = []
                    for line in ocr_result[0]:
                        # [[x1,y1],[x2,y2],...], text, confidence
                        box, (text, confidence) = line
                        
                        # 计算相对坐标
                        img = Image.open(BytesIO(img_data))
                        img_width, img_height = img.size
                        
                        # 计算边界框
                        x_min = min(point[0] for point in box) / img_width * 100
                        y_min = min(point[1] for point in box) / img_height * 100
                        x_max = max(point[0] for point in box) / img_width * 100
                        y_max = max(point[1] for point in box) / img_height * 100
                        
                        width = x_max - x_min
                        height = y_max - y_min
                        
                        text_type = self._get_text_type(text, confidence)
                        
                        all_texts.append({
                            'type': 'rectanglelabels',
                            'value': {
                                'x': x_min,
                                'y': y_min,
                                'width': width,
                                'height': height,
                                'rotation': 0,
                                'rectanglelabels': [text_type]
                            }
                        })
                        
                        all_texts.append({
                            'type': 'textarea',
                            'value': {
                                'x': x_min,
                                'y': y_min,
                                'width': width,
                                'height': height,
                                'rotation': 0,
                                'text': [text],
                                'score': float(confidence)
                            }
                        })
                    
                    results.append({
                        'result': all_texts,
                        'model_version': 'PaddleOCR Lightweight Chinese',
                        'score': sum(float(line[1][1]) for line in ocr_result[0]) / len(ocr_result[0]) if ocr_result[0] else 0
                    })
                    
                else:
                    # 处理指定区域
                    region_images = self._convert_regions_to_image(image_data, [r['value'] for r in regions if r['type'] == 'rectangle'])
                    
                    if not region_images:
                        results.append({
                            'result': [],
                            'model_version': 'PaddleOCR Lightweight Chinese'
                        })
                        continue
                    
                    all_texts = []
                    
                    for region_data in region_images:
                        region = region_data['region']
                        region_img = region_data['image']
                        
                        # 保存到BytesIO
                        img_byte_arr = BytesIO()
                        region_img.save(img_byte_arr, format=region_img.format if region_img.format else 'PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        # 预处理图像
                        img_byte_arr = self._preprocess_image(img_byte_arr)
                        
                        # OCR识别
                        ocr_result = self.model.ocr(img_byte_arr, cls=False)
                        
                        if not ocr_result or len(ocr_result) == 0 or len(ocr_result[0]) == 0:
                            continue
                        
                        # 组合文本结果
                        combined_text = " ".join([line[1][0] for line in ocr_result[0]])
                        avg_confidence = sum(float(line[1][1]) for line in ocr_result[0]) / len(ocr_result[0])
                        
                        text_type = self._get_text_type(combined_text, avg_confidence)
                        
                        # 添加矩形标签结果
                        all_texts.append({
                            'type': 'rectanglelabels',
                            'value': {
                                'x': region['x'],
                                'y': region['y'],
                                'width': region['width'],
                                'height': region['height'],
                                'rotation': 0,
                                'rectanglelabels': [text_type]
                            }
                        })
                        
                        # 添加文本区域结果
                        all_texts.append({
                            'type': 'textarea',
                            'value': {
                                'x': region['x'],
                                'y': region['y'],
                                'width': region['width'],
                                'height': region['height'],
                                'rotation': 0,
                                'text': [combined_text],
                                'score': float(avg_confidence)
                            }
                        })
                    
                    results.append({
                        'result': all_texts,
                        'model_version': 'PaddleOCR Lightweight Chinese',
                        'score': sum(float(a.get('value', {}).get('score', 0)) for a in all_texts if a.get('type') == 'textarea') / 
                                sum(1 for a in all_texts if a.get('type') == 'textarea') if any(a.get('type') == 'textarea' for a in all_texts) else 0
                    })
            
            except Exception as e:
                logger.error(f"处理任务出错: {str(e)}")
                results.append({
                    'result': [],
                    'model_version': 'PaddleOCR Lightweight Chinese'
                })
            
            # 主动进行垃圾回收，减少内存消耗
            gc.collect()
        
        logger.info(f"处理了 {len(tasks)} 个任务，耗时 {time.time() - start_time:.2f} 秒")
        return results 