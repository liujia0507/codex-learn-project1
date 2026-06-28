"""本地文档分析工具 — 支持 PDF、TXT、Markdown 文件"""
import os


def _read_pdf(file_path: str) -> str:
    """使用 PyMuPDF 读取 PDF 文件"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "错误: 请安装 PyMuPDF: pip install PyMuPDF"

    try:
        doc = fitz.open(file_path)
        text_parts = []
        for page_num in range(min(len(doc), 50)):  # 最多读50页
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
        doc.close()

        if not text_parts:
            return "PDF 文件中未找到可提取的文本内容（可能是扫描版 PDF）。"

        return "\n\n".join(text_parts)

    except Exception as e:
        return f"PDF 读取出错: {str(e)}"


def _read_text(file_path: str) -> str:
    """读取纯文本或 Markdown 文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return "文件内容为空。"
        return content
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(file_path, "r", encoding="gbk") as f:
                return f.read()
        except Exception as e:
            return f"文件编码读取出错: {str(e)}"
    except Exception as e:
        return f"文件读取出错: {str(e)}"


def read_document(file_path: str) -> str:
    """
    读取本地文档内容。支持 PDF (.pdf)、文本 (.txt)、Markdown (.md)。

    Args:
        file_path: 文档文件的绝对路径

    Returns:
        文档文本内容
    """
    if not os.path.exists(file_path):
        return f"错误: 文件不存在 — {file_path}"

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        content = _read_pdf(file_path)
        return f"📖 文档内容 ({os.path.basename(file_path)}):\n\n{content}"
    elif ext in (".txt", ".md", ".markdown", ".py", ".json", ".yaml", ".yml"):
        content = _read_text(file_path)
        return f"📖 文档内容 ({os.path.basename(file_path)}):\n\n{content}"
    else:
        return f"暂不支持的文件格式: {ext}。支持的格式: PDF, TXT, MD"
