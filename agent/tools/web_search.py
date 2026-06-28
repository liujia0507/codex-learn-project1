"""网页搜索工具 — 使用 DuckDuckGo 进行免费网页搜索"""
from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """
    使用 DuckDuckGo 搜索互联网。

    Args:
        query: 搜索关键词
        max_results: 返回的最大结果数

    Returns:
        格式化后的搜索结��字符串
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f'未找到与 "{query}" 相关的结果。'

        output_parts = [f'🔍 网页搜索结果: "{query}"\n']
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            href = r.get("href", "无链接")
            body = r.get("body", "无摘要")
            output_parts.append(f"{i}. **{title}**\n   URL: {href}\n   摘要: {body}\n")

        return "\n".join(output_parts)

    except Exception as e:
        return f"网页搜索出错: {str(e)}"
