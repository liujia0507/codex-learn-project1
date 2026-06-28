"""学术论文检索工具 — 使用 arXiv API 和 Semantic Scholar API"""
import arxiv
import requests
from typing import Optional


def _search_arxiv(query: str, max_results: int = 5) -> str:
    """通过 arXiv API 搜索论文"""
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        results = list(client.results(search))

        if not results:
            return ""

        parts = ["📄 **arXiv 论文**:\n"]
        for i, paper in enumerate(results, 1):
            authors = ", ".join(a.name for a in paper.authors[:3])
            if len(paper.authors) > 3:
                authors += " et al."
            parts.append(
                f"{i}. **{paper.title}**\n"
                f"   作者: {authors}\n"
                f"   日期: {paper.published.strftime('%Y-%m-%d')}\n"
                f"   摘要: {paper.summary[:300].replace(chr(10), ' ')}...\n"
                f"   PDF: {paper.pdf_url}\n"
            )
        return "\n".join(parts)

    except Exception as e:
        return f"arXiv 搜索出错: {str(e)}"


def _search_semantic_scholar(query: str, max_results: int = 5) -> str:
    """通过 Semantic Scholar API 搜索论文"""
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract,url,citationCount",
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        papers = data.get("data", [])

        if not papers:
            return ""

        parts = ["📄 **Semantic Scholar 论文**:\n"]
        for i, paper in enumerate(papers, 1):
            authors = ", ".join(
                a.get("name", "Unknown") for a in paper.get("authors", [])[:3]
            )
            if len(paper.get("authors", [])) > 3:
                authors += " et al."
            year = paper.get("year", "N/A")
            citations = paper.get("citationCount", 0)
            parts.append(
                f"{i}. **{paper.get('title', '无标题')}**\n"
                f"   作者: {authors}\n"
                f"   年份: {year} | 引用: {citations}\n"
                f"   摘要: {paper.get('abstract', '无摘要')[:300]}...\n"
                f"   链接: {paper.get('url', 'N/A')}\n"
            )
        return "\n".join(parts)

    except Exception as e:
        return f"Semantic Scholar 搜索出错: {str(e)}"


def search_papers(
    query: str,
    max_results: int = 5,
    source: str = "both",
) -> str:
    """
    在学术论文库中检索相关论文。

    Args:
        query: 搜索关键词
        max_results: 最大返回数
        source: 搜索来源 ("arxiv", "semantic_scholar", "both")

    Returns:
        格式化后的论文列表字符串
    """
    parts = [f'🎓 学术论文搜索结果: "{query}"\n']

    if source in ("arxiv", "both"):
        arxiv_results = _search_arxiv(query, max_results)
        if arxiv_results:
            parts.append(arxiv_results)

    if source in ("semantic_scholar", "both"):
        ss_results = _search_semantic_scholar(query, max_results)
        if ss_results:
            parts.append(ss_results)

    if len(parts) == 1:
        return f'未找到与 "{query}" 相关的学术论文。'

    return "\n".join(parts)
