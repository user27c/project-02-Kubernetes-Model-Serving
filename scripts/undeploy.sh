#!/bin/bash

# ============================================================================
# Kubernetes Model Serving - 一键取消部署脚本
# ============================================================================
# 此脚本会删除所有部署的资源
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

# ============================================================================
# 确认操作
# ============================================================================
log_warning "警告：此操作将删除所有部署的资源！"
echo ""
read -p "确定要取消部署吗？(yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "操作已取消"
    exit 0
fi

NAMESPACE="ml-serving"

# ============================================================================
# 步骤 1：删除 Kubernetes 资源
# ============================================================================
log_info "步骤 1: 删除 Kubernetes 资源..."

# 删除 HPA
if kubectl get hpa model-api-hpa -n $NAMESPACE &> /dev/null; then
    log_info "删除 HPA..."
    kubectl delete -f kubernetes/hpa.yaml -n $NAMESPACE --ignore-not-found=true
    log_success "HPA 已删除"
fi

# 删除 ServiceMonitor
if kubectl get servicemonitor model-api-monitor -n $NAMESPACE &> /dev/null 2>&1; then
    log_info "删除 ServiceMonitor..."
    kubectl delete -f monitoring/servicemonitor.yaml -n $NAMESPACE --ignore-not-found=true
    log_success "ServiceMonitor 已删除"
fi

# 删除 ConfigMap
if kubectl get configmap model-config -n $NAMESPACE &> /dev/null; then
    log_info "删除 ConfigMap..."
    kubectl delete -f kubernetes/configmap.yaml -n $NAMESPACE --ignore-not-found=true
    log_success "ConfigMap 已删除"
fi

# 删除 Ingress
if kubectl get ingress model-api-ingress -n $NAMESPACE &> /dev/null; then
    log_info "删除 Ingress..."
    kubectl delete -f kubernetes/ingress.yaml -n $NAMESPACE --ignore-not-found=true
    log_success "Ingress 已删除"
fi

# 删除 Service
log_info "删除 Service..."
kubectl delete -f kubernetes/service.yaml -n $NAMESPACE --ignore-not-found=true
log_success "Service 已删除"

# 删除 Deployment
log_info "删除 Deployment..."
kubectl delete -f kubernetes/deployment.yaml -n $NAMESPACE --ignore-not-found=true
log_success "Deployment 已删除"

# ============================================================================
# 步骤 2：等待资源删除完成
# ============================================================================
log_info "步骤 2: 等待资源删除完成..."

TIMEOUT=60
INTERVAL=2
ELAPSED=0

log_info "等待 Pod 完全终止..."

while [ $ELAPSED -lt $TIMEOUT ]; do
    POD_COUNT=$(kubectl get pods -n $NAMESPACE -l app=model-api --no-headers 2>/dev/null | wc -l || echo "0")
    
    if [ "$POD_COUNT" -eq 0 ]; then
        log_success "所有 Pod 已终止"
        break
    fi
    
    echo -ne "\r等待中... (${ELAPSED}s/${TIMEOUT}s) - 剩余 Pod: $POD_COUNT"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""

# ============================================================================
# 步骤 3：删除命名空间（可选）
# ============================================================================
log_info "步骤 3: 删除命名空间..."

if kubectl get namespace $NAMESPACE &> /dev/null; then
    read -p "是否要删除命名空间 '$NAMESPACE'？(yes/no): " -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "删除命名空间 $NAMESPACE..."
        kubectl delete namespace $NAMESPACE
        log_success "命名空间 $NAMESPACE 已删除"
    else
        log_info "保留命名空间 $NAMESPACE"
    fi
fi

# ============================================================================
# 步骤 4：显示删除状态
# ============================================================================
log_info "步骤 4: 显示删除状态..."

echo ""
echo "=== 命名空间 $NAMESPACE 中的资源 ==="
kubectl get all -n $NAMESPACE 2>/dev/null || echo "命名空间不存在或无资源"

echo ""
log_success "=========================================="
log_success "取消部署完成！"
log_success "=========================================="
echo ""
log_info "后续操作："
log_info "  1. 重新部署：./scripts/deploy.sh"
log_info "  2. 查看集群资源：kubectl get all -A"
log_info "  3. 查看命名空间：kubectl get namespaces"
echo ""
