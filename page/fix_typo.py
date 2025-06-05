import streamlit as st
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.utils import get_prompts_details, copy_text_to_clipboard, load_config_section, extract_and_clean_think_tags
from scripts.ollama_scripts import generate_ollama_completion
from scripts.openai_scripts import generate_openai_completion, get_openai_model_names # Stays openai_scripts


st.subheader("修正文本")

with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        prompt_lists = get_prompts_details("fix_typo_prompt")
        
        fallback_default_prompt_content = "请修正以下文本中的拼写和语法错误：\n"
        
        if not prompt_lists:
            st.warning("未能加载“修正文本”提示词。请检查`prompts.json`配置文件。")
            prompt_titles = []
            current_default_prompt_content = fallback_default_prompt_content
        else:
            prompt_titles = [prompt['title'] for prompt in prompt_lists]
        
        selected_prompt_title = st.selectbox(
            "选择修正模板:", 
            prompt_titles,
            index=0 if prompt_titles else None,
            disabled=not prompt_titles,
            key="fix_typo_prompt_selector"
        )
        
        if selected_prompt_title and prompt_lists:
            current_default_prompt_content = next(
                (p['content'] for p in prompt_lists if p['title'] == selected_prompt_title), 
                fallback_default_prompt_content
            )
        elif not prompt_lists:
            pass 
        else: 
             current_default_prompt_content = fallback_default_prompt_content
        
        with st.expander("查看和调整模板", expanded=True):
            edited_prompt_content = st.text_area(
                "模板内容:", 
                value=current_default_prompt_content, 
                height=250,
                key="fix_typo_edited_prompt"
            )

    with col2:
        if st.session_state.get('transcription_speaker_text'):
            use_transcription_text = st.radio(
                "使用上一页的转录结果？",
                options=["是", "否"],
                index=1,  # 默认选择“否”
                horizontal=True,
                key="use_transcription_text"
            )
            if use_transcription_text == "是":
                text_to_fix = st.text_area("待修正文本:", height=300, key="ft_text_input",value=st.session_state.transcription_speaker_text)
            else:
                text_to_fix = st.text_area("待修正文本:", height=300, key="ft_text_input")
        else:
            text_to_fix = st.text_area("待修正文本:", height=300, key="ft_text_input")


with st.container():
    fix_button = st.button("开始修正", type="primary")
    
    st.markdown("---")
    st.write("#### 修正结果")

    if 'ft_cleaned_text' not in st.session_state:
        st.session_state['ft_cleaned_text'] = ""
    if 'ft_thoughts' not in st.session_state:
        st.session_state['ft_thoughts'] = ""

    if fix_button and text_to_fix:
        if not edited_prompt_content.strip():
            st.error("提示词模板不能为空。")
        else:
            st.session_state['ft_cleaned_text'] = "" 
            st.session_state['ft_thoughts'] = ""

            with st.spinner('修正中，请稍候...'):
                final_prompt_for_llm = edited_prompt_content + "\n" + text_to_fix
                
                full_raw_response = ""
                response_stream = None

                try:
                    system_config = load_config_section("SYSTEM")
                    llm_mode = system_config.get('llm_mode', 'Ollama') # 'Ollama' or 'OpenAI'

                    if llm_mode == 'Ollama':
                        response_stream = generate_ollama_completion(final_prompt_for_llm)
                    elif llm_mode == 'OpenAI': # This refers to using an OpenAI-compatible API
                        openai_config = load_config_section("OPENAI") # Reads [OPENAI] from config.ini
                        openai_model_name = openai_config.get('model') # Gets default model from [OPENAI]
                        if not openai_model_name:
                            st.error("默认在线模型未在config.ini中配置。请先在 设置 > 在线模型 页面配置。")
                            st.stop()
                        # get_openai_model_names() fetches from openai.json
                        available_online_models = get_openai_model_names() 
                        if openai_model_name not in available_online_models:
                             st.warning(f"配置的默认在线模型 '{openai_model_name}' 未在 'config/openai.json' 中找到或定义。请检查设置。")
                             # Potentially stop or allow proceeding if user confirms
                        response_stream = generate_openai_completion(final_prompt_for_llm, openai_model_name)
                    else:
                        st.error(f"不支持的LLM模式: {llm_mode}")
                        st.stop()
                    
                    for chunk in response_stream:
                        full_raw_response += chunk
                    
                    cleaned_text, thoughts = extract_and_clean_think_tags(full_raw_response)
                    
                    st.session_state['ft_cleaned_text'] = cleaned_text
                    st.session_state['ft_thoughts'] = thoughts
                    st.success("修正完成！")

                except ValueError as ve: 
                    st.error(f"配置错误: {ve}")
                except Exception as e:
                    st.error(f"修正过程中发生错误: {e}")
                    st.session_state['ft_cleaned_text'] = full_raw_response 
                    st.session_state['ft_thoughts'] = f"错误发生，未能解析思考过程: {e}"
    
    if st.session_state.get('ft_cleaned_text'):
        st.markdown(st.session_state.ft_cleaned_text)
        st.button("复制修正结果", on_click=copy_text_to_clipboard, args=(st.session_state.ft_cleaned_text,), key="copy_ft_cleaned_result")

    if st.session_state.get('ft_thoughts'):
        with st.expander("查看模型的思考过程 🤔"):
            st.markdown(st.session_state.ft_thoughts)
            st.button("复制思考过程", on_click=copy_text_to_clipboard, args=(st.session_state.ft_thoughts,), key="copy_ft_thoughts_result")