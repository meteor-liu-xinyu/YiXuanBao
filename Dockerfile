FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/backend

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
# 注意：你的 requirements.txt 在根目录，所以从根目录复制
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# 复制整个 backend 目录
COPY backend/ /app/backend/

# 创建必要的目录
RUN mkdir -p /app/backend/staticfiles

EXPOSE 8000

# 复制启动脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]