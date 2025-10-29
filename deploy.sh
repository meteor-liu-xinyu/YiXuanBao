#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   YiXuanBao 一键部署${NC}"
echo -e "${GREEN}========================================${NC}\n"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    exit 1
fi

# 检查配置文件
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ 未找到 .env.production${NC}"
    exit 1
fi

# 构建前端
echo -e "${YELLOW}📦 [1/4] 构建前端...${NC}"
cd frontend
npm install
npm run build
cd ..

# 停止旧容器
echo -e "${YELLOW}🛑 [2/4] 停止旧容器...${NC}"
docker-compose down

# 启动新容器
echo -e "${YELLOW}🐳 [3/4] 启动容器...${NC}"
docker-compose up -d --build

# 等待服务启动
echo -e "${YELLOW}⏳ [4/4] 等待服务启动...${NC}"
sleep 15

# 显示状态
docker-compose ps

echo -e "\n${GREEN}✅ 部署完成！${NC}"
echo -e "🌐 访问: http://8.137.164.174\n"