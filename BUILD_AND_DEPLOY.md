# 构建和部署指南

## ⚠️ 重要提示

**在部署之前，必须先构建 Docker 镜像！**

当前项目缺少 Docker 镜像，导致 Pod 无法启动。

---

## 🚀 完整部署流程

### 步骤 1：构建 Docker 镜像

```bash
# 运行构建脚本
./scripts/build-image.sh
```

这会：
1. ✅ 创建 `Dockerfile`
2. ✅ 创建 `requirements.txt`
3. ✅ 使用国内 pip 镜像源（解决网络问题）
4. ✅ 构建镜像 `model-api:v1.0`

**预期输出：**
```
[INFO] 开始构建 Docker 镜像...
[INFO] 镜像名称：model-api:v1.0
[INFO] 执行 docker build...
Step 1/8 : FROM python:3.9-slim
...
[SUCCESS] 镜像构建成功！
```

### 步骤 2：配置 k3s 使用镜像

#### 方法 A：使用 k3s 本地镜像（推荐）

```bash
# 标记镜像为 k3s 可用
docker tag model-api:v1.0 localhost:5000/model-api:v1.0

# 推送到 k3s 本地仓库
docker push localhost:5000/model-api:v1.0
```

然后修改 `kubernetes/deployment.yaml`，将镜像改为：
```yaml
image: localhost:5000/model-api:v1.0
```

#### 方法 B：使用 Docker 镜像（需要 docker 运行时）

如果你的 k3s 使用 Docker 运行时，可以直接使用：
```yaml
image: model-api:v1.0
imagePullPolicy: IfNotPresent
```

### 步骤 3：部署应用

```bash
# 取消之前的部署（清理旧资源）
./scripts/undeploy.sh

# 重新部署
./scripts/deploy.sh
```

### 步骤 4：验证部署

```bash
# 查看 Pod 状态
kubectl get pods -n ml-serving

# 应该看到：
# NAME                         READY   STATUS    RESTARTS   AGE
# model-api-67b74bfbd7-xxxx    1/1     Running   0          2m
# model-api-67b74bfbd7-xxxx    1/1     Running   0          2m
# model-api-67b74bfbd7-xxxx    1/1     Running   0          2m

# 查看 Pod 日志
kubectl logs deployment/model-api -n ml-serving

# 应该看到应用启动日志：
# * Running on http://0.0.0.0:5000
```

### 步骤 5：运行测试

```bash
# 运行所有测试
./scripts/test.sh
```

---

## 🔧 故障排查

### 问题 1：Pod 仍然 CrashLoopBackOff

**检查镜像是否正确：**
```bash
# 查看 Pod 使用的镜像
kubectl get deployment model-api -n ml-serving -o jsonpath='{.spec.template.spec.containers[0].image}'

# 查看本地镜像
docker images | grep model-api
```

**解决方案：**
```bash
# 确保镜像存在
docker images model-api

# 如果镜像不存在，重新构建
./scripts/build-image.sh

# 如果使用 localhost:5000，确保推送了
docker push localhost:5000/model-api:v1.0
```

### 问题 2：ImagePullBackOff

**错误信息：**
```
Failed to pull image "model-api:v1.0": rpc error: code = NotFound
```

**解决方案：**
```bash
# 修改 deployment.yaml，添加 imagePullPolicy
kubectl edit deployment model-api -n ml-serving

# 添加或修改：
# imagePullPolicy: IfNotPresent
```

### 问题 3：应用启动后立即崩溃

**查看日志：**
```bash
kubectl logs deployment/model-api -n ml-serving --previous
```

**可能原因：**
- 端口被占用
- 配置文件缺失
- 依赖加载失败

---

## 📝 手动部署（可选）

如果你想手动控制每个步骤：

### 1. 构建镜像

```bash
docker build -t model-api:v1.0 .
```

### 2. 推送镜像

```bash
# 对于 k3s
docker tag model-api:v1.0 localhost:5000/model-api:v1.0
docker push localhost:5000/model-api:v1.0
```

### 3. 更新 deployment.yaml

编辑 `kubernetes/deployment.yaml` 第 102 行：

```yaml
image: localhost:5000/model-api:v1.0  # 修改这里
imagePullPolicy: IfNotPresent          # 添加这行
```

### 4. 部署

```bash
kubectl create namespace ml-serving
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

### 5. 等待就绪

```bash
kubectl wait --for=condition=ready pod -l app=model-api -n ml-serving --timeout=120s
```

---

## 🎯 快速验证

### 测试应用

```bash
# 端口转发
kubectl port-forward svc/model-api-service 8080:80 -n ml-serving

# 在另一个终端测试
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

**预期响应：**
```json
{"status": "healthy"}
```

### 查看指标

```bash
curl http://localhost:8080/metrics
```

**预期输出：**
```
# HELP model_api_requests_total Total number of requests processed
# TYPE model_api_requests_total counter
model_api_requests_total 0.0
...
```

---

## 📚 相关文档

- [README.md](README.md) - 项目主文档
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [scripts/README.md](scripts/README.md) - 脚本使用指南

---

## 💡 提示

1. **始终先构建镜像**：不要跳过构建步骤
2. **使用本地镜像源**：Dockerfile 已配置清华镜像源
3. **检查 imagePullPolicy**：本地测试用 `IfNotPresent`
4. **查看实时日志**：`kubectl logs -f deployment/model-api`
5. **使用 watch 监控**：`watch kubectl get pods -n ml-serving`

祝你部署成功！🎉
