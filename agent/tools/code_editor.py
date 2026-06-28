"""代码编辑工具 — 精确字符串替换，类似 Claude Edit"""
import os
from .code_writer import OUTPUT_ROOT, _sanitize_path


def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    project_name: str = "default",
) -> str:
    """
    对文件进行精确的字符串替换。old_string 必须在文件中唯一匹配。

    Args:
        file_path: 相对于项目目录的文件路径
        old_string: 要替换的原字符串（必须精确匹配）
        new_string: 替换后的新字符串
        project_name: 项目名称

    Returns:
        操作结果描述
    """
    try:
        full_path = _sanitize_path(file_path, project_name)

        if not os.path.exists(full_path):
            return f"错误: 文件不存在 — {os.path.join(project_name, file_path)}"

        # 读取原文件
        with open(full_path, "r", encoding="utf-8") as f:
            original = f.read()

        # 检查 old_string 是否存在
        count = original.count(old_string)
        if count == 0:
            return f"错误: 未找到匹配的字符串。文件: {os.path.join(project_name, file_path)}"
        if count > 1:
            return f"错误: old_string 匹配了 {count} 处，必须唯一。请提供更精确的上下文。"

        # 创建备份
        backup_path = full_path + ".bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original)

        # 执行替换
        modified = original.replace(old_string, new_string, 1)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(modified)

        return f"编辑成功: {os.path.join(project_name, file_path)} (备份: {os.path.join(project_name, file_path)}.bak)"

    except ValueError as e:
        return f"安全错误: {e}"
    except Exception as e:
        return f"编辑失败 ({file_path}): {e}"
