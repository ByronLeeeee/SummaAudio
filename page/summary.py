import streamlit as st
import json
import pyperclip
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ollama_scripts import grenerate as ollama_grenerate
from scripts.openai_scripts import grenerate as openai_grenerate
from scripts.utils import get_prompts_details, copy_text,load_config

st.subheader("文本归纳")

col1, col2 = st.columns(2)


with col1:
    summary_type = st.radio("选择归纳类型:", ["摘要", "会议纪要"])
    if summary_type == "摘要":
        prompt_lists = get_prompts_details("summary_prompt")

    elif summary_type == "会议纪要":
        prompt_lists = get_prompts_details("meeting_minutes_prompt")
    prompt_titles = [prompt['title'] for prompt in prompt_lists]
    prompt_seletor = st.selectbox("选择归纳模板:", prompt_titles)
    with st.expander("查看模板"):
        using_prompt = [prompt['content']
                        for prompt in prompt_lists if prompt['title'] == prompt_seletor][0]
        using_prompt_textarea = st.text_area(
            "模板预览与调整:", using_prompt, height=300)
    generate_btn = st.button("开始归纳")

with col2:
    text = st.text_area("待归纳文本:", height=300)


with st.container():
    st.write("结果:")

    if "sm_result" not in st.session_state:
        st.session_state.sm_result = ""

    if st.session_state.sm_result != "":
        st.write(st.session_state.sm_result)
        del st.session_state.sm_result

    if generate_btn:
        with st.spinner("正在归纳中..."):
            if summary_type == "会议纪要":
                final_prompt = using_prompt_textarea + text
            elif summary_type == "摘要":
                final_prompt = using_prompt_textarea + text
            else:
                final_prompt = text
            if load_config("SYSTEM")['llm_mode'] == 'ollama':
                respone = st.write_stream(ollama_grenerate(final_prompt))
            elif load_config("SYSTEM")['llm_mode'] == 'openai':
                respone = st.write_stream(openai_grenerate(final_prompt))
            st.session_state['sm_result'] = respone
        st.button("复制结果", on_click=copy_text, args=(respone,))
