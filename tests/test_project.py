"""
==========================
GitSmart 完整测试套件
==========================

测试原理（先看这个）:
─────────────────────

1️⃣ 单元测试 (Unit Testing)
   每个测试只测一个函数，排除外部依赖（文件系统、网络、Git）。
   比如测 get_repo() 时不用真实 Git 仓库，用临时目录模拟。

2️⃣ 隔离与 Mock
   外部依赖（API 调用、Git Repo）用 mock（模拟对象）替换，
   保证测试不依赖网络、不依赖真实文件。

3️⃣ Edge Cases（边界情况）
   - 空字符串 / None / 空列表
   - 特殊字符
   - 超大输入
   - 极限值（如阈值边界）

4️⃣ AAA 模式
   Arrange（准备数据）→ Act（调用函数）→ Assert（断言结果）

5️⃣ 覆盖率目标
   每行代码在某个测试中被执行到，包括 if 的 true/false 两个分支。
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

# ============================================================
# 模块 1: branch_parser.py — 分支名解析
# ============================================================
"""
测试原理:
  extract_jira_id: 正则匹配，测各种分支名格式和大小写
  append_jira_to_message: 测追加逻辑、重复检测、None 处理
"""

from gitsmart.branch_parser import extract_jira_id, append_jira_to_message

class TestBranchParser:
    """分支名解析 — 边界情况全覆盖"""

    # ── extract_jira_id ──────────────────────────────────

    def test_extract_standard_jira(self):
        """标准格式: feature/JIRA-123"""
        assert extract_jira_id("feature/JIRA-123") == "JIRA-123"

    def test_extract_lowercase(self):
        """分支名小写 → 返回大写"""
        assert extract_jira_id("bugfix/jira-456") == "JIRA-456"

    def test_extract_mixed_format(self):
        """不同前缀格式"""
        assert extract_jira_id("PROJ-789/some-branch") == "PROJ-789"
        assert extract_jira_id("hotfix/ABC-100-fix-login") == "ABC-100"

    def test_extract_no_match(self):
        """不包含 JIRA 号 → 返回 None（边界情况）"""
        assert extract_jira_id("feature/update-readme") is None

    def test_extract_empty_string(self):
        """空字符串 → None（边界情况）"""
        assert extract_jira_id("") is None

    def test_extract_special_chars(self):
        """带特殊字符的分支名"""
        assert extract_jira_id("feature/ABC-123_fix_test") == "ABC-123"

    # ── append_jira_to_message ──────────────────────────

    def test_append_jira_to_message(self):
        """普通追加"""
        result = append_jira_to_message("fix: 修复登录bug", "JIRA-123")
        assert result == "fix: 修复登录bug [JIRA-123]"

    def test_append_jira_already_present(self):
        """JIRA 号已在消息中 → 不重复追加（边界情况）"""
        result = append_jira_to_message("fix: [JIRA-123] 修复登录bug", "JIRA-123")
        assert result == "fix: [JIRA-123] 修复登录bug"
        # 断言没有变成 "fix: [JIRA-123] 修复登录bug [JIRA-123]"

    def test_append_jira_none(self):
        """JIRA ID 为 None → 保持原样（边界情况）"""
        result = append_jira_to_message("fix: 修复登录bug", None)
        assert result == "fix: 修复登录bug"

    def test_append_jira_empty_message(self):
        """空消息 + 有 JIRA（边界情况）"""
        result = append_jira_to_message("", "JIRA-001")
        assert result == " [JIRA-001]"


# ============================================================
# 模块 2: check_message.py — 提交信息检查
# ============================================================
"""
测试原理:
  validate_conventional_commit: 正则 + 多条规则，每个规则单独测
    包括：格式正确 / 格式错误 / 句号结尾 / 首字母大写
  suggest_type_from_message: 关键词匹配，测每个 type 的触发词
