"""DevAgent 核心 — 根据调研报告开发实际项目的 Agent"""
import re
from typing import Callable

from anthropic import Anthropic

from .config import config

# Dev Agent 专用工具定义
DEV_TOOL_DEFINITIONS = [
    {
        "name": "write_file",
        "description": "创建一个新文件并写入内容。用于生成项目的源代码、配置、README 等文件。",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "相对于项目目录的文件路径，如 'app.py', 'src/models.py', 'README.md'",
                },
                "content": {
                    "type": "string",
                    "description": "文件的完整内容（源代码、配置等）",
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称，用于创建子目录，如 'todo-app', 'ml-classifier'",
                },
            },
            "required": ["file_path", "content", "project_name"],
        },
    },
    {
        "name": "edit_file",
        "description": "精确修改已有文件中的某段代码。old_string 必须唯一匹配。",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要编辑的文件路径",
                },
                "old_string": {
                    "type": "string",
                    "description": "要替换的原字符串（必须精确匹配且唯一）",
                },
                "new_string": {
                    "type": "string",
                    "description": "替换后的新字符串",
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称",
                },
            },
            "required": ["file_path", "old_string", "new_string", "project_name"],
        },
    },
    {
        "name": "run_shell",
        "description": "在项目目录下执行 shell 命令。用于安装依赖、运行测试、启动应用等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 shell 命令，如 'pip install -r requirements.txt', 'python app.py'",
                },
                "working_dir": {
                    "type": "string",
                    "description": "工作目录（相对于 generated_projects/），如 'todo-app'",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时秒数，默认60",
                    "default": 60,
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "preview_app",
        "description": "在后台启动生成的应用并返回访问 URL。支持 Streamlit、FastAPI、Flask 等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "项目子目录名，如 'todo-app'",
                },
                "command": {
                    "type": "string",
                    "description": "启动命令，如 'streamlit run app.py', 'python -m uvicorn main:app'",
                    "default": "streamlit run app.py",
                },
                "port": {
                    "type": "integer",
                    "description": "端口号，不指定则自动选择空闲端口",
                },
            },
            "required": ["project_dir", "command"],
        },
    },
]

# 工具映射 — 在调用时才导入，避免循环依赖
_DEV_TOOL_MAP = None


def _get_dev_tool_map():
    global _DEV_TOOL_MAP
    if _DEV_TOOL_MAP is None:
        from .tools.code_writer import write_file
        from .tools.shell_exec import run_shell
        from .tools.code_editor import edit_file
        from .tools.preview import preview_app

        _DEV_TOOL_MAP = {
            "write_file": write_file,
            "run_shell": run_shell,
            "edit_file": edit_file,
            "preview_app": preview_app,
        }
    return _DEV_TOOL_MAP


DEV_SYSTEM_PROMPT = """你是一个专业的软件开发 Agent。你的任务是根据调研报告，从零开发一个实际可运行的项目。

## 工作流程

### Phase 1: 规划
1. 仔细分析调研报告，理解领域核心概念和技术
2. 确定最适合的项目类型和技术栈
3. 制定项目结构和文件清单

### Phase 2: 编码
1. 按顺序创建文件，从核心逻辑开始
2. 先写项目配置（requirements.txt / package.json / pyproject.toml）
3. 再写核心代码（主逻辑、模型、API）
4. 最后写入口文件和 UI
5. 使用 write_file 工具创建每个文件
6. 对已有文件进行修改时使用 edit_file

### Phase 3: 验证
1. 使用 run_shell 安装依赖
2. 使用 run_shell 运行基本测试或导入检查
3. 使用 preview_app 启动应用预览

## 项目类型指南
- 调研主题涉及 **Web/API/数据** → Streamlit 应用或 FastAPI 服务
- 调研主题涉及 **机器学习/深度学习** → Python 训练脚本 + 推理脚本
- 调研主题涉及 **工具/自动化** → CLI 工具
- 不确定时 → Streamlit Web 应用

## 代码规范
- Python 代码使用类型注解
- 添加必要的 docstring
- 添加合理的错误处理
- 生成完整的 requirements.txt
- 每个项目必须包含 README.md

## 重要规则
- 项目名使用 kebab-case (如 'ml-image-classifier')
- 每次只写一个文件，等待确认后再写下一个
- 关键文件写完后，可以先安装依赖再继续
- 代码中注释使用中文，变量/函数名使用英文
- 生成的代码必须是可以直接运行的
- 不要写伪代码或省略号（...），写完整的实现
"""


