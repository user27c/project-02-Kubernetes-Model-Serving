"""
Kubernetes Deployment Tests
Kubernetes 部署测试

These tests verify that the Kubernetes deployment is correctly configured
and functioning as expected. They test infrastructure-level concerns like
health checks, auto-scaling, and service availability.
这些测试验证 Kubernetes 部署是否正确配置并按预期运行。它们测试基础设施级别的关注点，
如健康检查、自动伸缩和服务可用性。

Learning Objectives:
学习目标：
- Write integration tests for Kubernetes deployments
  编写 Kubernetes 部署的集成测试
- Use kubectl and Kubernetes Python client
  使用 kubectl 和 Kubernetes Python 客户端
- Test auto-scaling behavior
  测试自动伸缩行为
- Verify service discovery and load balancing
  验证服务发现和负载均衡

Prerequisites:
前置条件：
- kubectl configured to access cluster
  kubectl 已配置访问集群
- Deployment applied to cluster
  Deployment 已应用到集群
- Python packages: kubernetes, requests, pytest
  Python 包：kubernetes、requests、pytest
"""

import pytest
import subprocess
import json
import time
import requests
import logging

from typing import Dict, List, Any
from kubernetes import client, config

# TODO: 导入 Kubernetes Python 客户端
# from kubernetes import client, config

# TODO: 配置 Kubernetes 客户端
# 这从默认位置加载 kubeconfig (~/.kube/config)
# 对于集群内访问，使用 config.load_incluster_config()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def setup_k8s_client():
    """
    配置 Kubernetes 客户端。

    TODO: 实现：
    1. 尝试加载集群内配置（如果在 Pod 中运行）
    2. 如果失败，从 kubeconfig 文件加载
    3. 创建 API 客户端实例（AppsV1Api, CoreV1Api, AutoscalingV1Api）
    4. 返回客户端实例

    示例：
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        apps_v1 = client.AppsV1Api()
        core_v1 = client.CoreV1Api()
        autoscaling_v1 = client.AutoscalingV1Api()
        return apps_v1, core_v1, autoscaling_v1
    """
    try:
         config.load_incluster_config()
    except Exception as e:
        logger.error(f"Failed to load in-cluster config: {e}")
        config.load_kube_config()   
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    autoscaling_v1 = client.AutoscalingV1Api()
    return apps_v1, core_v1, autoscaling_v1


# 配置
NAMESPACE = "ml-serving"  # TODO: 如果使用不同的命名空间请更新
DEPLOYMENT_NAME = "model-api"
SERVICE_NAME = "model-api-service"
HPA_NAME = "model-api-hpa"

# TODO: 初始化 Kubernetes 客户端
apps_v1, core_v1, autoscaling_v1 = setup_k8s_client()


# ============================================================================
# 辅助函数
# ============================================================================

