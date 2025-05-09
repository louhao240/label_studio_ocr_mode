# 轻量级中文OCR识别服务

这是一个为Label Studio设计的轻量级中文OCR识别服务，使用PaddleOCR作为后端，专为低内存环境（1GB内存）优化。

## 功能特点

- 针对中文文本优化的OCR识别
- 轻量级设计，适合内存受限环境（1GB）
- 自动识别各种文本类型（标题、段落、表格、数字、日期等）
- 支持Windows和Linux平台
- 提供置信度评估
- 支持用户自定义标签

## 系统要求

- Python 3.7+ 
- 1GB内存（至少）
- Label Studio 1.4.0+

## 文件说明

- `model.py` - OCR模型实现
- `_wsgi.py` - Web服务器实现
- `config.json` - 配置文件
- `start.sh`/`start.bat` - 启动脚本（Linux/Windows）
- `stop.sh`/`stop.bat` - 停止脚本（Linux/Windows）
- `chinese-ocr-template.xml` - Label Studio标注模板
- `requirements.txt` - 依赖包列表

## 安装与使用

### Linux系统

1. 克隆或下载本项目到服务器
2. 进入项目目录
3. 执行启动脚本：
   ```
   chmod +x start.sh stop.sh
   ./start.sh
   ```
4. 如需使用已有的Python虚拟环境：
   ```
   ./start.sh --use-venv /path/to/your/venv
   ```
5. 第一次启动时会自动下载PaddleOCR模型，请耐心等待

### Windows系统

1. 克隆或下载本项目到服务器
2. 进入项目目录
3. 双击执行`start.bat`或在命令行运行：
   ```
   start.bat
   ```
4. 如需使用已有的Python虚拟环境：
   ```
   start.bat --use-venv C:\path\to\your\venv
   ```
5. 第一次启动时会自动下载PaddleOCR模型，请耐心等待

### 在Label Studio中配置

1. 在Label Studio中创建新项目，选择图像分类任务类型
2. 在项目设置中导入标注模板：`chinese-ocr-template.xml`
3. 在项目设置->ML后端中添加URL：`http://localhost:9090`
4. 上传中文图像开始标注

## 内存优化措施

为适应1GB内存环境，本项目采取了以下优化：

1. 使用PaddleOCR的轻量级模型
2. 限制CPU线程使用数量为1
3. 对大图像进行预处理和缩放
4. 禁用不必要的模型组件（角度分类器等）
5. 主动垃圾回收
6. 通过WSGI服务器限制并发连接

## 标签类型说明

本系统可以自动判断以下文本类型：

- 文本 - 默认类型
- 标题 - 较短且置信度高的文本
- 段落 - 较长的文本块
- 表格 - 包含表格相关关键词
- 数字 - 纯数字内容
- 日期 - 含有日期格式的文本
- 姓名 - 识别为人名的文本
- 地址 - 识别为地址的文本
- 电话 - 识别为电话号码的文本
- 邮箱 - 识别为电子邮件的文本
- 证件号 - 识别为身份证或其他证件号码的文本
- 组织 - 识别为组织名称的文本
- 价格 - 识别为价格的文本
- 时间 - 识别为时间的文本

## 常见问题

### 中文显示乱码

如果遇到中文乱码问题，请检查：
1. 确保启动脚本中设置了正确的字符编码（UTF-8）
2. 确保Label Studio前端正确显示中文
3. 检查日志文件中是否有编码相关错误

### 内存不足

如遇到内存不足问题：
1. 减小处理的图像尺寸（在`config.json`中修改`det_limit_side_len`值）
2. 确保系统中没有其他占用大量内存的进程
3. 考虑增加内存交换空间（swap）

### 服务无法启动

如果服务无法启动：
1. 检查端口是否被占用
2. 检查Python环境是否正确安装
3. 查看日志文件中的错误信息

## 停止服务

- Linux: `./stop.sh`
- Windows: `stop.bat`

## 自定义配置

编辑`config.json`文件可修改模型参数、标签定义和服务器配置。 