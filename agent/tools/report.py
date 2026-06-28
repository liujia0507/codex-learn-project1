"""结构化报告生成工具"""
from datetime import datetime


def generate_report(
    topic: str,
    findings: str,
    references: list = None,
) -> str:
    """
    生成结构化的 Markdown 调研报告。

    Args:
        topic: 研究主题
        findings: 调研发现的综合总结
        references: 参考文献列表

    Returns:
        完整的 Markdown 格式报告
    """
    if references is None:
        references = []

    today = datetime.now().strftime("%Y-%m-%d")

    ref_section = ""
    if references:
        ref_section = "## 参考文献\n\n"
        for i, ref in enumerate(references, 1):
            ref_section += f"{i}. {ref}\n"

    report = f"""# 领域调研报告: {topic}

**生成日期**: {today}
**调研方式**: AI Agent 自动调研

---

## 摘要

本报告针对 **{topic}** 领域进行了自动化文献调研与信息搜集，综合了网络资源和学术论文的相关信息。

---

## 核心发现

{findings}

---

{ref_section}

## 结论

以上为针对 "{topic}" 领域的自动化调研结果。建议根据实际需求进一步深入查阅所列文献和资源。

---

*本报告由 Research Agent 自动生成 | {today}*
"""
    return report
