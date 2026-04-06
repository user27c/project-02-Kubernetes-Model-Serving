# Kubernetes Model Serving 项目

一个完整的 Kubernetes 模型服务部署项目，包含应用部署、监控、自动伸缩和测试。

## 🎯 快速导航

- 🚀 **新手入门**：阅读 [QUICKSTART.md](QUICKSTART.md)
- 📊 **项目总结**：阅读 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- 🧪 **测试文档**：阅读 [tests/README_TESTS.md](tests/README_TESTS.md)

## 📋 项目概览

### 项目结构

```
project-02-Kubernetes-Model-Serving/
├── src/                          # 应用程序代码
│   ├── app.py                    # Flask 应用（带 Prometheus 指标）
│   └── config.py                 # 配置管理
├── kubernetes/                   # Kubernetes 部署配置
│   ├── deployment.yaml           # 应用部署配置
│   ├── service.yaml              # 网络服务配置
│   ├── hpa.yaml                  # 自动伸缩配置
│   ├── configmap.yaml            # 配置文件
│   ├── ingress.yaml              # 外部访问配置
│   └── secrets.yaml.example      # 密钥模板
├── monitoring/                   # 监控配置
│   └── servicemonitor.yaml       # Prometheus 监控配置
├── tests/                        # 测试代码
│   ├── test_k8s.py               # Kubernetes 集成测试
│   └── README_TESTS.md           # 测试文档
├── scripts/                      # 自动化脚本
│   ├── deploy.sh                 # 一键部署脚本
│   └── test.sh                   # 一键测试脚本
└── README.md                     # 项目文档（本文件）
```

## 🚀 快速开始

### 前置条件

- Kubernetes 集群（k3s、minikube、kind 等）
- kubectl 命令行工具
- Python 3.8+（用于运行测试）
- pip（Python 包管理器）

### 一键部署

```bash
# 克隆项目后，运行一键部署脚本
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 一键取消部署

```bash
# 删除所有部署的资源
chmod +x scripts/undeploy.sh
./scripts/undeploy.sh
```

部署脚本会自动：
1. ✅ 检查 Kubernetes 集群连接
2. ✅ 创建命名空间 `ml-serving`
3. ✅ 部署应用（Deployment）
4. ✅ 部署网络服务（Service）
5. ✅ 部署监控配置（ServiceMonitor）
6. ✅ 等待所有 Pod 就绪
7. ✅ 显示部署状态

### 一键测试

```bash
# 部署完成后，运行一键测试脚本
chmod +x scripts/test.sh
./scripts/test.sh
```

测试脚本会自动：
1. ✅ 安装测试依赖（kubernetes、requests、pytest）
2. ✅ 运行所有 Kubernetes 集成测试
3. ✅ 生成测试报告

## 📦 手动部署（可选）

如果你想逐步了解部署过程：

### 1. 创建命名空间

```bash
kubectl create namespace ml-serving
```

### 2. 部署核心组件

```bash
# 部署应用
kubectl apply -f kubernetes/deployment.yaml

# 部署网络服务
kubectl apply -f kubernetes/service.yaml
```

### 3. 部署可选组件

```bash
# 部署监控（需要 Prometheus Operator）
kubectl apply -f monitoring/servicemonitor.yaml

# 部署自动伸缩
kubectl apply -f kubernetes/hpa.yaml

# 部署外部访问（需要 Ingress Controller）
kubectl apply -f kubernetes/ingress.yaml
```

### 4. 验证部署

```bash
# 查看 Pod 状态
kubectl get pods -n ml-serving

# 查看 Service 状态
kubectl get svc -n ml-serving

# 查看 Deployment 状态
kubectl get deployment -n ml-serving

# 查看 Pod 日志
kubectl logs deployment/model-api -n ml-serving
```

### 5. 访问服务

```bash
# 本地测试：端口转发
kubectl port-forward svc/model-api-service 8080:80 -n ml-serving

