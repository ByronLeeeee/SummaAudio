import streamlit as st
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from scripts.ollama_scripts import generate_ollama_completion
from scripts.openai_scripts import (
    generate_openai_completion,
    get_openai_model_names,
)  # Stays openai_scripts
from scripts.utils import (
    get_prompts_details,
    copy_text_to_clipboard,
    load_config_section,
    extract_and_clean_think_tags,
)

st.subheader("✍️ 文本归纳与摘要")

col_config, col_text_input = st.columns([1, 2])

with col_config:
    st.markdown("#### 配置归纳选项")
    summary_type = st.radio(
        "选择归纳类型:",
        ["摘要", "会议纪要"],
        horizontal=True,
        key="summary_type_selector",
    )

    prompt_category = (
        "summary_prompt" if summary_type == "摘要" else "meeting_minutes_prompt"
    )
    prompt_lists = get_prompts_details(prompt_category)

    default_prompt_content_summary = f"请为以下文本生成一份{summary_type}：\n"
    if not prompt_lists:
        st.warning(f"未能加载“{summary_type}”提示词。请检查`prompts.json`。")
        prompt_titles = []
    else:
        prompt_titles = [prompt["title"] for prompt in prompt_lists]

    selected_prompt_title = st.selectbox(
        f"选择{summary_type}模板:",
        prompt_titles,
        index=0 if prompt_titles else None,
        disabled=not prompt_lists,
        key="summary_prompt_selector",
    )

    current_default_prompt_content_summary = default_prompt_content_summary
    if selected_prompt_title and prompt_lists:
        current_default_prompt_content_summary = next(
            (p["content"] for p in prompt_lists if p["title"] == selected_prompt_title),
            default_prompt_content_summary,
        )

    with st.expander("查看和调整模板", expanded=False):
        edited_prompt_content = st.text_area(
            "模板内容:",
            value=current_default_prompt_content_summary,
            height=150,
            key="summary_prompt_editor",
        )

    generate_button = st.button(
        f"开始生成{summary_type}", type="primary", use_container_width=True
    )

with col_text_input:
    st.markdown("#### 输入待处理文本")
    if st.session_state.get("ft_cleaned_text"):
        use_fix_typo_text = st.radio(
            "使用修正结果？",
            options=["是", "否"],
            index=1,  # 默认选择“否”
            horizontal=True,
            key="use_fix_typo_text",
        )
        if use_fix_typo_text == "是":
            text_to_summarize = st.text_area(
                "待归纳文本:",
                height=400,
                key="summary_text_input",
                placeholder="在此处粘贴或输入需要归纳的文本...",
                value=st.session_state.ft_cleaned_text,
            )
        else:
            text_to_summarize = st.text_area(
                "待归纳文本:",
                height=400,
                key="summary_text_input",
                placeholder="在此处粘贴或输入需要归纳的文本...",
            )
    else:
        text_to_summarize = st.text_area(
            "待归纳文本:",
            height=400,
            key="summary_text_input",
            placeholder="在此处粘贴或输入需要归纳的文本...",
        )

st.markdown("---")
st.subheader("🚀 生成结果")

if "sm_cleaned_text" not in st.session_state:
    st.session_state.sm_cleaned_text = ""
if "sm_thoughts" not in st.session_state:
    st.session_state.sm_thoughts = ""


if generate_button and text_to_summarize:
    if not edited_prompt_content.strip():
        st.error("提示词模板不能为空。")
    else:
        st.session_state.sm_cleaned_text = ""
        st.session_state.sm_thoughts = ""

        with st.spinner(f"正在生成{summary_type}，请稍候..."):
            final_prompt_for_llm = edited_prompt_content + "\n" + text_to_summarize

            full_raw_response = ""
            response_stream = None
            try:
                system_config = load_config_section("SYSTEM")
                llm_mode = system_config.get(
                    "llm_mode", "Ollama"
                )  # 'Ollama' or 'OpenAI'

                if llm_mode == "Ollama":
                    response_stream = generate_ollama_completion(final_prompt_for_llm)
                elif (
                    llm_mode == "OpenAI"
                ):  # This refers to using an OpenAI-compatible API
                    openai_config = load_config_section(
                        "OPENAI"
                    )  # Reads [OPENAI] from config.ini
                    openai_model_name = openai_config.get(
                        "model"
                    )  # Gets default model from [OPENAI]
                    if not openai_model_name:
                        st.error(
                            "默认在线模型未在config.ini中配置。请先在 设置 > 在线模型 页面配置。"
                        )
                        st.stop()
                    # get_openai_model_names() fetches from openai.json
                    available_online_models = get_openai_model_names()
                    if openai_model_name not in available_online_models:
                        st.warning(
                            f"配置的默认在线模型 '{openai_model_name}' 未在 'config/openai.json' 中找到或定义。请检查设置。"
                        )
                    response_stream = generate_openai_completion(
                        final_prompt_for_llm, openai_model_name
                    )
                else:
                    st.error(f"不支持的LLM模式: {llm_mode}")
                    st.stop()

                for chunk in response_stream:
                    full_raw_response += chunk

                cleaned_text, thoughts = extract_and_clean_think_tags(full_raw_response)

                st.session_state["sm_cleaned_text"] = cleaned_text
                st.session_state["sm_thoughts"] = thoughts
                st.success(f"{summary_type}生成完成！")

            except ValueError as ve:
                st.error(f"配置错误: {ve}")
            except Exception as e:
                st.error(f"生成过程中发生错误: {e}")
                st.session_state["sm_cleaned_text"] = full_raw_response
                st.session_state["sm_thoughts"] = f"错误发生，未能解析思考过程: {e}"
elif generate_button and not text_to_summarize:
    st.warning("请输入待归纳的文本。")

if st.session_state.get("sm_thoughts"):
    with st.expander("查看模型的思考过程 🤔"):
        st.markdown(st.session_state.sm_thoughts)
        st.button(
            "复制思考过程",
            on_click=copy_text_to_clipboard,
            args=(st.session_state.sm_thoughts,),
            key="copy_summary_thoughts_result",
        )

if st.session_state.get("sm_cleaned_text"):
    st.markdown(st.session_state.sm_cleaned_text)
    st.button(
        "复制结果到剪贴板",
        on_click=copy_text_to_clipboard,
        args=(st.session_state.sm_cleaned_text,),
        key="copy_summary_cleaned_result",
    )
