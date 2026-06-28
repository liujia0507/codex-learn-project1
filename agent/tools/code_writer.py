"""文件写入工具 — 在 generated_projects/ 下安全地创建文件"""
import os
from pathlib import Path

# 默认输出根目录
OUTPUT_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_projects")


def _sanitize_path(file_path: str, project_name: str = "default") -> str:
    """
    安全化路径，确保所有写入都在 generated_projects/<project_name>/ 下。
    阻止 ../ 等路径穿越攻击。
    """
    # 构建完整路径
    full_path = os.path.normpath(os.path.join(OUTPUT_ROOT, project_name, file_path))

    # 检查是否在允许的目录内
    allowed_root = os.path.normpath(os.path.join(OUTPUT_ROOT, project_name))
    if not full_path.startswith(allowed_root):
        raise ValueError(f"路径穿越被阻止: {file_path}")

    return full_path


def write_file(
    file_path: str,
    content: str,
    project_name: str = "default",
) -> str:
    """
    将内容写入文件。自动创建父目录。

    Args:
        file_path: 相对于项目目录的文件路径（如 "app.py", "src/main.py"）
        content: 文件内容
        project_name: 项目名称，用于组织生成的项目

    Returns:
        操作结果描述
    """
    try:
        full_path = _sanitize_path(file_path, project_name)

        # 创建父目录
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 写入文件
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        relative = os.path.join(project_name, file_path)
        size = len(content)
        return f"文件写入成功: {relative} ({size} 字符)"

    except ValueError as e:
        return f"安全错误: {e}"
    except Exception as e:
        return f"文件写入失败 ({file_path}): {e}"
