#!/bin/bash

# ============================================================================
# Kubernetes Model Serving - 一键部署脚本
# ============================================================================
# 此脚本会自动部署整个项目到 Kubernetes 集群
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

check_command kubectl
check_command docker

# 检查 Kubernetes 集群连接
log_info "检查 Kubernetes 集群连接..."
if ! kubectl cluster-info &> /dev/null; then
    log_error "无法连接到 Kubernetes 集群"
    log_info "请确保："
    log_info "  1. k3s/minikube 正在运行"
    log_info "  2. kubeconfig 配置正确"
    exit 1
fi

log_success "Kubernetes 集群连接正常"

# ============================================================================
# 步骤 2：创建命名空间
# ============================================================================
log_info "步骤 2: 创建命名空间..."

NAMESPACE="ml-serving"
if kubectl get namespace $NAMESPACE &> /dev/null; then
    log_warning "命名空间 $NAMESPACE 已存在，跳过创建"
else
    kubectl create namespace $NAMESPACE
    log_success "命名空间 $NAMESPACE 创建成功"
fi

# ============================================================================
# 步骤 3：部署应用
# ============================================================================
log_info "步骤 3: 部署应用..."

# 部署 Deployment
log_info "部署 Deployment..."
kubectl apply -f kubernetes/deployment.yaml -n $NAMESPACE
log_success "Deployment 部署完成"

# 部署 Service
log_info "部署 Service..."
kubectl apply -f kubernetes/service.yaml -n $NAMESPACE
log_success "Service 部署完成"

# ============================================================================
# 步骤 4：部署可选组件
# ============================================================================
log_info "步骤 4: 部署可选组件..."

# 部署 ConfigMap（如果存在）
if [ -f "kubernetes/configmap.yaml" ]; then
    log_info "部署 ConfigMap..."
    kubectl apply -f kubernetes/configmap.yaml -n $NAMESPACE
    log_success "ConfigMap 部署完成"
fi

# 部署 ServiceMonitor（如果存在）
if [ -f "monitoring/servicemonitor.yaml" ]; then
    log_info "部署 ServiceMonitor..."
    if kubectl apply -f monitoring/servicemonitor.yaml -n $NAMESPACE 2>/dev/null; then
        log_success "ServiceMonitor 部署完成"
    else
        log_warning "ServiceMonitor 部署失败（可能需要 Prometheus Operator）"
    fi
fi

# 部署 HPA（如果存在）
if [ -f "kubernetes/hpa.yaml" ]; then
    log_info "部署 HPA..."
    kubectl apply -f kubernetes/hpa.yaml -n $NAMESPACE
    log_success "HPA 部署完成"
fi

# ============================================================================
# 步骤 5：等待 Pod 就绪
# ============================================================================
log_info "步骤 5: 等待 Pod 就绪..."

TIMEOUT=300  # 5 分钟超时
INTERVAL=5
ELAPSED=0

log_info "等待 Deployment 就绪 (超时：${TIMEOUT}秒)..."

while [ $ELAPSED -lt $TIMEOUT ]; do
    READY=$(kubectl get deployment model-api -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    DESIRED=$(kubectl get deployment model-api -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    
    if [ "$READY" == "$DESIRED" ] && [ "$READY" != "0" ]; then
        log_success "所有 Pod 已就绪 ($READY/$DESIRED)"
        break
    fi
    
    echo -ne "\r等待中... (${ELAPSED}s/${TIMEOUT}s) - 当前就绪：$READY/$DESIRED"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""

if [ $ELAPSED -ge $TIMEOUT ]; then
    log_error "等待超时，Pod 未完全就绪"
    log_warning "检查 Pod 状态：kubectl get pods -n $NAMESPACE"
    log_warning "查看 Pod 日志：kubectl logs deployment/model-api -n $NAMESPACE"
else
    log_success "部署完成！"
fi

# ============================================================================
# 步骤 6：显示部署状态
# ============================================================================
log_info "步骤 6: 显示部署状态..."

echo ""
echo "=== Deployment 状态 ==="
kubectl get deployment -n $NAMESPACE

echo ""
echo "=== Pod 状态 ==="
kubectl get pods -n $NAMESPACE

echo ""
echo "=== Service 状态 ==="
kubectl get svc -n $NAMESPACE

echo ""
log_success "=========================================="
log_success "部署完成！"
log_success "=========================================="
echo ""
log_info "后续操作："
log_info "  1. 查看 Pod 日志：kubectl logs deployment/model-api -n $NAMESPACE"
log_info "  2. 端口转发测试：kubectl port-forward svc/model-api-service 8080:80 -n $NAMESPACE"
log_info "  3. 访问健康检查：curl http://localhost:8080/health"
log_info "  4. 运行测试：./scripts/test.sh"
echo ""
