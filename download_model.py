#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动下载 GPT2 模型脚本
使用国内镜像源加速下载
"""

import os

# 设置国内镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from transformers import GPT2LMHeadModel, GPT2Tokenizer

def download_model():
    print("开始下载 GPT2 模型...")
    print("使用镜像：hf-mirror.com")
    
    # 下载 tokenizer
    print("\n1. 下载 tokenizer...")
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    print("✓ Tokenizer 下载完成")
    
    # 下载模型
    print("\n2. 下载模型权重...")
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    print("✓ 模型下载完成")
    
    # 验证
    print(f"\n模型大小：{model.num_parameters():,} 参数")
    print("模型已保存到缓存：~/.cache/huggingface/hub/")
    
    # 测试
    print("\n3. 测试模型...")
    input_text = "Hello, I'm a language model"
    inputs = tokenizer.encode(input_text, return_tensors="pt")
    outputs = model.generate(inputs, max_length=30)
    output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"输入：{input_text}")
    print(f"输出：{output_text}")
    print("\n✓ 模型测试成功！")

if __name__ == '__main__':
    download_model()
