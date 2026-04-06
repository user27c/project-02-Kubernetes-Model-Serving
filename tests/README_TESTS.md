# Kubernetes 测试运行指南

## 📋 测试概览

这个测试套件包含了 **24 个测试**，覆盖了 Kubernetes 部署的各个方面：

### 测试分类

| 测试类别 | 测试数量 | 说明 |
|---------|---------|------|
| **Deployment 测试** | 6 个 | 验证 Deployment 配置和状态 |
| **Pod 测试** | 4 个 | 验证 Pod 健康状态 |
| **Service 测试** | 5 个 | 验证 Service 配置和连接性 |
| **HPA 测试** | 5 个 | 验证自动伸缩配置 |
| **滚动更新测试** | 2 个 | 验证零停机部署 |
| **配置测试** | 2 个 | 验证 ConfigMap 使用 |
| **性能测试** | 2 个 | 验证延迟和吞吐量（慢测试） |
| **监控测试** | 2 个 | 验证 Prometheus 集成 |

## 🚀 快速开始

### 1. 前置条件

确保你已经完成以下部署：

```bash
# 1. 确保 k3s 正在运行
sudo systemctl start k3s

# 2. 确保命名空间已创建
kubectl create namespace ml-serving

# 3. 部署应用
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml

# 4. 等待 Pod 就绪
kubectl get pods -n ml-serving -w
```

### 2. 安装测试依赖

```bash
# 进入项目目录
cd /home/22-7/Dev/ai-infra-learn/ai-infra-project/junior-engineer/project-02-Kubernetes-Model-Serving

# 安装 Python 包
pip install kubernetes requests pytest
```

### 3. 运行所有测试

```bash
# 方法 1：使用 pytest（推荐）
pytest tests/test_k8s.py -v

# 方法 2：直接使用 Python
python tests/test_k8s.py
```

## 📖 运行特定测试

### 运行特定测试类

```bash
# 运行 Deployment 测试
pytest tests/test_k8s.py::TestDeployment -v

# 运行 Pod 测试
pytest tests/test_k8s.py::TestPods -v

# 运行 Service 测试
pytest tests/test_k8s.py::TestService -v

# 运行 HPA 测试
pytest tests/test_k8s.py::TestAutoScaling -v
```

### 运行单个测试

```bash
# 运行单个测试
pytest tests/test_k8s.py::TestDeployment::test_deployment_exists -v

# 运行健康检查测试
pytest tests/test_k8s.py::TestService::test_service_health_endpoint -v
```

### 跳过慢速测试

```bash
# 跳过标记为 @pytest.mark.slow 的测试
pytest tests/test_k8s.py -v -m "not slow"
```

### 仅运行慢速测试

```bash
# 只运行慢速测试（性能测试、滚动更新等）
pytest tests/test_k8s.py -v -m slow
```

## 📊 测试输出示例

### 成功输出

```
============================= test session starts ==============================
platform linux -- Python 3.9.16, pytest-7.4.0
collected 24 items

tests/test_k8s.py::TestDeployment::test_deployment_exists PASSED         [  4%]
tests/test_k8s.py::TestDeployment::test_deployment_replicas PASSED       [  8%]
tests/test_k8s.py::TestDeployment::test_deployment_image PASSED          [ 12%]
tests/test_k8s.py::TestDeployment::test_deployment_resource_limits PASSED [ 16%]
tests/test_k8s.py::TestDeployment::test_deployment_health_probes PASSED  [ 20%]
tests/test_k8s.py::TestDeployment::test_deployment_update_strategy PASSED [ 24%]
tests/test_k8s.py::TestPods::test_all_pods_running PASSED                [ 29%]
tests/test_k8s.py::TestPods::test_all_pods_ready PASSED                  [ 33%]
...

======================== 24 passed in 15.23s =============================
```

### 失败输出

```
============================= test session starts ==============================
platform linux -- Python 3.9.16, pytest-7.4.0
collected 24 items

tests/test_k8s.py::TestDeployment::test_deployment_replicas FAILED       [  8%]

=================================== FAILURES ===================================
____________________ TestDeployment.test_deployment_replicas ____________________

self = <test_k8s.TestDeployment object at 0x7f8b8c0a3d90>

    def test_deployment_replicas(self):
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        desired_replicas = deployment.spec.replicas
        current_replicas = deployment.status.replicas
    
>       assert desired_replicas == current_replicas
E       AssertionError: Current replicas (2) should match desired (3)

tests/test_k8s.py:267: AssertionError
=========================== short test summary info ============================
FAILED tests/test_k8s.py::TestDeployment::test_deployment_replicas
========================= 1 failed, 23 passed in 10.45s =========================
```

## 🔍 调试技巧

### 1. 查看详细日志

```bash
# 显示 logger 输出
pytest tests/test_k8s.py -v -s
```

### 2. 运行特定测试并显示输出

```bash
# 运行单个测试并显示所有输出
pytest tests/test_k8s.py::TestDeployment::test_deployment_replicas -v -s
```