# 在另一个终端访问
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

## 🧪 测试

### 运行所有测试

```bash
# 方法 1：使用测试脚本
./scripts/test.sh

# 方法 2：直接使用 pytest
pytest tests/test_k8s.py -v
```

### 运行特定测试

```bash
# 运行 Deployment 测试
pytest tests/test_k8s.py::TestDeployment -v

# 运行 Service 测试
pytest tests/test_k8s.py::TestService -v

# 运行单个测试
pytest tests/test_k8s.py::TestDeployment::test_deployment_exists -v
```

### 跳过慢速测试

```bash
# 跳过性能测试和滚动更新测试
pytest tests/test_k8s.py -v -m "not slow"
```

### 测试文档

详细测试文档请查看：[tests/README_TESTS.md](tests/README_TESTS.md)

## 📊 监控

### Prometheus 指标

应用暴露以下 Prometheus 指标：

- `model_api_requests_total` - 总请求数
- `model_api_request_duration_seconds` - 请求耗时
- `model_api_predictions_total` - 总预测数
- `model_api_inference_duration_seconds` - 推理耗时
- `model_api_model_loaded` - 模型加载状态
- `model_api_active_connections` - 活动连接数

### 访问 Prometheus Dashboard

```bash
# 如果使用 Helm 部署了 Prometheus Stack
kubectl port-forward svc/prometheus-service -n monitoring 9090:9090

# 浏览器访问 http://localhost:9090
```

## 🔧 故障排查

### Pod 无法启动

```bash
# 查看 Pod 状态
kubectl get pods -n ml-serving

# 查看 Pod 日志
kubectl logs deployment/model-api -n ml-serving

# 查看 Pod 详情（包含事件）
kubectl describe pod -l app=model-api -n ml-serving
```

### Service 无法访问

```bash
# 查看 Service 端点
kubectl get endpoints model-api-service -n ml-serving

# 测试内部连接
kubectl run test --rm -it --image=busybox --restart=Never -- \
  wget -qO- http://model-api-service.ml-serving.svc.cluster.local/health
```

### 监控不工作

```bash
# 查看 ServiceMonitor 状态
kubectl get servicemonitor -n ml-serving

# 查看 Prometheus 目标
kubectl port-forward svc/prometheus-k8s -n monitoring 9090:9090
# 浏览器访问 http://localhost:9090/targets
```

## 📚 学习路径

### 阶段 1：基础部署（1-2 天）
- ✅ 理解 Deployment 配置
- ✅ 理解 Service 配置
- ✅ 完成基础部署和测试

### 阶段 2：监控（1 天）
- ✅ 理解 Prometheus 指标
- ✅ 配置 ServiceMonitor
- ✅ 验证指标采集

### 阶段 3：自动伸缩（1 天）
- ✅ 理解 HPA 配置
- ✅ 配置 CPU 指标伸缩
- ✅ 测试自动伸缩

### 阶段 4：高级特性（2-3 天）
- ✅ 配置 Ingress 外部访问
- ✅ 配置 ConfigMap 和 Secrets
- ✅ 实现零停机滚动更新

## 🎯 测试覆盖

测试套件包含 **24 个测试**：

| 测试类别 | 测试数量 | 说明 |
|---------|---------|------|
| Deployment 测试 | 6 个 | 验证 Deployment 配置和状态 |
| Pod 测试 | 4 个 | 验证 Pod 健康状态 |
| Service 测试 | 5 个 | 验证 Service 配置和连接性 |
| HPA 测试 | 5 个 | 验证自动伸缩配置 |
| 滚动更新测试 | 2 个 | 验证零停机部署 |
| 配置测试 | 2 个 | 验证 ConfigMap 使用 |
| 性能测试 | 2 个 | 验证延迟和吞吐量 |
| 监控测试 | 2 个 | 验证 Prometheus 集成 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请提交 Issue 或联系项目维护者。
