import pytest
import tempfile
from gitsmart.code_scanner import scan_print_statements, scan_todo_comments, check_complexity

def test_scan_print():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def foo():
    print("hello")
    x = 1
    # print("commented")
""")
        f.flush()
        lines = scan_print_statements(f.name)
        assert lines == [3]  # print 在第3行

def test_scan_todo():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# TODO: implement this\nx=1\n# FIXME bug here\n")
        f.flush()
        todos = scan_todo_comments(f.name)
        assert len(todos) == 2
        assert todos[0]['type'] == 'TODO'
        assert todos[1]['type'] == 'FIXME'

def test_complexity():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def simple():
    return 1

def complex_func(x):
    if x > 0:
        if x > 1:
            return 1
        else:
            return 2
    else:
        return 3
""")
        f.flush()
        high = check_complexity(f.name, threshold=3)
        # simple 复杂度1, complex_func 复杂度4（if嵌套）
        assert len(high) == 1
        assert high[0]['name'] == 'complex_func'
