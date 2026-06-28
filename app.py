"""Streamlit Web UI — 领域调研 + 项目开发 串联流水线"""
import os
import tempfile
import streamlit as st

from agent import ResearchAgent, DevAgent
from agent.config import config

st.set_page_config(
    page_title="Research → Dev Pipeline",
    page_icon="🔬",
    layout="wide",
)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("⚙️ 配置")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=config.ANTHROPIC_API_KEY or "",
        help="从 https://console.anthropic.com/ 获取",
        placeholder="sk-ant-...",
    )

    model = st.selectbox(
        "模型",
        options=[
            "claude-sonnet-4-6",
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
            "claude-opus-4-8",
            "claude-fable-5",
        ],
        index=0,
    )

    st.divider()
    st.subheader("🔍 调研配置")
    max_search = st.slider("网页搜索条数", 1, 10, 5, key="search_slider")
    max_papers = st.slider("论文搜索条数", 1, 10, 5, key="papers_slider")
    max_research_rounds = st.slider("最大搜索轮数", 2, 10, 6, key="research_rounds")

    st.divider()
    st.subheader("🛠️ 开发配置")
    enable_dev = st.toggle("启用调研 → 开发流水线", value=True, help="调研完成后可一键生成项目")
    max_dev_rounds = st.slider("最大开发轮数", 5, 20, 12, key="dev_rounds")

    st.divider()
    st.markdown(
        """
    ### 使用说明
    1. 输入 API Key
    2. 输入研究主题
    3. (可选) 上传本地文档
    4. 点击「开始调研」
    5. 查看调研报告
    6. 点击「开始开发」生成项目
    """
    )