"""

from gitsmart.check_message import (
    validate_conventional_commit,
    suggest_type_from_message,
    VALID_TYPES
)

class TestCheckMessage:
    """提交信息检查 — 完整规则覆盖"""

    # ── validate_conventional_commit ─────────────────────

    def test_valid_commit_no_scope(self):
        """格式正确：type: subject"""
        valid, msg = validate_conventional_commit("feat: add login page")
        assert valid is True

    def test_valid_commit_with_scope(self):
        """格式正确：type(scope): subject"""
        valid, msg = validate_conventional_commit("fix(api): fix timeout bug")
        assert valid is True

    def test_valid_all_types(self):
        """每种 type 都应该通过"""
        for t in VALID_TYPES:
            valid, _ = validate_conventional_commit(f"{t}: test message here")
            assert valid is True, f"type '{t}' 应该合法"

    def test_invalid_no_type(self):
        """没有 type → 不合法"""
        valid, msg = validate_conventional_commit("随便写了个提交")
        assert valid is False
        assert "格式" in msg

    def test_invalid_wrong_type(self):
        """不在预定义列表的 type → 不合法（边界情况）"""
        valid, msg = validate_conventional_commit("xyz: some change")
        assert valid is False

    def test_invalid_no_colon_space(self):
        """冒号后没有空格 → 不合法（常见错误）"""
        valid, msg = validate_conventional_commit("fix:something")
        assert valid is False

    def test_invalid_trailing_period(self):
        """subject 以句号结尾 → 不合法（边界情况）"""
        valid, msg = validate_conventional_commit("docs: update readme.")
        assert valid is False
        assert "句号" in msg

    def test_invalid_subject_capitalized(self):
        """subject 首字母大写 → 不合法（规范要求）"""
        valid, msg = validate_conventional_commit("feat: Add login")
        assert valid is False
        assert "小写" in msg

    def test_empty_message(self):
        """空字符串 → 不合法（边界情况）"""
        valid, msg = validate_conventional_commit("")
        assert valid is False

    # ── suggest_type_from_message ───────────────────────

    def test_suggest_feat(self):
        """含 add/create/implement → feat"""
        assert suggest_type_from_message("add login page") == "feat"
        assert suggest_type_from_message("implement new api") == "feat"

    def test_suggest_fix(self):
        """含 fix/bug → fix"""
        assert suggest_type_from_message("fix crash bug") == "fix"
        assert suggest_type_from_message("resolve timeout") == "fix"

    def test_suggest_docs(self):
        """含 doc/readme → docs"""
        assert suggest_type_from_message("update readme") == "docs"
        # 注意: 'add doc' 中的 'add' 优先匹配 feat，所以用纯 docs 关键词
        assert suggest_type_from_message("write documentation") == "docs"

    def test_suggest_chore_default(self):
        """无匹配关键词 → chore（边界情况）"""
        assert suggest_type_from_message("random stuff") == "chore"

    def test_suggest_empty(self):
        """空字符串 → chore（边界情况）"""
        assert suggest_type_from_message("") == "chore"


# ============================================================
# 模块 3: config.py — 配置管理
# ============================================================
"""
测试原理:
  不依赖真实 YAML 文件，用 tmp_path 临时目录模拟文件。
  load_config 的两种路径：文件存在 / 文件不存在。
"""

from gitsmart.config import load_config, DEFAULT_CONFIG

class TestConfig:
    """配置管理 — 文件存在/不存在双分支"""

    def test_load_default_when_no_file(self):
        """没有配置文件 → 返回默认值（核心分支）"""
        # 用一个不存在的路径
        config = load_config(config_path="/tmp/nonexistent_path/gitsmart.yaml")
        assert config['llm']['enabled'] is False
        assert config['llm']['api_key'] == ''
        assert config['checks']['max_cc_complexity'] == 10

    def test_load_config_from_file(self):
        """有自定义配置文件 → 合并默认值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
llm:
  enabled: true
  api_key: test-key
  model: deepseek-chat
""")
            f.flush()
            config = load_config(config_path=f.name)
            # 自定义值
            assert config['llm']['enabled'] is True
            assert config['llm']['api_key'] == 'test-key'
            # 默认值（文件中没指定，用默认）
            assert config['llm']['max_tokens'] == 50
            assert config['checks']['max_cc_complexity'] == 10
            os.unlink(f.name)

    def test_config_defaults_unchanged(self):
        """多次调用不修改 DEFAULT_CONFIG（防止副作用）"""
        config = load_config(config_path="/tmp/absent.yaml")
        assert DEFAULT_CONFIG['llm']['enabled'] is False  # 原样保留


# ============================================================
# 模块 4: code_scanner.py — 代码扫描
# ============================================================
"""
测试原理:
  用临时 Python 文件模拟被扫描的代码，不依赖项目自身文件。
  覆盖：有/无 print、有/无 TODO、高/低复杂度。
