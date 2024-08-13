import configparser
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils import get_prompts_details, copy_text,load_config
from scripts.ollama_scripts import grenerate as ollama_grenerate
from scripts.openai_scripts import grenerate as openai_grenerate

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')


st.subheader("修正文本")

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        prompt_lists = get_prompts_details("fix_typo_prompt")
        prompt_titles = [prompt['title'] for prompt in prompt_lists]
        prompt_seletor = st.selectbox("选择归纳模板:", prompt_titles)
        with st.expander("查看模板"):
            using_prompt = [prompt['content']
                            for prompt in prompt_lists if prompt['title'] == prompt_seletor][0]
            using_prompt_textarea = st.text_area(
                "模板预览与调整:", using_prompt, height=500)

    with col2:
        text = st.text_area("待修正文本", height=300, key="ft_text")


with st.container():
    fix_btn = st.button("开始修正")
    st.write("修正结果")

    if 'ft_result' not in st.session_state:
        st.session_state['ft_result'] = ""

    if st.session_state.ft_result != "":
        st.write(st.session_state.ft_result)
        del st.session_state.ft_result

    if fix_btn:
        with st.spinner('修正中...'):
            final_prompt = using_prompt_textarea + text
            if load_config("SYSTEM")['llm_mode'] == 'ollama':
                respone = st.write_stream(ollama_grenerate(final_prompt))
            elif load_config("SYSTEM")['llm_mode'] == 'openai':
                respone = st.write_stream(openai_grenerate(final_prompt))
            st.session_state['ft_result'] = respone
        st.button("复制结果", on_click=copy_text, args=(respone,))
