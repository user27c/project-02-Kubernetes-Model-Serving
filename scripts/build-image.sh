#!/bin/bash

# ============================================================================
# 构建 Docker 镜像脚本
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 镜像名称和版本
IMAGE_NAME="model-api"
IMAGE_TAG="v1.0"

# 代理配置（如果使用代理，请取消注释并修改）
# export HTTP_PROXY=http://127.0.0.1:7890
# export HTTPS_PROXY=http://127.0.0.1:7890
# export NO_PROXY=localhost,127.0.0.1,.aliyuncs.com

log_info "开始构建 Docker 镜像..."
log_info "镜像名称：${IMAGE_NAME}:${IMAGE_TAG}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装"
    exit 1
fi

# 构建镜像（带代理支持）
log_info "执行 docker build..."
if [ -n "$HTTP_PROXY" ]; then
    log_info "使用代理：$HTTP_PROXY"
    docker build \
        --build-arg HTTP_PROXY=$HTTP_PROXY \
        --build-arg HTTPS_PROXY=$HTTPS_PROXY \
        -t ${IMAGE_NAME}:${IMAGE_TAG} .
else
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
fi

if [ $? -eq 0 ]; then
    log_success "镜像构建成功！"
    log_info "镜像信息："
    docker images | grep ${IMAGE_NAME}
    
    echo ""
    log_info "后续操作："
    log_info "  1. 本地测试：docker run -p 5000:5000 ${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "  2. 部署到 k3s：docker tag ${IMAGE_NAME}:${IMAGE_TAG} localhost:5000/${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "  3. 推送到本地仓库：docker push localhost:5000/${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "  4. 运行部署：./scripts/deploy.sh"
else
    log_error "镜像构建失败"
    exit 1
fi
