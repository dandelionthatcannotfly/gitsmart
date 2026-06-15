"""
配置文件管理（YAML）
"""
import yaml
import os

DEFAULT_CONFIG = {
    'llm': {
        'enabled': False,      # 是否启用LLM生成
        'api_type': 'openai',  # openai / deepseek
        'api_key': '',
        'model': 'gpt-3.5-turbo',
        'max_tokens': 50
    },
    'checks': {
        'max_cc_complexity': 10,
        'max_function_lines': 50,
        'forbid_print': True,
        'require_jira': False
    },
    'conventional_commit': {
        'enabled': True,
        'types': ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']
    }
}

def load_config(config_path='gitsmart.yaml'):
    """加载配置文件，若文件不存在则返回默认配置"""
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG.copy()
    with open(config_path, 'r') as f:
        user_config = yaml.safe_load(f)
    # 合并默认配置（简单合并，只覆盖已有键）
    merged = DEFAULT_CONFIG.copy()
    merged.update(user_config)
    return merged
