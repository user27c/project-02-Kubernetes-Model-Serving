from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import os
import sys
import logging
import signal
import time
from typing import Dict, Any, Optional
from config import Config
import threading
# from model import ModelLoader

# ============================================================================
# 配置
# ============================================================================
MODEL_NAME: str = ""
LOG_LEVEL: str = ""
MAX_BATCH_SIZE: int = 0
PORT: int = 0

def setup_logging() -> logging.Logger:
    '''
    配置应用日志。

    实现日志设置：
    1. 创建 logger 实例
    2. 从 LOG_LEVEL 环境变量设置日志级别
    3. 创建处理器（StreamHandler 用于容器日志）
    4. 设置格式：'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    5. 将 handler 添加到 logger

    返回：
        logging.Logger: 配置好的 logger 实例
    '''
    logger = logging.getLogger('model-api')
    logger.setLevel(getattr(logging, LOG_LEVEL))

logger = None

# ============================================================================
# PROMETHEUS 指标
# ============================================================================

# 计数器：单调递增的值（请求数、错误数、预测数）
# 直方图：值的分布（延迟、推理时间）
# 仪表盘：可以上升或下降的值（模型加载状态、活动连接数）
# 请求计数器
request_count = Counter('model_api_requests_total', 'Total number of requests processed by the model API')
# 求耗时直方图
request_duration = Histogram('model_api_request_duration_seconds', 'Duration of requests processed by the model API')
# 跟踪总预测数
prediction_count = Counter('model_api_predictions_total', 'Total number of predictions processed by the model API')
# 跟踪推理时间
inference_duration = Histogram('model_api_inference_duration_seconds', 'Duration of inference processed by the model API')
# 跟踪模型加载状态
model_loaded_gauge = Gauge('model_api_model_loaded', 'Whether the model is loaded')
# 跟踪当前活动请求数
active_connections = Gauge('model_api_active_connections', 'Number of active connections to the model API')

class ApplicationState:
    '''
    跟踪应用状态用于健康检查和优雅关机。

    此类维护状态信息，供 Kubernetes 探针使用：
    - is_ready：启动期间为 False（模型加载中），加载完成后为 True
    - is_alive：正常运行为 True，关机时为 False
    - model_loaded：模型加载成功后为 True
    - shutdown_event：线程事件配合优雅关机
    '''
    def __init__(self):
        self.is_ready: bool = False
        self.is_alive: bool = True
        self.model_loaded: bool = False
        self.shutdown_event = threading.Event()
        self.model = None
    
    def mark_ready(self):
        self.is_ready = True
        logger.info("Application is ready")

    def mark_not_ready(self) -> None:
        self.is_ready = False
        logger.info("Application is not ready")

    def mark_shutdown(self) -> None:
        self.is_alive = False
        self.shutdown_event()
        logger.info("Application is shutting down")

app_state = ApplicationState()
# ============================================================================
# Flask 应用
# ============================================================================

app = Flask(__name__)

# ============================================================================
# 中间件
# ============================================================================

@app.before_request
def before_request():
    '''
        每个请求前执行的中间件。

    实现：
    1. 增加 active_connections 仪表盘
    2. 存储请求开始时间（用于延迟计算）
    3. 记录请求详情（method, path, client IP）

    Flask 的 request 对象为线程本地，可以安全添加属性：
    request.start_time = time.time()
    '''
    pass

@app.after_request
def after_request(response):
    """
    每个请求后执行的中间件。

    TODO: 实现：
    1. 计算请求耗时（time.time() - request.start_time）
    2. 记录指标：
       - request_duration（直方图）
       - request_count（计数器，带标签）
    3. 减少 active_connections 仪表盘
    4. 记录响应状态和耗时
    参数：
        response：Flask Response 对象
    返回：
        Response 对象（Flask 必须返回）
    """
    pass

