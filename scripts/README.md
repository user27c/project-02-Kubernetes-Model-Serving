# Kubernetes 脚本使用指南

## 📦 自动化脚本

项目提供 3 个一键脚本，简化部署和管理流程。

---

## 🚀 1. deploy.sh - 一键部署

### 功能
自动部署整个项目到 Kubernetes 集群。

### 使用方式
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 自动化步骤
1. ✅ 检查 Kubernetes 集群连接
2. ✅ 创建命名空间 `ml-serving`
3. ✅ 部署 Deployment（应用）
4. ✅ 部署 Service（网络）
5. ✅ 部署 ConfigMap（配置）
6. ✅ 部署 ServiceMonitor（监控）
7. ✅ 部署 HPA（自动伸缩）
8. ✅ 等待 Pod 就绪（最多 5 分钟）
9. ✅ 显示部署状态

### 预期输出
```
[INFO] 步骤 1: 检查前置条件...
[SUCCESS] Kubernetes 集群连接正常
[INFO] 步骤 2: 创建命名空间...
[INFO] 步骤 3: 部署应用...
[SUCCESS] Deployment 部署完成
[SUCCESS] Service 部署完成
[INFO] 步骤 4: 部署可选组件...
[SUCCESS] ConfigMap 部署完成
[SUCCESS] ServiceMonitor 部署完成
[SUCCESS] HPA 部署完成
[SUCCESS] 所有 Pod 已就绪 (3/3)
[SUCCESS] ==========================================
[SUCCESS] 部署完成！
[SUCCESS] ==========================================
```

---

## 🧪 2. test.sh - 一键测试

### 功能
自动安装测试依赖并运行所有 Kubernetes 集成测试。

### 使用方式
```bash
chmod +x scripts/test.sh
./scripts/test.sh
```

### 前置条件
- 已运行 `./scripts/deploy.sh`
- Pod 处于 Running 状态

### 自动化步骤
1. ✅ 检查 Python 和 kubectl
2. ✅ 安装测试依赖（kubernetes、requests、pytest）
3. ✅ 检查部署状态
4. ✅ 运行所有 24 个测试
5. ✅ 显示测试结果

### 预期输出
```
[INFO] 步骤 1: 检查前置条件...
[SUCCESS] 前置条件检查通过
[INFO] 步骤 2: 安装测试依赖...
[SUCCESS] 测试依赖安装完成
[INFO] 步骤 3: 检查部署状态...
[SUCCESS] 部署状态检查完成
[INFO] 步骤 4: 运行测试...

==========================================
开始运行 Kubernetes 集成测试
==========================================

tests/test_k8s.py::TestDeployment::test_deployment_exists PASSED
tests/test_k8s.py::TestDeployment::test_deployment_replicas PASSED
...

==========================================
[SUCCESS] 所有测试通过！
```

---

## ❌ 3. undeploy.sh - 一键取消部署

### 功能
删除所有部署的 Kubernetes 资源。

### 使用方式
```bash
chmod +x scripts/undeploy.sh
./scripts/undeploy.sh
```

### 自动化步骤
1. ⚠️ 确认操作（防止误删）
2. ✅ 删除 HPA
3. ✅ 删除 ServiceMonitor
4. ✅ 删除 ConfigMap
5. ✅ 删除 Ingress
6. ✅ 删除 Service
7. ✅ 删除 Deployment
8. ✅ 等待 Pod 终止
9. ✅ 可选：删除命名空间
10. ✅ 显示删除状态

### 预期输出
```
[WARNING] 警告：此操作将删除所有部署的资源！

确定要取消部署吗？(yes/no): yes

[INFO] 步骤 1: 删除 Kubernetes 资源...
[INFO] 删除 HPA...
[SUCCESS] HPA 已删除
[INFO] 删除 ServiceMonitor...
[SUCCESS] ServiceMonitor 已删除
[INFO] 删除 Service...
[SUCCESS] Service 已删除
[INFO] 删除 Deployment...
[SUCCESS] Deployment 已删除
[INFO] 步骤 2: 等待资源删除完成...
[SUCCESS] 所有 Pod 已终止
[INFO] 步骤 3: 删除命名空间...

是否要删除命名空间 'ml-serving'？(yes/no): yes

[SUCCESS] 命名空间 ml-serving 已删除
[SUCCESS] ==========================================
[SUCCESS] 取消部署完成！
[SUCCESS] ==========================================
```

---

## 🔄 典型使用流程

### 场景 1：首次部署

```bash
# 1. 部署
./scripts/deploy.sh

# 2. 验证
kubectl get pods -n ml-serving

# 3. 测试
./scripts/test.sh
```

### 场景 2：重新部署

```bash
# 1. 取消部署
./scripts/undeploy.sh

# 2. 重新部署
./scripts/deploy.sh

# 3. 测试
./scripts/test.sh
```

### 场景 3：清理环境

```bash
# 完全清理
./scripts/undeploy.sh
# 选择删除命名空间：yes
```

---

## 🛠️ 手动命令参考

### 部署相关

```bash
# 创建命名空间
kubectl create namespace ml-serving

# 部署应用
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# 部署可选组件
kubectl apply -f kubernetes/hpa.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f monitoring/servicemonitor.yaml
```

### 查看状态

```bash
# 查看所有资源
kubectl get all -n ml-serving

# 查看 Pod
kubectl get pods -n ml-serving

# 查看 Service
kubectl get svc -n ml-serving

# 查看 Deployment
kubectl get deployment -n ml-serving

# 查看 Pod 日志
kubectl logs deployment/model-api -n ml-serving

# 实时查看日志
kubectl logs -f deployment/model-api -n ml-serving
```

### 删除资源

```bash
# 删除单个资源
kubectl delete deployment model-api -n ml-serving
kubectl delete service model-api-service -n ml-serving

# 删除所有资源
kubectl delete all -n ml-serving

# 删除命名空间（会删除所有资源）
kubectl delete namespace ml-serving
```

---

## ⚠️ 注意事项

### 1. undeploy.sh 是破坏性操作
- 会删除所有部署的资源
- 需要手动确认（输入 yes）
- 删除后无法恢复

### 2. 数据持久化
- 当前项目无持久化存储
- 删除 Pod 后数据会丢失
- 如需持久化，配置 PersistentVolume

### 3. 命名空间
- 建议保留命名空间以便重新部署
- 完全清理时才删除命名空间

### 4. 资源冲突
- 如果部署失败，先运行 undeploy.sh
- 清理后再重新 deploy.sh

---

## 🆘 故障排查

### 问题 1：deploy.sh 失败

```bash
# 查看详细错误
./scripts/deploy.sh 2>&1 | tee deploy.log

# 手动检查
kubectl get events -n ml-serving --sort-by='.lastTimestamp'
```

### 问题 2：test.sh 失败

```bash
# 查看 Pod 状态
kubectl get pods -n ml-serving

# 查看 Pod 日志
kubectl logs deployment/model-api -n ml-serving

# 手动运行测试
pytest tests/test_k8s.py -v
```

### 问题 3：undeploy.sh 卡住

```bash
# 强制删除 Pod
kubectl delete pods --all -n ml-serving --grace-period=0 --force

# 手动删除资源
kubectl delete -f kubernetes/deployment.yaml -n ml-serving
kubectl delete -f kubernetes/service.yaml -n ml-serving
```

---

## 📚 相关文档

- [README.md](README.md) - 项目主文档
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总结
- [tests/README_TESTS.md](tests/README_TESTS.md) - 测试文档
