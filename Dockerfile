FROM python:3.9-slim

# 安装 Tesseract
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

# 设置工作目录
WORKDIR /app

# 复制当前文件到容器中
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 启动应用
CMD ["python", "main.py"]
