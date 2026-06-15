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

def _deep_merge(default: dict, override: dict) -> dict:
    """深合并字典，嵌套的 dict 递归合并，而不是直接覆盖"""
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path='gitsmart.yaml'):
    """加载配置文件，若文件不存在则返回默认配置"""
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG.copy()
    with open(config_path, 'r') as f:
        user_config = yaml.safe_load(f) or {}
    # 深合并：用户配置只覆盖部分字段，其余保留默认值
    return _deep_merge(DEFAULT_CONFIG, user_config)
