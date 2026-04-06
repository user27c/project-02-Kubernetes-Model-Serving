# 快速开始指南

## 🎯 5 分钟快速上手

### 1. 检查环境

```bash
# 确保 k3s 正在运行
sudo systemctl start k3s

# 检查 Kubernetes 集群
kubectl cluster-info
```

### 2. 一键部署

```bash
# 运行部署脚本
./scripts/deploy.sh
```

### 3. 一键测试

```bash
# 部署完成后，运行测试脚本
./scripts/test.sh
```

## 📝 详细步骤

### 步骤 1：环境准备

#### 启动 k3s

```bash
# 启动 k3s
sudo systemctl start k3s

# 设置 kubeconfig
sudo cat /etc/rancher/k3s/k3s.yaml > ~/.kube/config
chmod 600 ~/.kube/config
```

#### 验证集群

```bash
kubectl cluster-info
kubectl get nodes
```

### 步骤 2：部署应用

#### 方式 1：一键部署（推荐）

```bash
./scripts/deploy.sh
```

#### 方式 2：手动部署

```bash
# 创建命名空间
kubectl create namespace ml-serving

# 部署应用
kubectl apply -f kubernetes/deployment.yaml

# 部署网络
kubectl apply -f kubernetes/service.yaml
```

### 步骤 3：验证部署

```bash
# 查看 Pod
kubectl get pods -n ml-serving

# 查看 Service
kubectl get svc -n ml-serving

# 查看日志
kubectl logs deployment/model-api -n ml-serving
```

### 步骤 4：访问服务

#### 方式 1：端口转发（推荐用于测试）

```bash
# 启动端口转发
kubectl port-forward svc/model-api-service 8080:80 -n ml-serving

# 在另一个终端访问
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

#### 方式 2：NodePort

如果 Service 类型是 NodePort：

```bash
# 获取 NodePort
kubectl get svc model-api-service -n ml-serving

# 访问（假设 NodePort 是 30080）
curl http://<节点 IP>:30080/health
```

### 步骤 5：运行测试

```bash
# 运行所有测试
./scripts/test.sh

# 或运行特定测试
pytest tests/test_k8s.py::TestDeployment -v
```

## 🔧 故障排查

### Pod 无法启动

```bash
# 查看 Pod 状态
kubectl get pods -n ml-serving

# 查看 Pod 详情
kubectl describe pod -l app=model-api -n ml-serving

# 查看日志
kubectl logs deployment/model-api -n ml-serving
```

### 常见问题

#### 1. SSL 错误

```
ERROR: Could not find a version that satisfies the requirement flask
```

**解决方案**：Pod 启动时无法访问 PyPI，需要修改 Dockerfile 使用国内镜像源。

#### 2. ImagePullBackOff

```
Error: ImagePullBackOff
```

**解决方案**：镜像不存在或无法访问，需要先构建镜像。

#### 3. CrashLoopBackOff

```
Error: CrashLoopBackOff
```

**解决方案**：应用启动失败，查看日志排查原因。

## 📚 下一步

### 学习 Kubernetes 配置

1. 阅读 `kubernetes/deployment.yaml` - 学习 Deployment 配置
2. 阅读 `kubernetes/service.yaml` - 学习 Service 配置
3. 阅读 `kubernetes/hpa.yaml` - 学习自动伸缩

### 学习监控

1. 阅读 `monitoring/servicemonitor.yaml` - 学习 ServiceMonitor
2. 部署 Prometheus Stack
3. 查看 Prometheus Dashboard

### 学习测试

1. 阅读 `tests/test_k8s.py` - 学习 Kubernetes 测试
2. 阅读 `tests/README_TESTS.md` - 测试文档
3. 运行测试并理解输出

## 🎓 学习资源

- [Kubernetes 官方文档](https://kubernetes.io/docs/)
- [kubectl 命令参考](https://kubernetes.io/docs/reference/kubectl/)
- [Prometheus 文档](https://prometheus.io/docs/)

## 💡 提示

- 使用 `kubectl explain <resource>` 查看资源文档
- 使用 `kubectl get <resource> -o yaml` 查看 YAML 配置
- 使用 `kubectl logs -f <pod>` 实时查看日志
- 使用 `kubectl top pods` 查看资源使用（需要 metrics-server）
