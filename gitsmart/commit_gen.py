"""
调用 LLM API 生成提交信息，支持 OpenAI 和 DeepSeek
"""
import os
from typing import Optional
import requests
import json

def call_deepseek_api(prompt: str, api_key: str, model: str = "deepseek-chat", max_tokens=60) -> str:
    """调用 DeepSeek API"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        raise Exception(f"DeepSeek API 错误: {response.text}")

def call_openai_api(prompt: str, api_key: str, model: str = "gpt-3.5-turbo", max_tokens=60) -> str:
    import openai
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def generate_commit_message(diff_text: str, config: dict) -> Optional[str]:
    """
    根据 diff 生成提交信息，返回 None 表示失败或禁用
    """
    llm_config = config.get('llm', {})
    if not llm_config.get('enabled', False):
        return None

    # 限制 diff 长度（前 2000 字符）
    diff_preview = diff_text[:2000]
    if not diff_preview.strip():
        return None

    prompt = f"""你是一个资深开发者。请根据以下代码变更，生成一条符合 Conventional Commits 规范的提交信息。
格式：<type>(<scope>): <subject>
type: feat|fix|docs|style|refactor|test|chore
scope: 可选，模块名（如 api, utils）
subject: 动词开头，不超过50字符

变更内容：
{diff_preview}

只返回一行提交信息，不要额外解释。
"""
    api_type = llm_config.get('api_type', 'openai')
    api_key = llm_config.get('api_key', '')
    model = llm_config.get('model', 'gpt-3.5-turbo')
    max_tokens = llm_config.get('max_tokens', 60)

    try:
        if api_type == 'deepseek':
            return call_deepseek_api(prompt, api_key, model, max_tokens)
        else:
            return call_openai_api(prompt, api_key, model, max_tokens)
    except Exception as e:
        print(f"[WARN] LLM 生成失败: {e}")
        return None
