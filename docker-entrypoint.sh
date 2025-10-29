#!/bin/bash
set -e

echo "=========================================="
echo "  YiXuanBao Backend Starting..."
echo "=========================================="

# 等待 MySQL 启动
echo "⏳ 等待MySQL数据库启动..."
while ! nc -z db 3306; do
  sleep 1
done
echo "✅ MySQL已启动！"

# 确保在 backend 目录
cd /app/backend

# 执行数据库迁移
echo "📊 执行数据库迁移..."
python manage.py migrate --noinput

# 收集静态文件
echo "📦 收集静态文件..."
python manage.py collectstatic --noinput

echo "🚀 启动Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    backend.wsgi:application