"""

from gitsmart.code_scanner import (
    scan_print_statements,
    scan_todo_comments,
    check_complexity
)

class TestCodeScanner:
    """代码扫描 — 临时文件 + 各类代码模式"""

    def test_scan_print_found(self):
        """有 print → 返回行号"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x=1\nprint(x)\ny=2\nprint('done')\n")
            f.flush()
            lines = scan_print_statements(f.name)
            assert lines == [2, 4]
            os.unlink(f.name)

    def test_scan_print_commented(self):
        """注释里的 print 不算（边界情况）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x=1\n# print('commented')\ny=2\n")
            f.flush()
            lines = scan_print_statements(f.name)
            assert lines == []  # 注释里的 print 不匹配
            os.unlink(f.name)

    def test_scan_print_in_string(self):
        """字符串里的 'print' 不算（边界情况）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('name = "printer"\n')  # printer 不是 print()
            f.flush()
            lines = scan_print_statements(f.name)
            assert lines == []
            os.unlink(f.name)

    def test_scan_todo_found(self):
        """有 TODO/FIXME → 返回正确类型"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# TODO: implement this\nx=1\n# FIXME: bug here\n")
            f.flush()
            todos = scan_todo_comments(f.name)
            assert len(todos) == 2
            assert todos[0]['type'] == 'TODO'
            assert todos[1]['type'] == 'FIXME'
            os.unlink(f.name)

    def test_scan_todo_case_insensitive(self):
        """todo 大小写不敏感（边界情况）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# todo: lowercase\n# TODO: uppercase\n# Todo: mixed\n")
            f.flush()
            todos = scan_todo_comments(f.name)
            assert len(todos) == 3
            os.unlink(f.name)

    def test_scan_todo_empty_file(self):
        """空文件 → []（边界情况）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("\n\n\n")
            f.flush()
            todos = scan_todo_comments(f.name)
            assert todos == []
            os.unlink(f.name)

    def test_check_complexity_below_threshold(self):
        """简单函数 → 不超过阈值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo():\n    return 1\n")
            f.flush()
            high = check_complexity(f.name, threshold=10)
            assert high == []  # 复杂度1 < 10
            os.unlink(f.name)

    def test_check_complexity_above_threshold(self):
        """复杂函数 → 超过阈值被检出"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def foo(x):
    if x > 0:
        if x > 1:
            if x > 2:
                if x > 3:  # 复杂度5
                    return 1
                return 2
            return 3
        return 4
    return 5

def bar():
    return 1  # 复杂度1
""")
            f.flush()
            high = check_complexity(f.name, threshold=3)
            # foo 复杂度5 > 3, bar 复杂度1 < 3
            names = [h['name'] for h in high]
            assert 'foo' in names
            assert 'bar' not in names
            os.unlink(f.name)

    def test_check_complexity_equality_threshold(self):
        """复杂度等于阈值 → 不被检出（边界情况，> 不是 >=）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def func(x):
    if x:  # 复杂度2
        return 1
    return 2
""")
            f.flush()
            high = check_complexity(f.name, threshold=2)
            assert high == []  # 2 > 2 是 False
            os.unlink(f.name)


# ============================================================
# 模块 5: commit_gen.py — LLM 提交信息生成
# ============================================================
"""
测试原理:
  用 unittest.mock.patch 替换真实的 HTTP 请求（不调用 API）。
  测试 LLM 禁用、空 diff、API 成功/失败 四种情况。
"""

from gitsmart.commit_gen import generate_commit_message

class TestCommitGen:
    """LLM 提交信息生成 — Mock 掉真实 API 调用"""

    def test_disabled_llm(self):
        """LLM 未启用 → 返回 None"""
        config = {'llm': {'enabled': False}}
        result = generate_commit_message("some diff", config)
        assert result is None

    def test_empty_diff(self):
        """空的 diff → 返回 None（边界情况）"""
        config = {'llm': {'enabled': True, 'api_key': 'test', 'api_type': 'deepseek'}}
        result = generate_commit_message("", config)
        assert result is None

    @patch('gitsmart.commit_gen.call_deepseek_api')
    def test_deepseek_success(self, mock_call):
        """DeepSeek 调用成功 → 返回提交信息"""
        mock_call.return_value = "feat: add user login"
        config = {
            'llm': {
                'enabled': True,
                'api_type': 'deepseek',
                'api_key': 'test-key',
                'model': 'deepseek-chat',
                'max_tokens': 60
            }
        }
        result = generate_commit_message("+print('hello')", config)
        assert result == "feat: add user login"
        mock_call.assert_called_once()  # 验证 API 被调用了

    @patch('gitsmart.commit_gen.call_deepseek_api')
    def test_deepseek_failure(self, mock_call):
        """DeepSeek 调用失败 → 返回 None（不崩溃）"""
        mock_call.side_effect = Exception("网络超时")
        config = {
            'llm': {
                'enabled': True,
                'api_type': 'deepseek',
                'api_key': 'test-key',
                'model': 'deepseek-chat',
                'max_tokens': 60
            }
        }
        # 即使 API 挂了，也应该优雅返回 None
        result = generate_commit_message("some diff", config)
        assert result is None


# ============================================================
# 模块 6: git_utils.py — Git 操作 (高级)
# ============================================================
"""
测试原理:
  Git 操作需要真实的 Git 仓库。用 tmp_path + git init 创建临时仓库。
  涉及: 无仓库时抛异常、有仓库时正常返回。
  这是集成测试（Integration Test）—— 需要真实 Git。
"""

from gitsmart.git_utils import get_repo, get_current_branch
from git import InvalidGitRepositoryError

class TestGitUtils:
    """Git 工具 — 临时 Git 仓库"""

    def test_get_repo_in_non_repo(self):
        """不在 Git 仓库中 → 抛出异常"""
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(Exception, match="不是Git仓库"):
                get_repo(tmp)

    def test_get_repo_in_git_repo(self):
        """在 Git 仓库中 → 返回 Repo 对象"""
        with tempfile.TemporaryDirectory() as tmp:
            os.system(f"git init {tmp} >/dev/null 2>&1")
            repo = get_repo(tmp)
            assert repo is not None

    def test_get_current_branch(self):
        """获取当前分支名"""
        with tempfile.TemporaryDirectory() as tmp:
            os.system(f"git init {tmp} >/dev/null 2>&1")
            os.system(f"cd {tmp} && git checkout -b test-branch >/dev/null 2>&1")
            branch = get_current_branch(get_repo(tmp))
            assert branch == "test-branch"
