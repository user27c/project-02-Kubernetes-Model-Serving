# 使用 PyTorch 官方镜像（已包含 torch 和 torchvision）
# 这样可以避免在容器内下载 800MB+ 的 torch
FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime

# 设置工作目录
WORKDIR /

# 使用国内 pip 镜像源（解决网络问题）
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
#     pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制依赖文件
COPY requirements.txt .

# 安装其他依赖（排除 torch，因为基础镜像已包含）
# 使用 --no-cache-dir 减少镜像大小
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ .

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动应用
CMD ["python", "app.py"]
