# Git 操作封装：diff、分支、暂存区

"""
Git操作封装：获取暂存区diff、变更文件列表、当前分支名
"""
from git import Repo, InvalidGitRepositoryError
import os

def get_repo(path='.'):
    """获取Git仓库对象，若不在仓库中则抛出异常"""
    try:
        return Repo(path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        raise Exception("当前目录不是Git仓库")

def get_staged_diff(repo=None):
    """返回暂存区与HEAD的diff文本（字符串）"""
    if repo is None:
        repo = get_repo()
    # 如果没有HEAD（首次提交），与空树比较
    if not repo.head.is_valid():
        # 首次提交：git diff --cached --no-index /dev/null <files> 复杂，简化处理返回空
        # 实际可以获取所有暂存文件并显示内容，为了MVP返回空字符串
        return ""
    diff = repo.git.diff('--cached')
    return diff

def get_staged_files(repo=None):
    """返回暂存区变更的文件路径列表（相对于仓库根目录）"""
    if repo is None:
        repo = get_repo()
    # 获取暂存区变动的文件
    diff_index = repo.index.diff('HEAD') if repo.head.is_valid() else repo.index.diff(None)
    return [item.a_path for item in diff_index]

def get_current_branch(repo=None):
    if repo is None:
        repo = get_repo()
    return repo.active_branch.name

# 测试用（后续可删除）
if __name__ == '__main__':
    print("当前分支:", get_current_branch())
    print("暂存文件:", get_staged_files())
    print("Diff预览:", get_staged_diff()[:200])