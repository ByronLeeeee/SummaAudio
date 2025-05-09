import streamlit as st
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.ollama_scripts import generate_ollama_completion
from scripts.openai_scripts import generate_openai_completion, get_openai_model_names
from scripts.utils import get_prompts_details, copy_text_to_clipboard, load_config_section

st.subheader("✍️ 文本归纳与摘要")

col_config, col_text_input = st.columns([1, 2]) # Adjusted column ratio

with col_config:
    st.markdown("#### 配置归纳选项")
    summary_type = st.radio(
        "选择归纳类型:", 
        ["摘要", "会议纪要"], 
        horizontal=True,
        key="summary_type_selector"
    )

    prompt_category = "summary_prompt" if summary_type == "摘要" else "meeting_minutes_prompt"
    prompt_lists = get_prompts_details(prompt_category)

    if not prompt_lists:
        st.warning(f"未能加载“{summary_type}”提示词。请检查`prompts.json`。")
        prompt_titles = []
        default_prompt_content = f"请为以下文本生成一份{summary_type}：\n"
    else:
        prompt_titles = [prompt['title'] for prompt in prompt_lists]
    
    selected_prompt_title = st.selectbox(
        f"选择{summary_type}模板:", 
        prompt_titles,
        index=0 if prompt_titles else None,
        disabled=not prompt_titles,
        key="summary_prompt_selector"
    )
    
    if selected_prompt_title:
        default_prompt_content = next(
            (p['content'] for p in prompt_lists if p['title'] == selected_prompt_title), 
            f"请为以下文本生成一份{summary_type}：\n"
        )

    with st.expander("查看和调整模板", expanded=False):
        edited_prompt_content = st.text_area(
            "模板内容:", 
            value=default_prompt_content, 
            height=150,
            key="summary_prompt_editor"
        )
    
    generate_button = st.button(f"开始生成{summary_type}", type="primary", use_container_width=True)

with col_text_input:
    st.markdown("#### 输入待处理文本")
    text_to_summarize = st.text_area(
        "待归纳文本:", 
        height=400,  # Increased height
        key="summary_text_input",
        placeholder="在此处粘贴或输入需要归纳的文本..."
    )

st.markdown("---")
st.subheader("🚀 生成结果")

if 'sm_result_text' not in st.session_state:
    st.session_state.sm_result_text = ""

if generate_button and text_to_summarize:
    if not edited_prompt_content.strip():
        st.error("提示词模板不能为空。")
    else:
        with st.spinner(f"正在生成{summary_type}，请稍候..."):
            final_prompt_for_llm = edited_prompt_content + "\n" + text_to_summarize
            
            try:
                system_config = load_config_section("SYSTEM")
                llm_mode = system_config.get('llm_mode', 'Ollama')

                if llm_mode == 'Ollama':
                    response_stream = generate_ollama_completion(final_prompt_for_llm)
                elif llm_mode == 'OpenAI':
                    openai_config = load_config_section("OPENAI")
                    openai_model_name = openai_config.get('model')
                    if not openai_model_name:
                        st.error("OpenAI模型未在config.ini中配置。请先在设置页面配置。")
                        st.stop()
                    available_openai_models = get_openai_model_names()
                    if openai_model_name not in available_openai_models:
                         st.warning(f"配置的OpenAI模型 '{openai_model_name}' 可能不可用或未在 `openai.json` 中定义。")
                    response_stream = generate_openai_completion(final_prompt_for_llm, openai_model_name)
                else:
                    st.error(f"不支持的LLM模式: {llm_mode}")
                    st.stop()

                response_placeholder = st.empty()
                full_response = ""
                for chunk in response_stream:
                    full_response += chunk
                    response_placeholder.markdown(full_response) 
                
                st.session_state['sm_result_text'] = full_response
                st.success(f"{summary_type}生成完成！")

            except ValueError as ve:
                st.error(f"配置错误: {ve}")
            except Exception as e:
                st.error(f"生成过程中发生错误: {e}")
                st.session_state['sm_result_text'] = "" # Clear on error
elif generate_button and not text_to_summarize:
    st.warning("请输入待归纳的文本。")


# Display result from session state
if st.session_state.get('sm_result_text'):
    st.text_area("结果预览:", st.session_state.sm_result_text, height=300, disabled=True, key="summary_result_display")
    st.button("复制结果到剪贴板", on_click=copy_text_to_clipboard, args=(st.session_state.sm_result_text,), key="copy_summary_result")