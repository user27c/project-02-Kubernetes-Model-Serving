from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import os
import sys
import logging
import signal
import time
import threading
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer



# ============================================================================
# 配置
# ============================================================================
MODEL_NAME = "gpt2"
LOG_LEVEL = "INFO"
MAX_BATCH_SIZE = 32
PORT = 5000

# ============================================================================
# 日志配置
# ============================================================================
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model-api')


# ============================================================================
# PROMETHEUS 指标
# ============================================================================

request_count = Counter(
    'model_api_requests_total',
    'Total number of requests processed by the model API',
    labelnames=['model_name', 'method', 'status']
)
request_duration = Histogram(
    'model_api_request_duration_seconds',
    'Duration of requests processed by the model API',
    labelnames=['model_name', 'endpoint']
)
prediction_count = Counter(
    'model_api_predictions_total',
    'Total number of predictions processed by the model API',
    labelnames=['model_name', 'status']
)
inference_duration = Histogram(
    'model_api_inference_duration_seconds',
    'Duration of inference processed by the model API',
    labelnames=['model_name']
)
model_loaded_gauge = Gauge(
    'model_api_model_loaded',
    'Whether the model is loaded'
)
active_connections = Gauge(
    'model_api_active_connections',
    'Number of active connections to the model API'
)

# ============================================================================
# 应用状态
# ============================================================================

class ApplicationState:
    def __init__(self):
        self.is_ready = False  # 初始化为 False，等模型加载完成
        self.is_alive = True
        self.model_loaded = False
        self.model = None
        self.tokenizer = None
        self.device = None
        self.start_time = time.time()

app_state = ApplicationState()

# ============================================================================
# 模型加载
# ============================================================================

def load_model():
    '''加载 GPT2 模型'''
    try:
        logger.info(f"Loading model: {MODEL_NAME}")
        
        # 检测设备
        app_state.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {app_state.device}")
        
        # 设置国内镜像（解决网络问题）
        import os
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        
        # 加载 tokenizer
        logger.info("Loading tokenizer...")
        app_state.tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)
        
        # 加载模型
        logger.info("Loading model weights...")
        app_state.model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)
        app_state.model.to(app_state.device)
        app_state.model.eval()
        
        app_state.model_loaded = True
        app_state.is_ready = True
        
        logger.info(f"Model loaded successfully on {app_state.device}")
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        app_state.is_ready = False
        raise

# 启动时加载模型
logger.info("Starting model loading...")
load_model()

# ============================================================================
# Flask 应用
# ============================================================================

app = Flask(__name__)

# ============================================================================
# API 接口
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    '''健康检查接口'''
    status_code = 200 if app_state.is_alive else 503
    return jsonify({
        "status": "healthy" if app_state.is_alive else "unhealthy",
        "model_loaded": app_state.model_loaded,
        "model_name": MODEL_NAME,
        "uptime_seconds": time.time() - app_state.start_time
    }), status_code

@app.route('/health/live', methods=['GET'])
def liveness():
    '''存活性探针'''
    return jsonify({
        "status": "healthy" if app_state.is_alive else "unhealthy",
        "model_loaded": app_state.model_loaded,
        "model_name": MODEL_NAME,
        "uptime_seconds": time.time() - app_state.start_time
    }), 200 if app_state.is_alive else 503

@app.route('/health/ready', methods=['GET'])
def readiness():
    '''就绪性探针'''
    return jsonify({
        "status": "ready" if app_state.is_ready else "not_ready",
        "model_loaded": app_state.model_loaded,
        "model_name": MODEL_NAME,
        "uptime_seconds": time.time() - app_state.start_time
    }), 200 if app_state.is_ready else 503

@app.route('/metrics', methods=['GET'])
def metrics():
    '''Prometheus 指标接口'''
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/predict', methods=['POST'])
def predict():
    '''预测接口 - 使用 GPT2 模型'''
    if not app_state.is_ready:
        return jsonify({"error": "Model not ready"}), 503
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    # 支持两种输入格式：文本或实例数组
    if 'text' in data:
        input_text = data['text']
    elif 'instance' in data:
        # 兼容旧格式，如果是数组则转为文本
        instance = data['instance']
        if isinstance(instance, list):
            input_text = ' '.join(map(str, instance))
        else:
            input_text = str(instance)
    else:
        return jsonify({"error": "Missing 'text' or 'instance' in request"}), 400
    
    start_time = time.time()
    
    try:
        # Tokenize 输入
        inputs = app_state.tokenizer.encode(input_text, return_tensors="pt")
        if app_state.device == "cuda":
            inputs = inputs.to("cuda")
        
        # 生成
        with torch.no_grad():
            outputs = app_state.model.generate(
                inputs,
                max_length=100,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=app_state.tokenizer.eos_token_id
            )
        
        # 解码输出
        generated_text = app_state.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        inference_time = (time.time() - start_time) * 1000
        
        # 记录指标
        prediction_count.labels(model_name=MODEL_NAME, status="success").inc()
        inference_duration.labels(model_name=MODEL_NAME).observe(inference_time / 1000)
        
        return jsonify({
            'input': input_text,
            'output': generated_text,
            'model_name': MODEL_NAME,
            'inference_time_ms': round(inference_time, 2),
            'device': app_state.device
        }), 200
        
    except Exception as e:
        logger.error(f"Error in predict: {str(e)}")
        prediction_count.labels(model_name=MODEL_NAME, status="error").inc()
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    '''根路由 - API 信息'''
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
# 优雅关停
# ============================================================================

def handle_shutdown(signum, frame):
    '''处理关停信号'''
    logger.info(f"Received signal {signum}, starting graceful shutdown...")
    app_state.is_ready = False
    time.sleep(2)
    app_state.is_alive = False
    logger.info("Shutdown complete")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    logger.info("Initializing application...")
    logger.info("Application initialized successfully")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
