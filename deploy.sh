#!/bin/bash

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   YiXuanBao 项目部署脚本${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

# 检查 docker-compose 或 docker compose
COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo -e "${RED}❌ Docker Compose 未安装${NC}"
        exit 1
    fi
fi

# 检查 .env.production
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ 未找到 .env.production 文件${NC}"
    echo -e "${YELLOW}请先创建 .env.production 并配置参数${NC}"
    echo -e "${YELLOW}参考 .env.production.example${NC}"
    exit 1
fi

# 检查占位符
if grep -q "YOUR_SERVER_IP\|CHANGE_THIS" .env.production; then
    echo -e "${RED}❌ .env.production 中包含占位符，请先填写实际值${NC}"
    exit 1
fi

# 1. 拉取最新代码
echo -e "\n${YELLOW}📥 [1/6] 拉取最新代码...${NC}"
git pull origin main || {
    echo -e "${RED}❌ Git pull 失败${NC}"
    exit 1
}
echo -e "${GREEN}   ✓ 代码更新成功${NC}"

# 2. 构建前端
echo -e "\n${YELLOW}📦 [2/6] 构建前端项目...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   安装依赖..."
    npm install || {
        echo -e "${RED}❌ npm install 失败${NC}"
        exit 1
    }
fi

npm run build || {
    echo -e "${RED}❌ 前端构建失败${NC}"
    exit 1
}

if [ ! -d "dist" ]; then
    echo -e "${RED}❌ dist 目录不存在，构建失败${NC}"
    exit 1
fi

echo -e "${GREEN}   ✓ 前端构建成功${NC}"
cd ..

# 3. 停止旧容器
echo -e "\n${YELLOW}🛑 [3/6] 停止旧容器...${NC}"
$COMPOSE_CMD down
echo -e "${GREEN}   ✓ 旧容器已停止${NC}"

# 4. 构建并启动新容器
echo -e "\n${YELLOW}🐳 [4/6] 构建并启动 Docker 容器...${NC}"
$COMPOSE_CMD up -d --build || {
    echo -e "${RED}❌ 容器启动失败${NC}"
    echo -e "${YELLOW}查看日志: $COMPOSE_CMD logs${NC}"
    exit 1
}
echo -e "${GREEN}   ✓ 容器启动成功${NC}"

# 5. 等待服务启动
echo -e "\n${YELLOW}⏳ [5/6] 等待服务启动...${NC}"
echo -n "   "
for i in {1..30}; do
    if $COMPOSE_CMD ps | grep -q "healthy\|Up"; then
        echo ""
        echo -e "${GREEN}   ✓ 服务启动完成${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# 6. 检查服务状态
echo -e "\n${YELLOW}📊 [6/6] 检查服务状态...${NC}"
$COMPOSE_CMD ps

# 7. 显示日志
echo -e "\n${YELLOW}📋 后端日志（最后20行）：${NC}"
$COMPOSE_CMD logs --tail=20 backend

# 完成
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}\n"

# 获取服务器 IP
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="YOUR_SERVER_IP"
fi

echo -e "🌐 访问地址:"
echo -e "   前端: ${BLUE}http://${SERVER_IP}${NC}"
echo -e "   API: ${BLUE}http://${SERVER_IP}/api/${NC}"
echo -e "   Django 管理后台: ${BLUE}http://${SERVER_IP}/django-admin/${NC}\n"

echo -e "📋 常用命令:"
echo -e "   查看日志: ${YELLOW}$COMPOSE_CMD logs -f${NC}"
echo -e "   重启服务: ${YELLOW}$COMPOSE_CMD restart${NC}"
echo -e "   停止服务: ${YELLOW}$COMPOSE_CMD down${NC}"
echo -e "   进入后端: ${YELLOW}$COMPOSE_CMD exec backend bash${NC}"
echo -e "   创建超级用户: ${YELLOW}$COMPOSE_CMD exec backend python manage.py createsuperuser${NC}\n"