import streamlit as st
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.utils import get_prompts_details, copy_text_to_clipboard, load_config_section
from scripts.ollama_scripts import generate_ollama_completion
from scripts.openai_scripts import generate_openai_completion, get_openai_model_names


st.subheader("修正文本")

with st.container(border=True): # Added border for visual grouping
    col1, col2 = st.columns(2)

    with col1:
        prompt_lists = get_prompts_details("fix_typo_prompt")
        if not prompt_lists:
            st.warning("未能加载“修正文本”提示词。请检查`prompts.json`配置文件。")
            prompt_titles = []
            default_prompt_content = "请修正以下文本中的拼写和语法错误：\n"
        else:
            prompt_titles = [prompt['title'] for prompt in prompt_lists]
        
        selected_prompt_title = st.selectbox(
            "选择修正模板:", 
            prompt_titles,
            index=0 if prompt_titles else None,
            disabled=not prompt_titles
        )
        
        if selected_prompt_title:
            default_prompt_content = next(
                (p['content'] for p in prompt_lists if p['title'] == selected_prompt_title), 
                "请修正以下文本中的拼写和语法错误：\n"
            )
        
        with st.expander("查看和调整模板", expanded=True): # Default to expanded
            edited_prompt_content = st.text_area(
                "模板内容:", 
                value=default_prompt_content, 
                height=200 # Reduced height slightly
            )

    with col2:
        text_to_fix = st.text_area("待修正文本:", height=300, key="ft_text_input")


with st.container():
    fix_button = st.button("开始修正", type="primary")
    
    st.markdown("---") # Separator
    st.write("#### 修正结果")

    if 'ft_result_text' not in st.session_state:
        st.session_state['ft_result_text'] = ""

    # Display previous result if any (useful if page reloads for other reasons)
    if st.session_state.ft_result_text:
        st.info("上次修正结果（点击“开始修正”将更新）：")
        st.markdown(f"```\n{st.session_state.ft_result_text}\n```")


    if fix_button and text_to_fix:
        if not edited_prompt_content.strip():
            st.error("提示词模板不能为空。")
        else:
            with st.spinner('修正中，请稍候...'):
                final_prompt_for_llm = edited_prompt_content + "\n" + text_to_fix
                
                try:
                    system_config = load_config_section("SYSTEM")
                    llm_mode = system_config.get('llm_mode', 'Ollama') # Default to Ollama if not set

                    if llm_mode == 'Ollama':
                        response_stream = generate_ollama_completion(final_prompt_for_llm)
                    elif llm_mode == 'OpenAI':
                        openai_config = load_config_section("OPENAI")
                        openai_model_name = openai_config.get('model')
                        if not openai_model_name:
                            st.error("OpenAI模型未在config.ini中配置。请先在设置页面配置。")
                            st.stop()
                        # Ensure model is available if possible (optional check)
                        available_openai_models = get_openai_model_names()
                        if openai_model_name not in available_openai_models:
                             st.warning(f"配置的OpenAI模型 '{openai_model_name}' 可能不可用或未在 `openai.json` 中定义。尝试继续...")
                        response_stream = generate_openai_completion(final_prompt_for_llm, openai_model_name)
                    else:
                        st.error(f"不支持的LLM模式: {llm_mode}")
                        st.stop()
                    
                    # Use a placeholder to stream the response
                    response_placeholder = st.empty()
                    full_response = ""
                    for chunk in response_stream:
                        full_response += chunk
                        response_placeholder.markdown(full_response) # Render as markdown for better formatting
                    
                    st.session_state['ft_result_text'] = full_response # Store the full response
                    st.success("修正完成！")

                except ValueError as ve: # Catch config errors
                    st.error(f"配置错误: {ve}")
                except Exception as e:
                    st.error(f"修正过程中发生错误: {e}")
                    st.session_state['ft_result_text'] = "" # Clear on error

    # Always show copy button if there's a result in session state
    if st.session_state.get('ft_result_text'):
        st.button("复制结果到剪贴板", on_click=copy_text_to_clipboard, args=(st.session_state.ft_result_text,), key="copy_ft_result")