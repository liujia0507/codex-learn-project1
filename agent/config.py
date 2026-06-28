"""配置管理模块 — 从环境变量读取配置"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Agent 全局配置"""

    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    # 搜索
    SEARCH_MAX_RESULTS: int = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
    PAPER_MAX_RESULTS: int = int(os.getenv("PAPER_MAX_RESULTS", "5"))

    # Agent
    MAX_TOOL_ROUNDS: int = int(os.getenv("MAX_TOOL_ROUNDS", "6"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))

    @classmethod
    def validate(cls) -> bool:
        """验证必要配置是否存在"""
        if not cls.ANTHROPIC_API_KEY:
            return False
        return True


config = Config()
