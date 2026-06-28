"""应用预览工具 — 后台启动应用并返回访问地址"""
import subprocess
import os
import time
import socket


def _is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """检查端口是否被占用"""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def _find_free_port(start: int = 8501, end: int = 8510) -> int:
    """找一个空闲端口"""
    for port in range(start, end):
        if not _is_port_open(port):
            return port
    return 8501


def preview_app(
    project_dir: str,
    command: str = "streamlit run app.py",
    port: int = None,
) -> str:
    """
    后台启动应用预览。支持 Streamlit / FastAPI / Flask 等。

    Args:
        project_dir: 项目目录（相对于 generated_projects）
        command: 启动命令
        port: 指定端口，不指定则自动查找

    Returns:
        预览地址和状态信息
    """
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "generated_projects",
    )
    full_dir = os.path.normpath(os.path.join(base_dir, project_dir))

    if not os.path.exists(full_dir):
        return f"错误: 项目目录不存在 — {full_dir}"

    if port is None:
        port = _find_free_port()

    # 在命令中替换端口
    cmd = command
    if "streamlit run" in cmd and "--server.port" not in cmd:
        cmd = f"{cmd} --server.port {port}"
    elif "uvicorn" in cmd and "--port" not in cmd:
        cmd = f"{cmd} --port {port}"

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=full_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # 等待一小段时间让服务启动
        time.sleep(2)

        # 检查进程是否存活
        returncode = process.poll()
        if returncode is not None:
            stderr = process.stderr.read()
            return f"应用启动失败 (exit {returncode}):\n{stderr}"

        return f"应用已启动\n  PID: {process.pid}\n  URL: http://localhost:{port}\n  命令: {cmd}\n  目录: {full_dir}"

    except Exception as e:
        return f"预览启动失败: {e}"
