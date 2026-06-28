"""Agent 核心循环 — ReAct 风格的 tool-use loop"""
import json
from typing import Callable

from anthropic import Anthropic

from .config import config
from .tools import TOOL_DEFINITIONS, TOOL_MAP

SYSTEM_PROMPT = """你是一个专业的领域调研 Agent。你的任务是帮助用户深入研究某个领域的知识。

## 工作流程
1. 理解用户的研究主题
2. 使用 web_search 搜索网络上的最新信息
3. 使用 search_papers 检索相关学术论文
4. 如果用户提供了本地文档，使用 read_document 读取分析
5. 综合所有信息，整理出关键发现
6. 最后使用 generate_report 生成结构化报告

## 重要规则
- 对于每个研究主题，至少执行一次网页搜索和一次论文检索
- 先用中文关键词搜索，再用英文关键词搜索，以获得更全面的结果
- 如果搜索结果不理想，尝试调整关键词重新搜索
- 在调用 generate_report 之前，确保已经收集了足够的信息
- 报告中请使用中文撰写，但保留英文的专业术语
- 报告应包含: 领域概览、核心技术/方法、主要挑战、最新进展、代表性论文

## 注意事项
- 每次搜索返回有限的结果，如果领域较广，考虑从不同角度多次搜索
- 不要编造信息，所有结论应基于搜索到的实际内容
"""


class ResearchAgent:
    """领域调研 Agent"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        max_tool_rounds: int = None,
        on_tool_call: Callable = None,
        on_message: Callable = None,
    ):
        """
        初始化 Research Agent。

        Args:
            api_key: Anthropic API Key
            model: 模型名称
            max_tool_rounds: 最大工具调用轮数
            on_tool_call: 工具调用回调 (tool_name, tool_input) -> None
            on_message: 消息回调 (text) -> None
        """
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        self.model = model or config.ANTHROPIC_MODEL
        self.max_tool_rounds = max_tool_rounds or config.MAX_TOOL_ROUNDS
        self.on_tool_call = on_tool_call
        self.on_message = on_message

        self.client = Anthropic(api_key=self.api_key)
        self.messages = []

    def run(self, topic: str, additional_context: str = "") -> str:
        """
        执行领域调研。

        Args:
            topic: 研究主题
            additional_context: 额外的上下文（如本地文档内容）

        Returns:
            最终的研究报告 (Markdown 格式)
        """
        # 构建初始消息
        user_message = f"请帮我调研以下领域: **{topic}**"

        if additional_context:
            user_message += (
                f"\n\n以下是我提供的相关本地文档资料，请结合分析:\n\n{additional_context}"
            )

        self.messages = [{"role": "user", "content": user_message}]

        # Agent 循环
        for round_num in range(self.max_tool_rounds):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.messages,
            )

            # 检查是否有文本回复
            text_content = ""
            tool_uses = []

            for block in response.content:
                if block.type == "text" and block.text.strip():
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_uses.append(block)

            # 输出文本消息
            if text_content and self.on_message:
                self.on_message(text_content)

            # 没有工具调用 → Agent 认为任务完成
            if not tool_uses:
                return self._extract_final_text()

            # 添加 assistant 消息
            self.messages.append(
                {"role": "assistant", "content": response.content}
            )

            # 执行工具调用
            tool_results = []
            for tool_block in tool_uses:
                tool_name = tool_block.name
                tool_input = tool_block.input

                if self.on_tool_call:
                    self.on_tool_call(tool_name, tool_input)

                # 执行工具
                tool_fn = TOOL_MAP.get(tool_name)
                if tool_fn:
                    try:
                        result = tool_fn(**tool_input)
                    except Exception as e:
                        result = f"工具执行错误: {str(e)}"
                else:
                    result = f"未知工具: {tool_name}"

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result,
                    }
                )

            # 将工具结果添加到消息中
            self.messages.append({"role": "user", "content": tool_results})

        # 达到最大轮数，请求生成报告
        final_response = self.client.messages.create(
            model=self.model,
            max_tokens=config.MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=self.messages
            + [
                {
                    "role": "user",
                    "content": "请基于以上所有调研结果，调用 generate_report 生成最终的结构化报告。",
                }
            ],
        )

        return self._extract_final_text(final_response)

    def _extract_final_text(self, final_response=None) -> str:
        """从最终响应中提取文本"""
        if final_response:
            text = "".join(
                b.text for b in final_response.content if b.type == "text"
            )
            if text.strip():
                return text

        # 如果最后的 assistant 消息中有文本
        for msg in reversed(self.messages):
            if msg["role"] == "assistant":
                if isinstance(msg["content"], str):
                    return msg["content"]
                # 处理 content blocks
                text = "".join(
                    b.text
                    for b in msg["content"]
                    if hasattr(b, "text") and b.text
                )
                if text.strip():
                    return text

        return "调研完成，但未能生成最终报告。请检查 API 配置。"
