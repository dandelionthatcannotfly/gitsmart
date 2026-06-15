"""
检查提交信息是否符合 Conventional Commits 格式
并提供一个基于 TF‑IDF 的简单类型分类器（进阶可选）
"""
import re

# 预定义的有效类型
VALID_TYPES = ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']

def validate_conventional_commit(message: str) -> tuple[bool, str]:
    """
    检查是否符合格式: type(scope?): subject
    subject 不超过50字符，不以句号结尾，首字母不大写强制（可选）
    返回 (是否通过, 错误说明)
    """
    message = message.strip()
    # 基本正则：允许 scope 可选
    pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}$'
    if not re.match(pattern, message):
        return False, "格式应为 '<type>(<scope>): <subject>'，subject 长度1-50"

    # 额外：subject 不能以句号结尾
    subject = message.split(':', 1)[1].strip()
    if subject.endswith('.'):
        return False, "subject 末尾不要加句号"

    # 可选：首字母小写（很多规范要求）
    if subject[0].isupper():
        return False, "subject 建议以小写字母开头"

    return True, "格式正确"

def suggest_type_from_message(message: str) -> str:
    """
    简易关键词匹配（代替 ML 分类器，更容易理解）
    根据消息中的关键词猜测 type
    """
    msg_lower = message.lower()
    if any(w in msg_lower for w in ['add', 'create', 'implement', 'new']):
        return 'feat'
    if any(w in msg_lower for w in ['fix', 'bug', 'resolve', 'repair']):
        return 'fix'
    if any(w in msg_lower for w in ['doc', 'readme', 'comment']):
        return 'docs'
    if any(w in msg_lower for w in ['style', 'format', 'lint']):
        return 'style'
    if any(w in msg_lower for w in ['refactor', 'rename', 'move']):
        return 'refactor'
    if any(w in msg_lower for w in ['test', 'spec']):
        return 'test'
    return 'chore'
