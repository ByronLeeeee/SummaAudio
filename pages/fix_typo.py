import streamlit as st
import configparser
from scripts.ollama_scripts import generate
import pyperclip
import difflib

config = configparser.ConfigParser()
config.read('config.ini',encoding='utf-8')

st.subheader("修正文本")

col1, col2 = st.columns(2)

with col1:
    text = st.text_area("待修正文本",height=500)
    fix_btn = st.button("开始修正")

with col2:
    st.write("修正结果")
    if fix_btn:
        with st.spinner('修正中...'):
            final_prompt = config['OLLAMA']['fix_typo_prompt'] + text
            
            result = st.write(generate(final_prompt))
        pyperclip.copy(result)
        st.success("修正完毕，结果已复制到剪贴板")