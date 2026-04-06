
# ============================================================================
# SERVICEMONITOR 使用说明
# ============================================================================

# 前置条件：

# 1. 安装 Prometheus Operator
#    使用 Helm：
      helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
      helm repo update
      helm install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring --create-namespace
        
# 2. 验证 Prometheus Operator 是否在运行：
#      kubectl get pods -n monitoring
#      # 应能看到：prometheus-operator、prometheus-prometheus-0 等

# 3. 验证 ServiceMonitor CRD 是否存在：
#      kubectl get crd servicemonitors.monitoring.coreos.com

# 部署 ServiceMonitor：
#   kubectl apply -f servicemonitor.yaml -n ml-serving

# 验证 ServiceMonitor：
#   kubectl get servicemonitor -n ml-serving
#   kubectl describe servicemonitor model-api-monitor -n ml-serving

# 检查 Prometheus 是否在抓取数据：
#   1. 对 Prometheus 端口转发：
#      kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

#   2. 在浏览器打开: http://localhost:9090

#   3. 检查 targets：页面顶部 Status → Targets
#      应能看到 model-api 的 endpoints

#   4. 查询指标：Graph 页签
#      查询: model_api_requests_total
#      应能看到你的指标数据

# ============================================================================
# SERVICEMONITOR 匹配逻辑
# ============================================================================

# ServiceMonitor 如何找到 Service：

# 1. Prometheus Operator 监听 ServiceMonitor 资源
# 2. ServiceMonitor.spec.selector 匹配 Service 的标签
# 3. ServiceMonitor.spec.namespaceSelector 匹配命名空间
# 4. 对于每个匹配的 Service：
#    - 获取 Service 端点（Pod 的 IP）
#    - 为每个端点生成抓取配置
#    - 更新 Prometheus 的配置
# 5. Prometheus 按指定间隔抓取端点

# Service 示例标签：
#   apiVersion: v1
#   kind: Service
#   metadata:
#     name: model-api-service
#     labels:
#       app: model-api  # ← ServiceMonitor 的 selector 匹配此标签

# ServiceMonitor 示例 selector：
#   selector:
#     matchLabels:
#       app: model-api  # ← 匹配 Service 的标签

---

# ============================================================================
# PROMETHEUS OPERATOR 架构
# ============================================================================

# ┌─────────────────────────────────────────────────────────────┐
# │                 Prometheus Operator                         │
# │                                                             │
# │  监听：                                                     │
# │  - Prometheus CRD                                           │
# │  - ServiceMonitor CRD                                       │
# │  - PodMonitor CRD                                           │
# │  - PrometheusRule CRD （告警）                              │
# │                                                             │
# │  生成：                                                     │
# │  - Prometheus StatefulSet                                   │
# │  - Prometheus ConfigMap（抓取配置）                         │
# │  - 用于服务发现的 RBAC 规则                                 │
# └─────────────────────────────────────────────────────────────┘
#                           │
#                           ▼
# ┌─────────────────────────────────────────────────────────────┐
# │                   Prometheus Server                         │
# │                                                             │
# │  1. 读取生成的 ConfigMap                                    │
# │  2. 通过 K8s API 发现 Service                               │
# │  3. 抓取 /metrics 端点                                      │
# │  4. 存储时序数据                                            │
# └─────────────────────────────────────────────────────────────┘
#                           │
#                           ▼
# ┌─────────────────────────────────────────────────────────────┐
# │                      你的服务                               │
# │                                                             │
# │  Pods 暴露 /metrics 端点                                    │
# │  Prometheus 每 30 秒抓取一次                                │
# └─────────────────────────────────────────────────────────────┘

---

# ============================================================================
# SERVICEMONITOR 调试
# ============================================================================

# ServiceMonitor 未发现服务（Service）时：
#   1. 检查 ServiceMonitor 的标签是否与 Service 匹配：
#      kubectl get svc -n ml-serving --show-labels
#      kubectl get servicemonitor model-api-monitor -n ml-serving -o yaml | grep -A 3 selector
#
#   2. 检查命名空间选择器：
#      kubectl describe servicemonitor model-api-monitor -n ml-serving
#
#   3. 检查 Prometheus Operator 日志：
#      kubectl logs -n monitoring deployment/prometheus-operator

# 指标在 Prometheus 中未出现时：
#   1. 检查 Prometheus 的 targets：
#      kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
#      # 打开 http://localhost:9090/targets
#
#   2. 验证端点是否健康：
#      kubectl port-forward -n ml-serving svc/model-api-service 8080:80
#      curl http://localhost:8080/metrics
#
#   3. 检查 Prometheus 日志：
#      kubectl logs -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0

# Prometheus 无法抓取端点时：
#   - 检查 RBAC 权限
#   - 检查网络策略，确保 Prometheus 能访问 Service
#   - 检查 Service 端口名称与 ServiceMonitor 中配置是否一致

# ============================================================================
# SERVICEMONITOR 示例
# ============================================================================

# 示例 1：多个端点
#   endpoints:
#   - port: http
#     path: /metrics
#   - port: admin
#     path: /admin/metrics

# 示例 2：不同抓取间隔
#   endpoints:
#   - port: http
#     path: /metrics
#     interval: 30s  # 高频抓取
#   - port: admin
#     path: /admin/metrics
#     interval: 5m   # 低频抓取

# 示例 3：标签过滤
#   selector:
#     matchLabels:
#       app: model-api
#     matchExpressions:
#     - key: environment
#       operator: In
#       values: [production, staging]

# 示例 4：跨命名空间监控
#   namespaceSelector:
#     matchNames:
#     - ml-serving
#     - ml-serving-staging
#     - ml-serving-prod

---

# ============================================================================
# 最佳实践
# ============================================================================

# 1. 使用规范的标签选择器
#    - 服务间标签需标准化
#    - 对标签规范进行文档记录
#    - 标签选择器不要匹配到非目标服务

# 2. 设置合适的抓取间隔
#    - 30s：标准频率（兼顾实时性与负载）
#    - 15s：高频抓取（适用于实时看板）
#    - 1m-5m：低频抓取（适用于批处理、资源消耗大的指标）

# 3. 配置抓取超时时间
#    - 必须比 interval 短
#    - 考虑网络延迟
#    - 一般服务建议 10s

# 4. 谨慎使用重标签
#    - 仅在必要时使用（复杂度提升）
#    - 对 relabeling 规则做文档说明
#    - 用真实数据测试 relabeling

# 5. 关注指标基数
#    - 太多唯一标签组合会带来高内存消耗
#    - 避免 userId、时间戳等无界标签
#    - 不需要的高基数指标要丢弃

# 6. 命名空间隔离
#    - 使用 namespaceSelector 限定作用范围
#    - 防止错误监控到非目标服务
#    - 提升 Prometheus 性能

# ============================================================================
# 学习检查点
# ============================================================================

# 完成本文件后你应掌握：
# ✓ 理解什么是 ServiceMonitor 及其用途
# ✓ 知道 Prometheus Operator 如何使用 ServiceMonitor
# ✓ 通过标签选择器配置服务发现
# ✓ 设置抓取的间隔和超时时间
# ✓ 明白 ServiceMonitor 与手动配置的差异
# ✓ 调试 ServiceMonitor 的常见问题
# ✓ 指标采集的最佳实践
