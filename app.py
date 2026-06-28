"""Streamlit Web UI — 领域调研 Agent 交互界面"""
import os
import tempfile
import streamlit as st

from agent import ResearchAgent
from agent.config import config

st.set_page_config(
    page_title="领域调研 Agent",
    page_icon="🔬",
    layout="wide",
)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("⚙️ 配置")

    # API Key
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=config.ANTHROPIC_API_KEY or "",
        help="从 https://console.anthropic.com/ 获取",
        placeholder="sk-ant-...",
    )

    # 模型选择
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
        help="选择使用的 Claude 模型",
    )

    # 搜索配置
    st.divider()
    st.subheader("🔍 搜索配置")
    max_search = st.slider("网页搜索条数", 1, 10, 5)
    max_papers = st.slider("论文搜索条数", 1, 10, 5)
    max_rounds = st.slider("最大搜索轮数", 2, 10, 6)

    st.divider()
    st.markdown(
        """
    ### 使用说明
    1. 输入 API Key
    2. 输入研究主题
    3. (可选) 上传本地 PDF/文档
    4. 点击「开始调研」
    5. 等待 Agent 搜集信息并生成报告
    """
    )

# ==================== 主界面 ====================
st.title("🔬 领域调研 Agent")
st.caption("基于 Claude API 的自动化领域知识调研工具")

# 输入区域
col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input(
        "研究主题",
        placeholder="例如: Transformer 注意力机制的最新进展, 大语言模型幻觉问题研究...",
        key="topic_input",
    )
with col2:
    uploaded_file = st.file_uploader(
        "📎 上传本地文档 (可选)",
        type=["pdf", "txt", "md"],
        help="上传 PDF、TXT 或 Markdown 文档作为额外参考材料",
    )

# 研究按钮
start_btn = st.button(
    "🚀 开始调研",
    type="primary",
    use_container_width=True,
    disabled=not api_key or not topic,
)

if not api_key and topic:
    st.warning("⚠️ 请在侧边栏输入 Anthropic API Key")

# ==================== 状态管理 ====================
if "agent_running" not in st.session_state:
    st.session_state.agent_running = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []
if "final_report" not in st.session_state:
    st.session_state.final_report = ""


def reset_session():
    """重置会话状态"""
    st.session_state.messages = []
    st.session_state.tool_calls = []
    st.session_state.final_report = ""
    st.session_state.agent_running = False


# ==================== 执行调研 ====================
if start_btn and api_key and topic:
    reset_session()
    st.session_state.agent_running = True

    # 处理上传文件
    additional_context = ""
    if uploaded_file:
        # 保存到临时文件
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        ) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        from agent.tools.doc_reader import read_document

        additional_context = read_document(tmp_path)

    # 进度容器
    status_container = st.status("🔬 Agent 正在调研中...", expanded=True)

    # 回调函数
    def on_message(text):
        st.session_state.messages.append({"role": "assistant", "content": text})

    def on_tool_call(tool_name, tool_input):
        st.session_state.tool_calls.append(
            {"tool": tool_name, "input": tool_input}
        )

    # 执行 Agent
    try:
        agent = ResearchAgent(
            api_key=api_key,
            model=model,
            max_tool_rounds=max_rounds,
            on_message=on_message,
            on_tool_call=on_tool_call,
        )

        with status_container:
            st.write("🔄 正在初始化 Agent...")
            report = agent.run(topic, additional_context)
            st.session_state.final_report = report
            st.write("✅ 调研完成!")

        status_container.update(label="✅ 调研完成", state="complete")

    except Exception as e:
        status_container.update(label=f"❌ 出错: {e}", state="error")
        st.error(f"Agent 执行出错: {e}")

    st.session_state.agent_running = False

# ==================== 结果展示 ====================

# 工具调用历史
if st.session_state.tool_calls:
    with st.expander("🔧 工具调用过程", expanded=False):
        for i, tc in enumerate(st.session_state.tool_calls, 1):
            st.markdown(f"**{i}. {tc['tool']}**")
            st.json(tc["input"])
            if i < len(st.session_state.tool_calls):
                st.divider()

# Agent 思考过程
if st.session_state.messages:
    with st.expander("💬 Agent 思考过程", expanded=False):
        for msg in st.session_state.messages:
            st.markdown(msg["content"])
            st.divider()

# 最终报告
if st.session_state.final_report:
    st.divider()
    st.subheader("📋 调研报告")

    # 渲染 markdown
    st.markdown(st.session_state.final_report)

    # 下载按钮
    st.download_button(
        label="📥 下载报告 (Markdown)",
        data=st.session_state.final_report,
        file_name=f"research_report_{topic.replace(' ', '_')[:50]}.md",
        mime="text/markdown",
        type="secondary",
    )
