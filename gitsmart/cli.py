"""
命令行入口：gitsmart check / gitsmart generate
"""
import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .git_utils import get_repo, get_staged_diff, get_staged_files, get_current_branch
from .config import load_config
from .code_scanner import scan_file
from .check_message import validate_conventional_commit, suggest_type_from_message
from .branch_parser import extract_jira_id, append_jira_to_message
from .commit_gen import generate_commit_message

console = Console()

@click.group()
def cli():
    """GitSmart - 智能代码审查与提交辅助工具"""
    pass

@cli.command()
@click.option('--generate', is_flag=True, help="生成推荐提交信息")
def check(generate):
    """检查暂存区代码质量，并可选择生成提交信息"""
    # 加载配置
    config = load_config()
    repo = get_repo()
    files = get_staged_files(repo)
    if not files:
        console.print("[yellow]没有暂存的文件，请先 git add[/yellow]")
        sys.exit(0)

    # 1. 代码扫描
    all_issues = []
    for f in files:
        full_path = Path(repo.working_dir) / f
        if full_path.exists():
            issues = scan_file(str(full_path), config)
            all_issues.extend(issues)

    # 显示扫描结果
    if all_issues:
        console.print("[bold red]发现以下问题:[/bold red]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("文件", style="dim")
        table.add_column("行号")
        table.add_column("类型")
        table.add_column("描述")
        for issue in all_issues:
            table.add_row(issue['file'], str(issue['line']), issue['type'], issue['message'])
        console.print(table)
    else:
        console.print("[green]✅ 未发现明显问题[/green]")

    # 2. 提交信息生成（如果请求）
    if generate:
        diff = get_staged_diff(repo)
        if diff:
            msg = generate_commit_message(diff, config)
            if msg:
                console.print(Panel(msg, title="🤖 推荐提交信息", border_style="green"))
            else:
                console.print("[yellow]无法生成提交信息（LLM未启用或失败）[/yellow]")
        else:
            console.print("[yellow]无代码变更差异[/yellow]")

@cli.command()
def hook_pre_commit():
    """供 pre-commit 钩子调用：检查代码质量，有问题则退出码非0"""
    config = load_config()
    repo = get_repo()
    files = get_staged_files(repo)
    issues = []
    for f in files:
        full_path = Path(repo.working_dir) / f
        if full_path.exists():
            issues.extend(scan_file(str(full_path), config))
    if issues:
        console.print("[red]❌ pre-commit 检查失败，请修复以上问题后重新提交[/red]")
        sys.exit(1)
    else:
        console.print("[green]✅ pre-commit 检查通过[/green]")
        sys.exit(0)

@cli.command()
@click.argument('commit_msg_file', type=click.Path())
def hook_commit_msg(commit_msg_file):
    """供 commit-msg 钩子调用：检查提交信息格式，并可自动追加JIRA号"""
    config = load_config()
    # 读取用户编写的提交信息
    with open(commit_msg_file, 'r') as f:
        original_msg = f.read().strip()

    # 1. 格式检查
    if config.get('conventional_commit', {}).get('enabled', True):
        valid, error = validate_conventional_commit(original_msg)
        if not valid:
            console.print(f"[red]提交信息格式错误: {error}[/red]")
            console.print(f"当前信息: {original_msg}")
            sys.exit(1)

    # 2. 自动追加 JIRA ID
    branch = get_current_branch(repo=get_repo())
    jira_id = extract_jira_id(branch)
    new_msg = append_jira_to_message(original_msg, jira_id)
    if new_msg != original_msg:
        console.print(f"[blue]自动追加 JIRA ID: {jira_id}[/blue]")
        with open(commit_msg_file, 'w') as f:
            f.write(new_msg)

    console.print("[green]✅ 提交信息校验通过[/green]")
    sys.exit(0)

if __name__ == '__main__':
    cli()