### 3. 检查测试失败原因

```bash
# 失败时显示本地变量
pytest tests/test_k8s.py -v --tb=local
```

### 4. 在失败后停止

```bash
# 第一次失败就停止
pytest tests/test_k8s.py -x
```

## 📝 测试详解

### Deployment 测试

```python
# 1. test_deployment_exists
# 验证 Deployment 是否存在

# 2. test_deployment_replicas
# 验证副本数量（期望=当前=就绪，且>=3）

# 3. test_deployment_image
# 验证镜像不使用 latest 标签

# 4. test_deployment_resource_limits
# 验证资源配置（requests 和 limits）

# 5. test_deployment_health_probes
# 验证健康检查探针（liveness 和 readiness）

# 6. test_deployment_update_strategy
# 验证滚动更新策略（maxSurge=1, maxUnavailable=0）
```

### Pod 测试

```python
# 1. test_all_pods_running
# 所有 Pod 都处于 Running 状态

# 2. test_all_pods_ready
# 所有 Pod 都通过 readiness 检查

# 3. test_no_pod_restarts
# Pod 重启次数 < 3

# 4. test_pod_resource_usage
# 使用 kubectl top 检查资源使用（需要 metrics-server）
```

### Service 测试

```python
# 1. test_service_exists
# Service 资源存在

# 2. test_service_endpoints
# Service 有正确的端点（Pod IP）

# 3. test_service_health_endpoint
# /health 端点返回 200 和 healthy 状态

# 4. test_service_metrics_endpoint
# /metrics 端点返回 Prometheus 指标

# 5. test_service_load_balancing
# Service 成功处理多个请求
```

### HPA 测试

```python
# 1. test_hpa_exists
# HPA 资源存在并指向正确的 Deployment

# 2. test_hpa_configuration
# minReplicas=3, maxReplicas=10, CPU target=70%

# 3. test_hpa_current_metrics
# HPA 能读取当前指标

# 4. test_hpa_scale_up (慢测试)
# 验证 HPA 在负载下扩容（需要手动运行负载生成器）

# 5. test_hpa_scale_down (慢测试)
# 验证 HPA 在负载降低后缩容
```

## ⚠️ 常见问题

### 问题 1：Kubernetes 客户端无法连接

**错误信息：**
```
Config not found. Error: Invalid kube-config file.
```

**解决方案：**
```bash
# 确保 kubeconfig 存在
ls -la ~/.kube/config

# 如果是 k3s，需要配置 kubeconfig
sudo cat /etc/rancher/k3s/k3s.yaml > ~/.kube/config
chmod 600 ~/.kube/config
```

### 问题 2：Service 无法访问

**错误信息：**
```
Could not connect to service (may need port-forward for ClusterIP)
```

**解决方案：**
```bash
# 如果是 ClusterIP Service，需要端口转发
kubectl port-forward svc/model-api-service 8080:80 -n ml-serving

# 然后在另一个终端运行测试
pytest tests/test_k8s.py::TestService -v
```

### 问题 3：Metrics Server 未安装

**错误信息：**
```
Metrics server not available
```

**解决方案：**
```bash
# 这个测试会跳过，不影响其他测试
# 如果需要 metrics，安装 metrics-server：
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 问题 4：Pod 未就绪

**错误信息：**
```
AssertionError: Current replicas (0) should match desired (3)
```

**解决方案：**
```bash
# 等待 Pod 就绪
kubectl get pods -n ml-serving -w

# 检查 Pod 日志
kubectl logs deployment/model-api -n ml-serving
```

## 🎯 测试清单

运行测试后，你应该看到：

- ✅ **6/6** Deployment 测试通过
- ✅ **4/4** Pod 测试通过
- ✅ **5/5** Service 测试通过
- ✅ **3/5** HPA 测试通过（2 个慢测试可选）
- ✅ **2/2** 滚动更新测试通过
- ✅ **2/2** 配置测试通过
- ⚠️ **0/2** 性能测试（可选，需要 Service 可访问）
- ⚠️ **0/2** 监控测试（可选，需要 Prometheus 配置）

**总计：22-24 个测试通过**

## 📚 下一步

1. **理解测试代码**
   - 阅读每个测试的 docstring
   - 理解断言逻辑
   - 学习 Kubernetes Python SDK 的使用

2. **添加自定义测试**
   - 根据你的需求添加新测试
   - 例如：测试特定的业务逻辑

3. **集成到 CI/CD**
   - 在 GitHub Actions 中运行测试
   - 设置测试覆盖率要求

4. **性能优化**
   - 优化慢速测试
   - 并行运行测试

## 💡 提示

- 使用 `-v` 获取详细输出
- 使用 `-s` 显示 logger 信息
- 使用 `-k` 运行匹配名称的测试
- 使用 `--tb=short` 简化错误回溯
- 使用 `-x` 在第一次失败时停止

祝测试顺利！🎉
