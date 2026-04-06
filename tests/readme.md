### 🎯 测试类别 1️⃣ 辅助函数 (Helper Functions)
- setup_k8s_client() - 配置 Kubernetes 客户端
- run_kubectl() - 执行 kubectl 命令
- wait_for_condition() - 等待条件满足
- get_service_url() - 获取 Service 外部 URL 2️⃣ 部署测试 (TestDeployment)
- ✅ Deployment 存在性
- ✅ 副本数量正确性
- ✅ 容器镜像验证
- ✅ 资源请求和限制
- ✅ 健康检查探针（liveness/readiness）
- ✅ 滚动更新策略 3️⃣ Pod 测试 (TestPods)
- ✅ 所有 Pod 处于 Running 状态
- ✅ 所有 Pod 就绪（通过 readiness 探针）
- ✅ 无过度重启
- ✅ 资源使用率在限制内 4️⃣ Service 测试 (TestService)
- ✅ Service 存在性
- ✅ Endpoints 配置
- ✅ /health 端点可访问
- ✅ /metrics 端点可访问
- ✅ 负载均衡分发 5️⃣ 自动伸缩测试 (TestAutoScaling)
- ✅ HPA 存在性
- ✅ HPA 配置（min/max replicas、CPU 目标）
- ✅ 当前指标读取
- 🐌 扩容测试（慢测试）
- 🐌 缩容测试（慢测试） 6️⃣ 滚动更新测试 (TestRollingUpdate)
- 🐌 零停机滚动更新
- 🐌 回滚功能 7️⃣ 配置测试 (TestConfiguration)
- ✅ ConfigMap 存在性
- ✅ Pod 使用 ConfigMap 配置 8️⃣ 性能测试 (TestPerformance)
- 🐌 负载下延迟测试（P95 < 500ms）
- 🐌 吞吐量测试（1000+ RPS） 9️⃣ 监控测试 (TestMonitoring)
- ✅ Prometheus 抓取指标
- ✅ 指标可用性
### 🏷️ 测试标记
- 普通测试 ：快速执行
- @pytest.mark.slow ：慢速测试（需要等待扩容、滚动更新等）
### 📝 运行方式
```
# 运行所有测试
pytest test_k8s.py

# 运行特定测试类
pytest test_k8s.py::TestDeployment

# 运行特定测试
pytest test_k8s.
py::TestDeployment::test_deployment_
exists

# 跳过慢速测试
pytest test_k8s.py -m "not slow"

# 仅运行慢速测试
pytest test_k8s.py -m slow

# 详细输出
pytest test_k8s.py -v
```
### 🎓 学习目标
完成这些测试后，你将掌握：

- ✅ 编写 Kubernetes 集成测试
- ✅ 使用 kubectl 和 Kubernetes Python 客户端
- ✅ 测试自动伸缩行为
- ✅ 验证服务发现和负载均衡
- ✅ 实现零停机部署测试
- ✅ 性能和负载测试
- ✅ 监控和可观测性验证
现在你可以开始实现这些 TODO 测试了！需要我帮你实现某个具体测试吗？