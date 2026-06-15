"""
从分支名提取 JIRA/工单号
"""
import re

def extract_jira_id(branch_name: str) -> str | None:
    """匹配如 JIRA-123, PROJ-456, bugfix/ABC-789"""
    match = re.search(r'([A-Z]+-\d+)', branch_name, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

def append_jira_to_message(message: str, jira_id: str | None) -> str:
    """如果 jira_id 存在且不在消息中，追加到末尾"""
    if not jira_id:
        return message
    if jira_id in message:
        return message
    return f"{message} [{jira_id}]"
