"""
扫描Python代码中的坏味道：print语句、TODO注释、圈复杂度
"""
import ast
import re
from pathlib import Path
import radon.complexity as radon_cc
from radon.visitors import ComplexityVisitor

class PrintVisitor(ast.NodeVisitor):
    """收集所有print调用的行号"""
    def __init__(self):
        self.print_lines = []

    def visit_Call(self, node):
        # 检查是否为 print(...) 调用
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.print_lines.append(node.lineno)
        self.generic_visit(node)

def scan_print_statements(file_path):
    """返回文件中print语句的行号列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    tree = ast.parse(content, filename=file_path)
    visitor = PrintVisitor()
    visitor.visit(tree)
    return visitor.print_lines

def scan_todo_comments(file_path):
    """返回TODO/FIXME注释的行号和内容"""
    todos = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            # 匹配 # 后面的 TODO 或 FIXME（不区分大小写）
            match = re.search(r'#\s*(TODO|FIXME)(.*)$', line, re.IGNORECASE)
            if match:
                todos.append({
                    'line': lineno,
                    'type': match.group(1).upper(),
                    'text': match.group(2).strip()
                })
    return todos

def check_complexity(file_path, threshold=10):
    """返回圈复杂度超过阈值的函数列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # radon 返回 Complexity 对象列表
    blocks = radon_cc.cc_visit(content)
    high = []
    for block in blocks:
        if block.complexity > threshold:
            high.append({
                'name': block.name,
                'line': block.lineno,
                'complexity': block.complexity
            })
    return high

def scan_file(file_path, config):
    """对一个文件执行所有扫描，返回报告字典"""
    issues = []
    # 只扫描 .py 文件
    if not file_path.endswith('.py'):
        return issues

    # 1. print 语句
    if config.get('checks', {}).get('forbid_print', True):
        prints = scan_print_statements(file_path)
        for line in prints:
            issues.append({
                'file': file_path,
                'line': line,
                'type': 'print_statement',
                'message': '包含 print() 调试语句'
            })

    # 2. TODO 注释
    todos = scan_todo_comments(file_path)
    for todo in todos:
        issues.append({
            'file': file_path,
            'line': todo['line'],
            'type': 'todo_comment',
            'message': f"{todo['type']}: {todo['text']}"
        })

    # 3. 圈复杂度
    threshold = config.get('checks', {}).get('max_cc_complexity', 10)
    complex_funcs = check_complexity(file_path, threshold)
    for func in complex_funcs:
        issues.append({
            'file': file_path,
            'line': func['line'],
            'type': 'high_complexity',
            'message': f"函数 {func['name']} 圈复杂度 {func['complexity']} > {threshold}"
        })

    return issues
