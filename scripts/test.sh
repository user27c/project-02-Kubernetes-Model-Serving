#!/bin/bash

# ============================================================================
# Kubernetes Model Serving - 一键测试脚本
# ============================================================================
# 此脚本会自动安装测试依赖并运行所有测试
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# ============================================================================
# 步骤 1：检查前置条件
# ============================================================================
log_info "步骤 1: 检查前置条件..."

check_command python3
check_command pip3
check_command kubectl

# 检查 Kubernetes 集群连接
if ! kubectl cluster-info &> /dev/null; then
    log_error "无法连接到 Kubernetes 集群"
    exit 1
fi

log_success "前置条件检查通过"

# ============================================================================
# 步骤 2：安装测试依赖
# ============================================================================
log_info "步骤 2: 安装测试依赖..."

# 创建临时 requirements 文件
TEMP_REQUIREMENTS=$(mktemp)
cat > $TEMP_REQUIREMENTS << EOF
kubernetes>=28.0.0
requests>=2.31.0
pytest>=7.4.0
pytest-cov>=4.1.0
EOF

log_info "安装 Python 包..."
pip3 install -r $TEMP_REQUIREMENTS -q

# 清理临时文件
rm -f $TEMP_REQUIREMENTS

log_success "测试依赖安装完成"

# ============================================================================
# 步骤 3：检查部署状态
# ============================================================================
log_info "步骤 3: 检查部署状态..."

NAMESPACE="ml-serving"

# 检查命名空间
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    log_error "命名空间 $NAMESPACE 不存在"
    log_info "请先运行部署：./scripts/deploy.sh"
    exit 1
fi

# 检查 Deployment
if ! kubectl get deployment model-api -n $NAMESPACE &> /dev/null; then
    log_error "Deployment model-api 不存在"
    log_info "请先运行部署：./scripts/deploy.sh"
    exit 1
fi

# 检查 Pod 状态
READY=$(kubectl get deployment model-api -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
if [ "$READY" == "0" ]; then
    log_warning "Pod 未就绪，测试可能会失败"
    log_info "等待 Pod 就绪..."
    kubectl wait --for=condition=ready pod -l app=model-api -n $NAMESPACE --timeout=120s || true
fi

log_success "部署状态检查完成"

# ============================================================================
# 步骤 4：运行测试
# ============================================================================
log_info "步骤 4: 运行测试..."

echo ""
echo "=========================================="
echo "开始运行 Kubernetes 集成测试"
echo "=========================================="
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 运行 pytest
pytest tests/test_k8s.py -v --tb=short

# 获取退出码
TEST_EXIT_CODE=$?

echo ""
echo "=========================================="

# ============================================================================
# 步骤 5：显示测试结果
# ============================================================================
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_success "所有测试通过！"
else
    log_error "部分测试失败"
    log_info "查看详细失败信息，请运行：pytest tests/test_k8s.py -v"
fi

echo ""
log_info "测试报告已生成"
log_info "查看测试文档：tests/README_TESTS.md"
echo ""

exit $TEST_EXIT_CODE
