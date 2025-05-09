import streamlit as st
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.utils import get_prompts_details, copy_text_to_clipboard, load_config_section, extract_and_clean_think_tags # MODIFIED
from scripts.ollama_scripts import generate_ollama_completion
from scripts.openai_scripts import generate_openai_completion, get_openai_model_names


st.subheader("修正文本")

with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        prompt_lists = get_prompts_details("fix_typo_prompt")
        
        # --- MODIFICATION START ---
        # Define a fallback default_prompt_content at a higher scope
        fallback_default_prompt_content = "请修正以下文本中的拼写和语法错误：\n"
        
        if not prompt_lists:
            st.warning("未能加载“修正文本”提示词。请检查`prompts.json`配置文件。")
            prompt_titles = []
            # When prompt_lists is empty, current_default_prompt_content will use the fallback
            current_default_prompt_content = fallback_default_prompt_content
        else:
            prompt_titles = [prompt['title'] for prompt in prompt_lists]
        
        selected_prompt_title = st.selectbox(
            "选择修正模板:", 
            prompt_titles,
            index=0 if prompt_titles else None, # No index if no titles
            disabled=not prompt_titles,
            key="fix_typo_prompt_selector" # Added a key
        )
        
        # Determine current_default_prompt_content based on selection or fallback
        if selected_prompt_title and prompt_lists:
            current_default_prompt_content = next(
                (p['content'] for p in prompt_lists if p['title'] == selected_prompt_title), 
                fallback_default_prompt_content # Use fallback if title not found (should not happen if selected_prompt_title is from prompt_titles)
            )
        elif not prompt_lists: # If prompt_lists was empty, this was already set
            pass # current_default_prompt_content is already fallback_default_prompt_content
        else: # prompt_lists exists, but no title selected (e.g. if selectbox is empty due to no prompt_titles)
             current_default_prompt_content = fallback_default_prompt_content
        # --- MODIFICATION END ---
        
        with st.expander("查看和调整模板", expanded=True):
            edited_prompt_content = st.text_area(
                "模板内容:", 
                value=current_default_prompt_content, 
                height=200,
                key="fix_typo_edited_prompt" # Added a key
            )

    with col2:
        text_to_fix = st.text_area("待修正文本:", height=300, key="ft_text_input")


with st.container():
    fix_button = st.button("开始修正", type="primary")
    
    st.markdown("---")
    st.write("#### 修正结果")

    # Initialize session_state keys
    if 'ft_cleaned_text' not in st.session_state:
        st.session_state['ft_cleaned_text'] = ""
    if 'ft_thoughts' not in st.session_state:
        st.session_state['ft_thoughts'] = ""

    if fix_button and text_to_fix:
        if not edited_prompt_content.strip():
            st.error("提示词模板不能为空。")
        else:
            st.session_state['ft_cleaned_text'] = "" # Clear previous results
            st.session_state['ft_thoughts'] = ""   # Clear previous thoughts

            with st.spinner('修正中，请稍候...'):
                final_prompt_for_llm = edited_prompt_content + "\n" + text_to_fix
                
                full_raw_response = ""
                response_stream = None

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
                             st.warning(f"配置的OpenAI模型 '{openai_model_name}' 可能不可用或未在 `openai.json` 中定义。尝试继续...")
                        response_stream = generate_openai_completion(final_prompt_for_llm, openai_model_name)
                    else:
                        st.error(f"不支持的LLM模式: {llm_mode}")
                        st.stop()
                    
                    # Collect the full streaming response
                    # temp_response_placeholder = st.empty() # Optional: for live display of raw stream
                    for chunk in response_stream:
                        full_raw_response += chunk
                        # temp_response_placeholder.markdown(full_raw_response + "▌") 
                    # temp_response_placeholder.empty() 

                    # Process for <think> tags
                    cleaned_text, thoughts = extract_and_clean_think_tags(full_raw_response)
                    
                    st.session_state['ft_cleaned_text'] = cleaned_text
                    st.session_state['ft_thoughts'] = thoughts
                    st.success("修正完成！")

                except ValueError as ve: 
                    st.error(f"配置错误: {ve}")
                except Exception as e:
                    st.error(f"修正过程中发生错误: {e}")
                    st.session_state['ft_cleaned_text'] = full_raw_response # Show raw on error
                    st.session_state['ft_thoughts'] = f"错误发生，未能解析思考过程: {e}"
    
    # Display results outside the button click block to persist them
    if st.session_state.get('ft_cleaned_text'):
        st.markdown(st.session_state.ft_cleaned_text) # Display cleaned text
        st.button("复制修正结果", on_click=copy_text_to_clipboard, args=(st.session_state.ft_cleaned_text,), key="copy_ft_cleaned_result")

    if st.session_state.get('ft_thoughts'):
        with st.expander("查看模型的思考过程 🤔"):
            st.markdown(st.session_state.ft_thoughts)
            st.button("复制思考过程", on_click=copy_text_to_clipboard, args=(st.session_state.ft_thoughts,), key="copy_ft_thoughts_result")