# ==================== 状态管理 ====================
defaults = {
    "research_done": False,
    "dev_done": False,
    "research_messages": [],
    "research_tool_calls": [],
    "final_report": "",
    "dev_messages": [],
    "dev_tool_calls": [],
    "dev_result": "",
    "dev_files": [],
    "topic": "",
    "running": False,
    "dev_running": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_all():
    for k, v in defaults.items():
        st.session_state[k] = v


# ==================== 主界面 ====================
st.title("🔬 Research → 🛠️ Dev Pipeline")
st.caption("领域调研 → 自动生成项目，一站式 AI 开发流水线")

# 输入区域
col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input(
        "研究主题",
        placeholder="例如: Transformer 注意力机制的最新进展, 简单的待办事项 Web 应用...",
        key="topic_input",
    )
with col2:
    uploaded_file = st.file_uploader(
        " 上传本地文档 (可选)",
        type=["pdf", "txt", "md"],
    )

# 操作按钮
btn_col1, btn_col2 = st.columns([1, 1])
with btn_col1:
    start_research = st.button(
        "🔬 开始调研",
        type="primary",
        use_container_width=True,
        disabled=not api_key or not topic,
    )
with btn_col2:
    start_dev = st.button(
        "🛠️ 开始开发",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.research_done or st.session_state.dev_running,
    )

if not api_key and topic:
    st.warning("⚠️ 请在侧边栏输入 Anthropic API Key")

# ==================== Phase 1: 调研 ====================
if start_research and api_key and topic:
    reset_all()
    st.session_state.topic = topic
    st.session_state.running = True

    # 处理本地上传
    additional_context = ""
    if uploaded_file:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        from agent.tools.doc_reader import read_document

        additional_context = read_document(tmp_path)

    status_container = st.status("🔬 Agent 正在调研中...", expanded=True)

    def on_research_message(text):
        st.session_state.research_messages.append({"role": "assistant", "content": text})

    def on_research_tool(tool_name, tool_input):
        st.session_state.research_tool_calls.append({"tool": tool_name, "input": tool_input})

    try:
        agent = ResearchAgent(
            api_key=api_key,
            model=model or "claude-sonnet-4-6",
            max_tool_rounds=max_research_rounds,
            on_message=on_research_message,
            on_tool_call=on_research_tool,
        )

        with status_container:
            report = agent.run(topic, additional_context)
            st.session_state.final_report = report

        status_container.update(label="✅ 调研完成", state="complete")
        st.session_state.research_done = True

    except Exception as e:
        status_container.update(label=f"❌ 调研出错: {e}", state="error")
        st.error(f"Agent 执行出错: {e}")

    st.session_state.running = False

# ==================== Phase 2: 开发 ====================
if start_dev and st.session_state.research_done and st.session_state.final_report:
    st.session_state.dev_running = True
    st.session_state.dev_done = False

    dev_status = st.status("🛠️ Dev Agent 正在开发中...", expanded=True)

    def on_dev_message(text):
        st.session_state.dev_messages.append({"role": "assistant", "content": text})

    def on_dev_tool(tool_name, tool_input):
        st.session_state.dev_tool_calls.append({"tool": tool_name, "input": tool_input})

    def on_file_created(file_path):
        st.session_state.dev_files.append(file_path)

    try:
        dev_agent = DevAgent(
            api_key=api_key,
            model=model or "claude-sonnet-4-6",
            max_tool_rounds=max_dev_rounds,
            on_message=on_dev_message,
            on_tool_call=on_dev_tool,
            on_file_created=on_file_created,
        )

        with dev_status:
            result = dev_agent.run(
                research_report=st.session_state.final_report,
                topic=st.session_state.topic,
            )
            st.session_state.dev_result = result

        dev_status.update(label="✅ 开发完成", state="complete")
        st.session_state.dev_done = True

    except Exception as e:
        dev_status.update(label=f"❌ 开发出错: {e}", state="error")
        st.error(f"Dev Agent 执行出错: {e}")

    st.session_state.dev_running = False

# ==================== 结果展示 ====================

# --- 调研工具调用 ---
if st.session_state.research_tool_calls:
    with st.expander("🔧 调研工具调用过程", expanded=False):
        for i, tc in enumerate(st.session_state.research_tool_calls, 1):
            st.markdown(f"**{i}. {tc['tool']}**")
            st.json(tc["input"])
            if i < len(st.session_state.research_tool_calls):
                st.divider()

# --- 调研思考过程 ---
if st.session_state.research_messages:
    with st.expander("💬 调研 Agent 思考过程", expanded=False):
        for msg in st.session_state.research_messages:
            st.markdown(msg["content"])
            st.divider()

# --- 调研报告 ---
if st.session_state.final_report:
    st.divider()
    st.subheader("📋 调研报告")
    st.markdown(st.session_state.final_report)
    st.download_button(
        label="📥 下载报告 (Markdown)",
        data=st.session_state.final_report,
        file_name=f"research_report_{st.session_state.topic.replace(' ', '_')[:50]}.md",
        mime="text/markdown",
        type="secondary",
    )

    # 开发提示
    if enable_dev and not st.session_state.dev_done:
        st.info("💡 调研完成！点击上方 **🛠️ 开始开发** 按钮，自动生成项目代码。")

# --- Dev 工具调用 ---
if st.session_state.dev_tool_calls:
    st.divider()
    with st.expander("🔧 开发工具调用过程", expanded=False):
        for i, tc in enumerate(st.session_state.dev_tool_calls, 1):
            icon = {"write_file": "📝", "edit_file": "✏️", "run_shell": "💻", "preview_app": "🚀"}.get(tc["tool"], "🔧")
            st.markdown(f"**{i}. {icon} {tc['tool']}**")
            st.json(tc["input"])
            if i < len(st.session_state.dev_tool_calls):
                st.divider()

# --- Dev 思考过程 ---
if st.session_state.dev_messages:
    with st.expander("💬 Dev Agent 思考过程", expanded=False):
        for msg in st.session_state.dev_messages:
            st.markdown(msg["content"])
            st.divider()

# --- 开发结果 ---
if st.session_state.dev_result:
    st.divider()
    st.subheader("🛠️ 开发结果")

    # 文件列表
    if st.session_state.dev_files:
        st.markdown("### 📁 生成的文件")
        cols = st.columns(3)
        for i, f in enumerate(st.session_state.dev_files):
            with cols[i % 3]:
                st.code(f, language=None)

    st.markdown(st.session_state.dev_result)