@app.route('/health', methods=['GET'])
def health():
    '''
    综合性的健康检查接口，提供给存活性和就绪性探针使用。
    Kubernetes 会调用该接口判断：
    - 存活性：应用是否存活？（需不需要重启？）
    - 就绪性：应用是否准备好接收流量？（需不需要将流量路由过来？）
    实现健康检查逻辑：
    1. 检查是否正在关停（app_state.is_alive）
    2. 检查模型是否已加载（app_state.model_loaded）
    3. 返回合适的状态码和消息
    返回码：
    - 200 OK：健康且就绪
    - 503 Service Unavailable：未就绪（模型加载中）或正在关停
    响应格式：
    {
        "status": "healthy" | "unhealthy",
        "model_loaded": true | false,
        "model_name": "resnet50",
        "uptime_seconds": 123.45
    }

    注：部分实现会分开提供 /health/live 和 /health/ready。为简化，这里使用一个接口同时支持两者。
    '''
    if app_state.is_alive and app_state.model_loaded:
        return jsonify({
            "status": "healthy",
            "model_loaded": app_state.model_loaded,
            "model_name": "resnet50",
            "uptime_seconds": time.time() - app_state.start_time
        }), 200
    else :
        return jsonify({
            "status": "unhealthy",
            "model_loaded": app_state.model_loaded,
            "model_name": "resnet50",
            "uptime_seconds": time.time() - app_state.start_time
        }), 503

@app.route('/health/live', methods=['GET'])
def liveness():
    '''
    专用的存活性探针接口。
    应用存活（未死锁或崩溃）则返回 200。
    若该接口多次返回失败，Kubernetes 会重启该 pod。
    实现存活性检查：
    1. 检查 app_state.is_alive
    2. 存活时返回 200，关停中返回 503

    该探针应宽松——除非应用确实崩溃，否则不要失败。
    '''
    return jsonify({
        "status": app_state.is_alive,
        "model_loaded": app_state.model_loaded,
        "model_name": "resnet50",
        "uptime_seconds": time.time() - app_state.start_time
    }), (200 if app_state.is_alive else 503)

@app.route('/health/ready', methods=['GET'])
def readiness():
    '''
     专用的就绪性探针接口。
    应用准备好提供服务就返回 200。
    若状态异常，Kubernetes 会将 pod 从服务端点中移除。
    实现就绪性检查：
    1. 检查 app_state.is_ready 和 app_state.model_loaded
    2. 可选：检查依赖（数据库、缓存等）
    3. 准备好返回 200，否则 503
    该探针应严格——如果不能正常服务应返回失败。
    '''
    return jsonify({
        "status": app_state.is_ready,
        "model_loaded": app_state.model_loaded,
        "model_name": MODEL_NAME,
        "uptime_seconds": time.time() - app_state.start_time
    }), (200 if app_state.is_ready and app_state.model_loaded else 503)

# ============================================================================
# 指标接口
# ============================================================================

@app.route('/metrics', methods=['GET'])
def metrics():
    '''
    Prometheus 指标接口。
    以 Prometheus 格式暴露指标，供 Prometheus 抓取。
    Prometheus 每 30 秒会采集一次该接口（已在 ServiceMonitor 配置）。
    实现指标接口：
    1. 使用 prometheus_client.generate_latest() 获取指标内容
    2. 用正确的 content type（CONTENT_TYPE_LATEST）返回
    示例输出格式：
    # HELP model_api_requests_total Total requests
    # TYPE model_api_requests_total counter
    model_api_requests_total{endpoint="/predict",method="POST",status_code="200"} 42.0
    返回：
        Response：Prometheus 文本格式的指标
    '''
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# ============================================================================
# API 接口
# ============================================================================

@app.route('/predict', methods=['POST'])
def predict():
    '''
    模型预测接口。
    接收 JSON 输入，执行推理并返回预测结果。
    实现预测接口：
    1. 校验请求为 JSON 格式
    2. 从 request.json 提取输入数据
    3. 校验输入格式及大小（检查 MAX_BATCH_SIZE）
    4. 对推理操作计时
    5. 调用 model.predict(input_data)
    6. 记录指标：
       - prediction_count（计数）
       - inference_duration（推理用时）
    7. 以 JSON 返回预测结果
    8. 错误处理（无效输入/推理失败）
    请求格式：
    {
        "instances": [
            [1, 2, 3, ...],
            [4, 5, 6, ...]
        ]
    }
    响应格式：
    {
        "predictions": [
            {"class": "cat", "confidence": 0.95},
            {"class": "dog", "confidence": 0.87}
        ],
        "model_name": "resnet50",
        "inference_time_ms": 45.2
    }
    错误响应：
    {
        "error": "Invalid input format",
        "details": "Expected 'instances' key in JSON"
    }
    '''
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json()
    if 'instance' not in data:
        return jsonify({"Missing 'instances' in request"}), 400
    if len(data['instance']) > MAX_BATCH_SIZE:
        return jsonify({"error": "Batch size exceeds limit"}), 400
    # 记时并推理
    start_time = time.time()
    try:
        predictions = app_state.model.predict(data['instance'])
        inference_time = (time.time() - start_time) * 1000

        # 记录指标
        prediction_count.labels(model_name=MODEL_NAME, status="success").inc()
        inference_duration.labels(model_name=MODEL_NAME).observe(inference_time/1000)

        return jsonify({
            'predictions': predictions,
            'model_name': MODEL_NAME,
            'inference_time_ms': round(inference_time, 2)
        }), 200
    except Exception as e:
        logger.error(f"Error in predict: {str(e)}")
        prediction_count.labels(model_name=MODEL_NAME, status="error").inc()
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500
    