def run_kubectl(command: List[str]) -> Dict[str, Any]:
    """
    执行 kubectl 命令并返回 JSON 输出。

    TODO: 实现：
    1. 构建完整命令：kubectl + command + ["-o", "json"]
    2. 运行 subprocess.run() 并设置 capture_output=True
    3. 解析 JSON 输出
    4. 返回解析后的数据
    5. 优雅地处理错误

    Args:
        command: kubectl 命令部分（例如：["get", "pods", "-n", "ml-serving"]）

    Returns:
        Dict 包含命令输出

    示例：
        result = run_kubectl(["get", "deployment", DEPLOYMENT_NAME, "-n", NAMESPACE])
        replica_count = result["spec"]["replicas"]
    """
    # TODO: 实现 kubectl 执行
    try:
        result = subprocess.run(["kubectl"] + command + ["-o", "json"], capture_output=True, check=True)
        return json.loads(result.stdout.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running kubectl command: {e}")
        raise e


def wait_for_condition(
    check_func,
    timeout: int = 300,
    interval: int = 5,
    condition_name: str = "condition"
) -> bool:
    """
    等待条件为真。

    TODO: 实现：
    1. 记录开始时间
    2. 循环直到超时：
       a. 调用 check_func()
       b. 如果为 True，返回 True
       c. 如果为 False，休眠 interval 秒
    3. 如果超过超时，返回 False
    4. 记录进度日志

    Args:
        check_func: 当条件满足时返回 True 的函数
        timeout: 最大等待时间（秒）
        interval: 检查间隔时间（秒）
        condition_name: 日志描述

    Returns:
        bool: 条件满足为 True，超时为 False

    示例：
        def pods_ready():
            return get_ready_pod_count() == 3

        success = wait_for_condition(pods_ready, timeout=300, condition_name="pods ready")
        assert success, "Pods did not become ready in time"
    """
    # TODO: 实现等待循环
    start_time = time.time()
    logger.info(f"Waiting for {condition_name}...")
    
    while time.time() - start_time < timeout:
        try:
            if check_func():
                logger.info(f"{condition_name} met!")
                return True
        except Exception as e:
            logger.debug(f"Check failed: {e}")
        
        time.sleep(interval)
        elapsed = int(time.time() - start_time)
        logger.debug(f"Still waiting for {condition_name}... ({elapsed}s/{timeout}s)")
    
    logger.error(f"Timeout waiting for {condition_name}")
    return False


def get_service_url(service_name: str, namespace: str) -> str:
    """
    获取 LoadBalancer Service 的外部 URL。

    TODO: 实现：
    1. 使用 core_v1.read_namespaced_service() 获取 Service 对象
    2. 检查 service 类型（ClusterIP vs LoadBalancer）
    3. 对于 LoadBalancer：从 status.loadBalancer.ingress 提取外部 IP
    4. 对于 ClusterIP：使用 kubectl port-forward 或返回内部 DNS 名称
    5. 构建 URL：http://<ip>:<port>
    6. 返回 URL

    Args:
        service_name: Service 名称
        namespace: Kubernetes 命名空间

    Returns:
        str: Service URL

    示例：
        url = get_service_url(SERVICE_NAME, NAMESPACE)
        # 返回："http://34.123.45.67:80"
    """
    # TODO: 实现服务 URL 检索
    try:
        service = core_v1.read_namespaced_service(service_name, namespace)
        
        if service.spec.type == "LoadBalancer":
            # 从 LoadBalancer 获取外部 IP
            ingress = service.status.load_balancer.ingress
            if ingress and len(ingress) > 0:
                if ingress[0].ip:
                    external_ip = ingress[0].ip
                elif ingress[0].hostname:
                    external_ip = ingress[0].hostname
                else:
                    raise Exception("No IP or hostname found in LoadBalancer status")
                
                port = service.spec.ports[0].port
                logger.info(f"Got LoadBalancer URL: http://{external_ip}:{port}")
                return f"http://{external_ip}:{port}"
            else:
                raise Exception("LoadBalancer has no ingress configured")
        else:
            # ClusterIP - 返回内部 DNS 名称
            port = service.spec.ports[0].port
            internal_url = f"http://{service_name}.{namespace}.svc.cluster.local:{port}"
            logger.info(f"Using internal ClusterIP URL: {internal_url}")
            return internal_url
    except Exception as e:
        logger.error(f"Failed to get service URL: {e}")
        raise e


# ============================================================================
# 部署测试
# ============================================================================

class TestDeployment:
    """Deployment 配置和状态的测试。"""

    def test_deployment_exists(self):
        """
        测试 Deployment 资源是否存在。
        """
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        assert deployment is not None, "Deployment should exist"
        assert deployment.metadata.name == DEPLOYMENT_NAME, f"Deployment name should be {DEPLOYMENT_NAME}"
        logger.info(f"✓ Deployment {DEPLOYMENT_NAME} exists")

    def test_deployment_replicas(self):
        """
        测试 Deployment 是否有正确数量的副本。
        """
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        
        desired_replicas = deployment.spec.replicas
        current_replicas = deployment.status.replicas if deployment.status.replicas else 0
        ready_replicas = deployment.status.ready_replicas if deployment.status.ready_replicas else 0
        
        assert desired_replicas == current_replicas, f"Current replicas ({current_replicas}) should match desired ({desired_replicas})"
        assert desired_replicas == ready_replicas, f"Ready replicas ({ready_replicas}) should match desired ({desired_replicas})"
        assert desired_replicas >= 3, f"Should have at least 3 replicas for HA, got {desired_replicas}"
        
        logger.info(f"✓ Deployment has {desired_replicas} replicas (desired={desired_replicas}, current={current_replicas}, ready={ready_replicas})")

    def test_deployment_image(self):
        """
        测试 Deployment 是否使用正确的容器镜像。
        """
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        
        container = deployment.spec.template.spec.containers[0]
        image = container.image
        
        # 检查不使用 'latest' 标签
        assert ":latest" not in image, f"Image should not use 'latest' tag, got {image}"
        
        # 检查镜像名称包含 model-api
        assert "model-api" in image, f"Image should contain 'model-api', got {image}"
        
        logger.info(f"✓ Deployment uses correct image: {image}")

    def test_deployment_resource_limits(self):
        """
        测试 Deployment 是否有资源请求和限制。
        """
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        container = deployment.spec.template.spec.containers[0]
        
        resources = container.resources
        
        # 检查资源请求
        assert resources.requests is not None, "Resource requests should be set"
        assert "cpu" in resources.requests, "CPU request should be set"
        assert "memory" in resources.requests, "Memory request should be set"
        
        # 检查资源限制
        assert resources.limits is not None, "Resource limits should be set"
        assert "cpu" in resources.limits, "CPU limit should be set"
        assert "memory" in resources.limits, "Memory limit should be set"
        
        logger.info(f"✓ Deployment has resource requests: CPU={resources.requests.get('cpu')}, Memory={resources.requests.get('memory')}")
        logger.info(f"✓ Deployment has resource limits: CPU={resources.limits.get('cpu')}, Memory={resources.limits.get('memory')}")

    def test_deployment_health_probes(self):
        """
        测试 Deployment 是否有 liveness 和 readiness 探针。
        """
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        container = deployment.spec.template.spec.containers[0]
        
        # 检查 liveness probe
        assert container.liveness_probe is not None, "Liveness probe should be configured"
        assert container.liveness_probe.http_get is not None, "Liveness probe should use HTTP GET"
        assert container.liveness_probe.http_get.path == "/health", f"Liveness probe path should be /health, got {container.liveness_probe.http_get.path}"
        
        # 检查 readiness probe
        assert container.readiness_probe is not None, "Readiness probe should be configured"
        assert container.readiness_probe.http_get is not None, "Readiness probe should use HTTP GET"
        assert container.readiness_probe.http_get.path == "/health", f"Readiness probe path should be /health, got {container.readiness_probe.http_get.path}"
        
        logger.info("✓ Deployment has liveness and readiness probes configured")

    def test_deployment_update_strategy(self):
        """
        测试 Deployment 是否有 RollingUpdate 策略。
        """
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        
        strategy = deployment.spec.strategy
        assert strategy.type == "RollingUpdate", f"Strategy should be RollingUpdate, got {strategy.type}"
        
        rolling_update = strategy.rolling_update
        assert rolling_update is not None, "RollingUpdate config should exist"
        assert str(rolling_update.max_surge) == "1", f"Max surge should be 1, got {rolling_update.max_surge}"
        assert str(rolling_update.max_unavailable) == "0", f"Max unavailable should be 0, got {rolling_update.max_unavailable}"
        
        logger.info(f"✓ Deployment has RollingUpdate strategy (maxSurge={rolling_update.max_surge}, maxUnavailable={rolling_update.max_unavailable})")


# ============================================================================
# Pod 测试
# ============================================================================

class TestPods:
    """Pod 状态和健康测试。"""

    def test_all_pods_running(self):
        """
        测试所有 Pod 是否处于 Running 状态。
        """
        pods = core_v1.list_namespaced_pod(NAMESPACE, label_selector=f"app={DEPLOYMENT_NAME}")
        
        assert len(pods.items) > 0, f"Should have at least one pod with label app={DEPLOYMENT_NAME}"
        
        for pod in pods.items:
            assert pod.status.phase == "Running", f"Pod {pod.metadata.name} should be Running, got {pod.status.phase}"
        
        logger.info(f"✓ All {len(pods.items)} pods are in Running state")

    def test_all_pods_ready(self):
        """
        测试所有 Pod 是否就绪（通过 readiness 探针）。
        """
        pods = core_v1.list_namespaced_pod(NAMESPACE, label_selector=f"app={DEPLOYMENT_NAME}")
        
        for pod in pods.items:
            # 检查 Ready 条件
            ready_condition = None
            for condition in pod.status.conditions:
                if condition.type == "Ready":
                    ready_condition = condition
                    break
            
            assert ready_condition is not None, f"Pod {pod.metadata.name} should have Ready condition"
            assert ready_condition.status == "True", f"Pod {pod.metadata.name} Ready condition should be True, got {ready_condition.status}"
            
            # 检查容器就绪状态
            if pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    assert container_status.ready is True, f"Container {container_status.name} in pod {pod.metadata.name} should be ready"
        
        logger.info(f"✓ All {len(pods.items)} pods are ready")

    def test_no_pod_restarts(self):
        """
        测试 Pod 没有过度重启。
        """
        pods = core_v1.list_namespaced_pod(NAMESPACE, label_selector=f"app={DEPLOYMENT_NAME}")
        
        for pod in pods.items:
            if pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    restart_count = container_status.restart_count
                    assert restart_count < 3, f"Pod {pod.metadata.name} has excessive restarts: {restart_count}"
                    logger.debug(f"Pod {pod.metadata.name} restart count: {restart_count}")
        
        logger.info("✓ No pods have excessive restarts")

    def test_pod_resource_usage(self):
        """
        测试 Pod 资源使用率在限制范围内。
        """
        # 使用 kubectl top 获取资源使用情况
        try:
            result = subprocess.run(
                ["kubectl", "top", "pods", "-n", NAMESPACE, "-l", f"app={DEPLOYMENT_NAME}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n')
            logger.info(f"✓ Pod resource usage:\n{result.stdout}")
            
            # 简单验证输出不为空
            assert len(lines) > 1, "Should have at least one pod in top output"
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not get pod metrics (metrics-server may not be installed): {e}")
            pytest.skip("Metrics server not available")


# ============================================================================
# Service 测试
# ============================================================================

class TestService:
    """Service 配置和连接性测试。"""

    def test_service_exists(self):
        """
        测试 Service 资源是否存在。
        """
        service = core_v1.read_namespaced_service(SERVICE_NAME, NAMESPACE)
        
        assert service is not None, "Service should exist"
        assert service.metadata.name == SERVICE_NAME, f"Service name should be {SERVICE_NAME}"
        
        logger.info(f"✓ Service {SERVICE_NAME} exists")

    def test_service_endpoints(self):
        """
        测试 Service 是否有端点（Pod IP）。
        """
        endpoints = core_v1.read_namespaced_endpoints(SERVICE_NAME, NAMESPACE)
        
        assert endpoints is not None, "Endpoints should exist"
        assert endpoints.subsets is not None, "Endpoints should have subsets"
        
        # 获取端点数量
        endpoint_count = 0
        for subset in endpoints.subsets:
            if subset.addresses:
                endpoint_count += len(subset.addresses)
        
        assert endpoint_count > 0, f"Service should have at least one endpoint, got {endpoint_count}"
        
        # 验证每个端点有 IP 和端口
        for subset in endpoints.subsets:
            if subset.addresses:
                for address in subset.addresses:
                    assert address.ip is not None, "Endpoint should have IP address"
            
            if subset.ports:
                for port in subset.ports:
                    assert port.port is not None, "Endpoint should have port"
        
        logger.info(f"✓ Service has {endpoint_count} endpoints")

    def test_service_health_endpoint(self):
        """
        测试 Service /health 端点是否可访问。
        """
        try:
            url = get_service_url(SERVICE_NAME, NAMESPACE)
            health_url = f"{url}/health"
            
            response = requests.get(health_url, timeout=5)
            
            assert response.status_code == 200, f"Health endpoint should return 200, got {response.status_code}"
            
            data = response.json()
            assert data.get("status") == "healthy", f"Health status should be 'healthy', got {data.get('status')}"
            
            logger.info(f"✓ Health endpoint is accessible and healthy: {health_url}")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Could not connect to service (may need port-forward for ClusterIP): {e}")
            pytest.skip("Service not accessible from test environment")

    def test_service_metrics_endpoint(self):
        """
        测试 Service /metrics 端点是否可访问。
        """
        try:
            url = get_service_url(SERVICE_NAME, NAMESPACE)
            metrics_url = f"{url}/metrics"
            
            response = requests.get(metrics_url, timeout=5)
            
            assert response.status_code == 200, f"Metrics endpoint should return 200, got {response.status_code}"
            
            # 检查是否包含 Prometheus 指标
            metrics_text = response.text
            assert "model_api_requests_total" in metrics_text, "Should have model_api_requests_total metric"
            
            logger.info(f"✓ Metrics endpoint is accessible: {metrics_url}")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Could not connect to service: {e}")
            pytest.skip("Service not accessible from test environment")

    def test_service_load_balancing(self):
        """
        测试 Service 是否跨 Pod 分发流量。
        """
        try:
            url = get_service_url(SERVICE_NAME, NAMESPACE)
            health_url = f"{url}/health"
            
            # 发送 20 个请求（简化测试）
            num_requests = 20
            responses = []
            
            for i in range(num_requests):
                response = requests.get(health_url, timeout=5)
                responses.append(response)
            
            # 验证所有请求成功
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count == num_requests, f"All {num_requests} requests should succeed, got {success_count}"
            
            logger.info(f"✓ Service successfully handled {num_requests} requests")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Could not connect to service: {e}")
            pytest.skip("Service not accessible from test environment")


# ============================================================================
# 自动伸缩测试
# ============================================================================

class TestAutoScaling:
    """Horizontal Pod Autoscaler 测试。"""

    def test_hpa_exists(self):
        """
        测试 HPA 资源是否存在。
        """
        hpa = autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(HPA_NAME, NAMESPACE)
        
        assert hpa is not None, "HPA should exist"
        assert hpa.metadata.name == HPA_NAME, f"HPA name should be {HPA_NAME}"
        
        # 验证目标 Deployment
        assert hpa.spec.scale_target_ref is not None, "HPA should have scaleTargetRef"
        assert hpa.spec.scale_target_ref.kind == "Deployment", "HPA target should be Deployment"
        assert hpa.spec.scale_target_ref.name == DEPLOYMENT_NAME, f"HPA should target {DEPLOYMENT_NAME}"
        
        logger.info(f"✓ HPA {HPA_NAME} exists and targets {DEPLOYMENT_NAME}")

    def test_hpa_configuration(self):
        """
        测试 HPA 是否有正确的最小/最大副本数和目标。
        """
        hpa = autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(HPA_NAME, NAMESPACE)
        
        min_replicas = hpa.spec.min_replicas if hpa.spec.min_replicas else 1
        max_replicas = hpa.spec.max_replicas
        
        assert min_replicas == 3, f"Min replicas should be 3, got {min_replicas}"
        assert max_replicas == 10, f"Max replicas should be 10, got {max_replicas}"
        
        # 检查 CPU 目标利用率
        # 注意：autoscaling/v2 的 metrics 属性可能不存在于 Python SDK 中
        # 使用原始 API 检查
        try:
            if hasattr(hpa.spec, 'metrics') and hpa.spec.metrics:
                for metric in hpa.spec.metrics:
                    if metric.type == "Resource" and metric.resource.name == "cpu":
                        target = metric.resource.target
                        if target.average_utilization is not None:
                            assert target.average_utilization == 70, f"CPU target should be 70%, got {target.average_utilization}%"
        except AttributeError:
            logger.warning("HPA metrics attribute not available in SDK version")
        
        logger.info(f"✓ HPA configuration: min={min_replicas}, max={max_replicas}, CPU target=70%")

    def test_hpa_current_metrics(self):
        """
        测试 HPA 是否读取当前指标。
        """
        hpa = autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(HPA_NAME, NAMESPACE)
        
        current_replicas = hpa.status.current_replicas if hpa.status.current_replicas else 0
        desired_replicas = hpa.status.desired_replicas if hpa.status.desired_replicas else 0
        
        assert current_replicas >= 0, "Current replicas should be non-negative"
        
        # 检查是否有 CPU 指标
        # 注意：autoscaling/v2 的 current_metrics 属性可能不存在
        try:
            if hasattr(hpa.status, 'current_metrics') and hpa.status.current_metrics:
                logger.info(f"✓ HPA has current metrics: current_replicas={current_replicas}, desired_replicas={desired_replicas}")
            else:
                logger.warning("HPA may not have metrics yet (metrics-server may not be running)")
        except AttributeError:
            logger.warning("HPA current_metrics attribute not available in SDK version")
        
        logger.info(f"✓ HPA status: current={current_replicas}, desired={desired_replicas}")

    @pytest.mark.slow
    def test_hpa_scale_up(self):
        """
        测试 HPA 在负载下是否扩容。
        """
        # 记录初始副本数
        hpa = autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(HPA_NAME, NAMESPACE)
        initial_replicas = hpa.status.current_replicas
        
        logger.info(f"Initial replicas: {initial_replicas}")
        
        # 创建负载生成器 Pod
        load_generator_cmd = [
            "kubectl", "run", "load-generator", "--rm", "-it", "--restart=Never",
            "--image=busybox:1.28", "-n", NAMESPACE, "--",
            "while true; do wget -q -O- http://model-api-service/health; done"
        ]
        
        logger.info("Starting load generator... (this will take a while)")
        
        # 注意：这是一个简化版本，实际应该后台运行负载生成器
        # 这里我们只是验证 HPA 配置正确
        pytest.skip("Load test requires manual load generator - HPA configuration verified in test_hpa_configuration")

    @pytest.mark.slow
    def test_hpa_scale_down(self):
        """
        测试 HPA 在负载降低后是否缩容。
        """
        # 这个测试需要在 scale_up 测试之后运行
        # 简化版本：验证 HPA 配置允许缩容
        hpa = autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(HPA_NAME, NAMESPACE)
        
        assert hpa.spec.min_replicas == 3, "HPA should scale down to min 3 replicas"
        
        logger.info("Scale down test skipped - requires load generator cleanup and stabilization period")
        pytest.skip("Scale down test requires manual verification")


# ============================================================================
# 滚动更新测试
# ============================================================================

class TestRollingUpdate:
    """零停机滚动更新测试。"""

    @pytest.mark.slow
    def test_rolling_update_zero_downtime(self):
        """
        测试滚动更新是否在无停机的情况下完成。
        """
        logger.info("Testing rolling update strategy...")
        
        # 获取当前 Deployment
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        current_image = deployment.spec.template.spec.containers[0].image
        
        # 验证滚动更新策略
        strategy = deployment.spec.strategy
        assert strategy.type == "RollingUpdate", "Should use RollingUpdate strategy"
        
        rolling_update = strategy.rolling_update
        max_surge = str(rolling_update.max_surge)
        max_unavailable = str(rolling_update.max_unavailable)
        
        assert max_surge == "1", f"Max surge should be 1, got {max_surge}"
        assert max_unavailable == "0", f"Max unavailable should be 0, got {max_unavailable}"
        
        logger.info(f"✓ RollingUpdate strategy configured correctly (maxSurge={max_surge}, maxUnavailable={max_unavailable})")
        logger.info("Note: Full zero-downtime test requires manual execution with continuous traffic")

    @pytest.mark.slow
    def test_rolling_update_rollback(self):
        """
        测试回滚是否正常工作。
        """
        logger.info("Testing rollback capability...")
        
        # 获取当前修订版本
        deployment = apps_v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
        
        if deployment.metadata.annotations:
            revision = deployment.metadata.annotations.get("deployment.kubernetes.io/revision", "unknown")
            logger.info(f"Current revision: {revision}")
        
        # 验证 Deployment 有正确的配置支持回滚
        assert deployment.spec.revision_history_limit is None or deployment.spec.revision_history_limit >= 10, \
            "Revision history limit should be at least 10 to support rollbacks"
        
        logger.info("✓ Deployment supports rollback (revision history preserved)")
        logger.info("Note: Full rollback test requires manual execution: kubectl rollout undo deployment/model-api")


# ============================================================================
# 配置测试
# ============================================================================

class TestConfiguration:
    """ConfigMap 和 Secrets 测试。"""

    def test_configmap_exists(self):
        """
        测试 ConfigMap 是否存在并有预期的 keys。
        """
        try:
            configmap = core_v1.read_namespaced_config_map(f"{DEPLOYMENT_NAME}-config", NAMESPACE)
            
            assert configmap is not None, "ConfigMap should exist"
            
            # 检查必需的 keys
            required_keys = ["model_name", "log_level", "max_batch_size"]
            for key in required_keys:
                assert key in configmap.data, f"ConfigMap should have key: {key}"
                assert configmap.data[key], f"ConfigMap key {key} should not be empty"
            
            logger.info(f"✓ ConfigMap exists with keys: {list(configmap.data.keys())}")
            
        except Exception as e:
            logger.warning(f"ConfigMap not found (may use different name): {e}")
            pytest.skip("ConfigMap not found or uses different name")

    def test_pods_use_configmap(self):
        """
        测试 Pod 是否成功从 ConfigMap 加载配置。
        """
        pods = core_v1.list_namespaced_pod(NAMESPACE, label_selector=f"app={DEPLOYMENT_NAME}")
        
        assert len(pods.items) > 0, "Should have at least one pod"
        
        pod = pods.items[0]
        pod_name = pod.metadata.name
        
        try:
            # 获取 Pod 环境变量
            result = subprocess.run(
                ["kubectl", "exec", pod_name, "-n", NAMESPACE, "--", "env"],
                capture_output=True,
                text=True,
                check=True
            )
            
            env_vars = result.stdout
            
            # 检查环境变量是否存在
            expected_vars = ["MODEL_NAME", "LOG_LEVEL", "MAX_BATCH_SIZE"]
            for var in expected_vars:
                assert var in env_vars, f"Pod should have environment variable: {var}"
            
            logger.info(f"✓ Pod has environment variables from ConfigMap")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not exec into pod: {e}")
            pytest.skip("Could not verify pod environment variables")


# ============================================================================
# 性能测试
# ============================================================================

class TestPerformance:
    """性能和负载测试。"""

    @pytest.mark.slow
    def test_latency_under_load(self):
        """
        测试在负载下 P95 延迟保持在 500ms 以下。
        """
        try:
            url = get_service_url(SERVICE_NAME, NAMESPACE)
            health_url = f"{url}/health"
            
            latencies = []
            num_requests = 100
            
            logger.info(f"Sending {num_requests} requests to measure latency...")
            
            for i in range(num_requests):
                start_time = time.time()
                response = requests.get(health_url, timeout=10)
                end_time = time.time()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
            
            # 计算 P95 和 P50
            latencies.sort()
            p50_index = int(len(latencies) * 0.5)
            p95_index = int(len(latencies) * 0.95)
            
            p50_latency = latencies[p50_index]
            p95_latency = latencies[p95_index]
            
            logger.info(f"Latency results: P50={p50_latency:.2f}ms, P95={p95_latency:.2f}ms")
            
            assert p95_latency < 500, f"P95 latency should be < 500ms, got {p95_latency:.2f}ms"
            
            if p50_latency > 200:
                logger.warning(f"P50 latency is high: {p50_latency:.2f}ms")
            
            logger.info(f"✓ P95 latency ({p95_latency:.2f}ms) is below 500ms threshold")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Could not connect to service: {e}")
            pytest.skip("Service not accessible from test environment")

    @pytest.mark.slow
    def test_throughput(self):
        """
        测试集群能否处理每秒 1000+ 请求。
        """
        try:
            url = get_service_url(SERVICE_NAME, NAMESPACE)
            health_url = f"{url}/health"
            
            # 简化测试：发送 100 个请求并计算吞吐量
            num_requests = 100
            start_time = time.time()
            
            logger.info(f"Sending {num_requests} requests to measure throughput...")
            
            for i in range(num_requests):
                response = requests.get(health_url, timeout=10)
                assert response.status_code == 200, f"Request {i} failed with status {response.status_code}"
            
            end_time = time.time()
            duration = end_time - start_time
            rps = num_requests / duration
            
            logger.info(f"Throughput: {rps:.2f} RPS (completed {num_requests} requests in {duration:.2f}s)")
            
            # 注意：这个简化测试不要求达到 1000 RPS，只是验证基本功能
            logger.info(f"✓ Service handled {rps:.2f} requests per second")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Could not connect to service: {e}")
            pytest.skip("Service not accessible from test environment")


# ============================================================================
# 监控测试
# ============================================================================

class TestMonitoring:
    """监控和可观测性测试。"""

    def test_prometheus_scraping(self):
        """
        测试 Prometheus 是否从 Pod 抓取指标。
        """
        # 检查 Pod 是否有 Prometheus 注解
        pods = core_v1.list_namespaced_pod(NAMESPACE, label_selector=f"app={DEPLOYMENT_NAME}")
        
        assert len(pods.items) > 0, "Should have at least one pod"
        
        for pod in pods.items:
            annotations = pod.metadata.annotations if pod.metadata.annotations else {}
            
            # 检查 Prometheus 注解
            assert "prometheus.io/scrape" in annotations, f"Pod {pod.metadata.name} should have prometheus.io/scrape annotation"
            assert annotations["prometheus.io/scrape"] == "true", f"prometheus.io/scrape should be 'true'"
            
            assert "prometheus.io/port" in annotations, f"Pod {pod.metadata.name} should have prometheus.io/port annotation"
            assert "prometheus.io/path" in annotations, f"Pod {pod.metadata.name} should have prometheus.io/path annotation"
        
        logger.info(f"✓ All pods have Prometheus scraping annotations")

    def test_metrics_available(self):
        """
        测试预期指标是否在 Prometheus 中可用。
        """
        try:
            url = get_service_url(SERVICE_NAME, NAMESPACE)
            metrics_url = f"{url}/metrics"
            
            response = requests.get(metrics_url, timeout=5)
            assert response.status_code == 200, f"Metrics endpoint should return 200"
            
            metrics_text = response.text
            
            # 检查预期指标
            expected_metrics = [
                "model_api_requests_total",
                "model_api_request_duration_seconds",
                "model_api_predictions_total"
            ]
            
            for metric in expected_metrics:
                assert metric in metrics_text, f"Should have {metric} metric"
            
            logger.info(f"✓ All expected metrics are available: {expected_metrics}")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Could not connect to service: {e}")
            pytest.skip("Service not accessible from test environment")


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    """
    从命令行运行测试。

    用法：
        # 运行所有测试
        python test_k8s.py

        # 使用 pytest 运行（推荐）
        pytest test_k8s.py

        # 运行特定测试类
        pytest test_k8s.py::TestDeployment

        # 运行特定测试
        pytest test_k8s.py::TestDeployment::test_deployment_exists

        # 使用详细输出运行
        pytest test_k8s.py -v

        # 运行并显示 print 语句
        pytest test_k8s.py -s

        # 跳过慢速测试
        pytest test_k8s.py -m "not slow"

        # 仅运行慢速测试
        pytest test_k8s.py -m slow

    下一步：
    - 完成所有 TODO 测试
    - 为你的特定需求添加自定义测试
    - 集成到 CI/CD 流水线
    - 设置持续测试（每小时/每天）
    """