class DevAgent:
    """项目开发 Agent"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        max_tool_rounds: int = None,
        on_tool_call: Callable = None,
        on_message: Callable = None,
        on_file_created: Callable = None,
    ):
        """
        初始化 Dev Agent。

        Args:
            api_key: Anthropic API Key
            model: 模型名称
            max_tool_rounds: 最大工具调用轮数
            on_tool_call: 工具调用回调 (tool_name, tool_input) -> None
            on_message: 消息回调 (text) -> None
            on_file_created: 文件创建回调 (file_path) -> None
        """
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        self.model = model or config.ANTHROPIC_MODEL
        self.max_tool_rounds = max_tool_rounds or config.MAX_TOOL_ROUNDS
        self.on_tool_call = on_tool_call
        self.on_message = on_message
        self.on_file_created = on_file_created

        self.client = Anthropic(api_key=self.api_key)
        self.messages = []
        self.project_name = "default-project"
        self.created_files = []

    def _extract_project_name(self, research_report: str) -> str:
        """从调研报告中提取或生成项目名"""
        # 尝试找第一个标题作为项目名
        title_match = re.search(r"# 领域调研报告:\s*(.+)", research_report)
        if title_match:
            topic = title_match.group(1).strip()
        else:
            # 取第一行非空内容
            lines = [l.strip() for l in research_report.split("\n") if l.strip()]
            topic = lines[0] if lines else "project"

        # 简化为 kebab-case
        import re as re_module

        name = topic.lower()
        name = re_module.sub(r"[^\w\s-]", "", name)
        name = re_module.sub(r"\s+", "-", name)
        return name[:40] or "generated-project"

    def run(
        self,
        research_report: str,
        topic: str = "",
        additional_requirements: str = "",
    ) -> str:
        """
        根据调研报告开发项目。

        Args:
            research_report: 调研报告全文（Markdown）
            topic: 原始研究主题
            additional_requirements: 额外开发需求

        Returns:
            开发结果摘要
        """
        self.project_name = self._extract_project_name(research_report)
        self.created_files = []

        # 构建初始消息
        user_message = f"""请根据以下调研报告，开发一个实际可运行的项目。

## 研究主题
{topic or '从报告中提取'}

## 调研报告
{research_report}
"""

        if additional_requirements:
            user_message += f"\n## 额外需求\n{additional_requirements}\n"

        user_message += f"""
## 开发指令
1. 分析报告，规划项目架构（项目名: {self.project_name}）
2. 逐个创建文件，使用 write_file 工具
3. 所有文件使用 project_name="{self.project_name}"
4. 核心文件写完后，使用 run_shell 安装依赖
5. 最后使用 preview_app 启动预览

请开始规划并编写代码。"""

        self.messages = [{"role": "user", "content": user_message}]

        # Agent 循环
        for round_num in range(self.max_tool_rounds):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                system=DEV_SYSTEM_PROMPT,
                tools=DEV_TOOL_DEFINITIONS,
                messages=self.messages,
            )

            text_content = ""
            tool_uses = []

            for block in response.content:
                if block.type == "text" and block.text.strip():
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_uses.append(block)

            if text_content and self.on_message:
                self.on_message(text_content)

            if not tool_uses:
                return self._build_result_summary()

            self.messages.append(
                {"role": "assistant", "content": response.content}
            )

            # 执行工具调用
            tool_results = []
            for tool_block in tool_uses:
                tool_name = tool_block.name
                tool_input = dict(tool_block.input)

                if self.on_tool_call:
                    self.on_tool_call(tool_name, tool_input)

                tool_map = _get_dev_tool_map()
                tool_fn = tool_map.get(tool_name)

                if tool_fn:
                    try:
                        result = tool_fn(**tool_input)
                    except Exception as e:
                        result = f"工具执行错误: {e}"
                else:
                    result = f"未知工具: {tool_name}"

                # 追踪文件创建
                if tool_name == "write_file" and "成功" in result:
                    fp = tool_input.get("file_path", "")
                    if fp not in self.created_files:
                        self.created_files.append(fp)
                        if self.on_file_created:
                            self.on_file_created(fp)

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result,
                    }
                )

            self.messages.append({"role": "user", "content": tool_results})

        # 最大轮数到达
        return self._build_result_summary()

    def _build_result_summary(self) -> str:
        """构建开发结果摘要"""
        lines = [
            f"## 开发完成: {self.project_name}",
            "",
            f"### 生成的文件 ({len(self.created_files)} 个)",
            "",
        ]
        for f in self.created_files:
            lines.append(f"- `{f}`")

        import os

        from .tools.code_writer import OUTPUT_ROOT

        project_dir = os.path.join(OUTPUT_ROOT, self.project_name)
        lines.extend(
            [
                "",
                f"### 项目目录",
                f"`{project_dir}`",
                "",
                "项目已生成完毕，可在 `generated_projects/` 目录中查看。",
            ]
        )

        return "\n".join(lines)
