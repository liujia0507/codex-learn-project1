"""Shell 命令执行工具 — 在安全限制下执行系统命令"""
import subprocess
import os

# 危险命令黑名单
BLOCKED_COMMANDS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "sudo rm",
    "mkfs.",
    "format",
    "del /F /S",
    "del /f /s",
    "chmod 777 /",
    ":(){ :|:& };:",  # fork bomb
    "shutdown",
    "reboot",
    "dd if=",
]

# 允许的工作目录前缀
ALLOWED_DIRS = [
    os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_projects")),
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # project1 root
]


def _is_safe(command: str, working_dir: str) -> tuple[bool, str]:
    """检查命令是否安全"""
    cmd_lower = command.lower().replace("\\", "/")

    for blocked in BLOCKED_COMMANDS:
        if blocked.lower() in cmd_lower:
            return False, f"命令被安全策略阻止，匹配危险模式: {blocked}"

    # 检查工作目录
    norm_wd = os.path.normpath(working_dir)
    allowed = False
    for ad in ALLOWED_DIRS:
        if norm_wd.startswith(ad):
            allowed = True
            break
    if not allowed:
        return False, f"工作目录不在允许范围内: {working_dir}"

    return True, ""


def run_shell(
    command: str,
    working_dir: str = None,
    timeout: int = 60,
) -> str:
    """
    在安全限制下执行 shell 命令。

    Args:
        command: 要执行的命令
        working_dir: 工作目录，默认为 generated_projects
        timeout: 超时秒数，默认60

    Returns:
        stdout/stderr 输出
    """
    if working_dir is None:
        working_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "generated_projects",
        )

    # 安全检查
    safe, reason = _is_safe(command, working_dir)
    if not safe:
        return f"命令被拒绝: {reason}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        output_parts = []
        if result.stdout:
            output_parts.append(f"[stdout]:\n{result.stdout.strip()}")
        if result.stderr:
            output_parts.append(f"[stderr]:\n{result.stderr.strip()}")
        output_parts.append(f"[exit code]: {result.returncode}")

        return "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return f"命令执行超时 ({timeout}秒): {command}"
    except Exception as e:
        return f"命令执行出错: {e}"
