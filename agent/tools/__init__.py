from .web_search import web_search
from .paper_search import search_papers
from .doc_reader import read_document
from .report import generate_report

# Tool definitions in Anthropic tool-use format
TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": "搜索互联网获取最新信息。用于查找某一领域的最新进展、教程、博客文章等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回的最大结果数，默认5",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_papers",
        "description": "在学术论文库中检索相关论文。支持 arXiv 和 Semantic Scholar。用于查找学术文献、预印本等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "论文搜索关键词",
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回的最大论文数，默认5",
                    "default": 5,
                },
                "source": {
                    "type": "string",
                    "enum": ["arxiv", "semantic_scholar", "both"],
                    "description": "搜索来源: arxiv, semantic_scholar, 或 both",
                    "default": "both",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_document",
        "description": "读取本地文档内容。支持 PDF、TXT、Markdown 格式。用于分析用户上传的论文、笔记等本地资料。",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文档文件的绝对路径",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "generate_report",
        "description": "将所有调研结果整合为结构化的 Markdown 报告。应在调研完成后调用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "研究主题",
                },
                "findings": {
                    "type": "string",
                    "description": "所有调研发现的综合总结",
                },
                "references": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "参考文献列表",
                },
            },
            "required": ["topic", "findings"],
        },
    },
]

# Map tool names to actual functions
TOOL_MAP = {
    "web_search": web_search,
    "search_papers": search_papers,
    "read_document": read_document,
    "generate_report": generate_report,
}