@app.route('/', methods=['GET'])
def index():
    '''
    根路由 - API 信息。
    实现根路由接口：
    返回基础 API 信息和可用接口信息。
    响应：
    {
        "service": "Model Serving API",
        "version": "2.0",
        "model": "resnet50",
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "metrics": "/metrics"
        }
    }
    '''
    return jsonify({
        "service": "Model Serving API",
        "version": "2.0",
        "model": MODEL_NAME,
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "metrics": "/metrics"
        }
    }), 200

# ============================================================================
# 模型加载
# ============================================================================

def load_model() -> None:
    '''
    在应用启动时加载 ML 模型。

    该函数在应用开始接收流量前调用。
    与就绪性探针密切相关——只有当模型加载完成后应用才标记为就绪。

    实现模型加载：
    1. 记录模型加载开始日志
    2. 导入并初始化 ModelLoader（来自 model.py）
    3. 根据环境变量 MODEL_NAME 加载模型
    4. 保存模型到 app_state.model
    5. 设置 app_state.model_loaded = True
    6. 更新 model_loaded_gauge 指标
    7. 标记应用为已就绪（app_state.mark_ready()）
    8. 处理错误（模型加载失败时记录并退出）
    '''
    from model_loader import ModelLoader
    loader = ModelLoader()
    app_state.model = loader.load()
    app_state.model_loaded = True
    model_loaded_gauge(model_name=MODEL_NAME, version='1.0').set(1)
    app_state.mark_ready()

# ============================================================================
# 优雅关停
# ============================================================================

def handle_shutdown(signum, frame):
    """
     处理关停信号，实现优雅终止。
    Kubernetes 终止 pod 时会发送 SIGTERM：
    1. pod 从服务列表移除（不再接收新流量）
    2. 向容器发送 SIGTERM
    3. 保留期限（默认 30 秒）
    4. 若还未停止则 SIGKILL 强制终止
    实现优雅关停：
    1. 记录收到关停信号的日志
    2. 标记应用不再就绪（app_state.mark_not_ready()）
    3. 稍等以完成活动请求（如等待 2 秒）
    4. 标记应用已关停（app_state.mark_shutdown()）
    5. 记录关停完成日志
    6. 优雅退出
    参数：
        signum：信号编号
        frame：当前栈帧
    """
    logger.info(f"Received signal {signum}, starting graceful shutdown...")
    app_state.mark_not_ready()
    time.sleep(2)
    app_state.mark_shutdown()
    logger.info("Shutdown complete")
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# ============================================================================
# 应用初始化
# ============================================================================

def  initialize_application():
    '''
    启动时初始化应用。
    实现应用初始化：
    1. 记录应用启动及配置信息
    2. 调用 load_model() 加载 ML 模型
    3. 记录初始化完成
    4. 处理启动异常
    该函数会在 Flask 启动 Web 服务前调用。
    '''   
    logger.info("Initializing application...")
    load_model()
    logger.info("Application initialized successfully")

# ============================================================================
# 主入口
# ============================================================================


if __name__ == '__main__':
    """
    应用主入口。

    实现 main：
    1. 初始化应用（加载模型、设置状态）
    2. 启动 Flask 开发服务器

    配置：
    - host: '0.0.0.0'（监听所有地址，容器化部署需此配置）
    - port: 环境变量 PORT（默认为 5000）
    - debug: 生产环境应为 False（可通过环境变量设置）

    注：生产环境应使用 Gunicorn 或 uWSGI 而非 Flask dev server。
    Dockerfile 示例启动命令：
        gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 60 app:app
    """
    initialize_application()

    app.run(host='0.0.0.0', port=PORT, debug=False)