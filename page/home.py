import streamlit as st

st.title("欢迎使用一键转录！")
st.markdown("---")
st.info("本应用旨在提供便捷的音视频转录、文本修正和内容归纳功能。")

st.subheader("首次使用指南")
st.markdown("""
1.  **检查配置**：首次使用前，请务必前往 **设置** 页面检查并配置相关参数。
    *   **系统设置**：选择您希望使用的LLM（大型语言模型）后端（Ollama或OpenAI）。
    *   **ModelScope设置**：配置语音识别模型相关的缓存路径和结果输出路径。
    *   **Ollama/OpenAI设置**：根据所选LLM模式，配置相应的URL、模型名称、API密钥等。
2.  **准备提示词**：您可以在 **提示词管理** 页面查看、修改或添加用于文本修正和归纳的提示词模板。
3.  **开始使用**：
    *   **一键转录**：上传音频文件，选择所需处理流程，应用将自动完成转录、修正和归纳。
    *   **分步处理**：如果您希望对每个步骤进行更细致的控制，可以使用“音频转录”、“修正文本”、“文本归纳”等独立功能。
""")

st.page_link("page/setting.py", label="➡️ 前往设置页面", icon="⚙️")
st.page_link("page/prompts_manager.py", label="➡️ 管理提示词模板", icon="📚")

st.markdown("---")
st.caption("如果您在使用过程中遇到任何问题，请检查日志文件或相关配置。")
st.caption("也可以访问 [GitHub](https://github.com/ByronLeeeee/summaaudio) 提交问题或反馈。")
st.caption("或者联系微信：legal-lby")
st.caption("Copyright© 2024-2025 ByronLeeeee 李伯阳律师 - 北京市隆安（广州）律师事务所")