import streamlit as st
from scripts.ollama_scripts import generate
import configparser
import pyperclip

config = configparser.ConfigParser()
config.read("config/config.ini",encoding="utf-8")


st.subheader("文本归纳")

col1, col2 = st.columns(2)


with col1:
    summary_type = st.radio("选择归纳类型:",["摘要","会议纪要"])
    text = st.text_area("待归纳文本:",height=500)
    generate_btn = st.button("开始归纳")
    
with col2: 
    st.write("结果:")
    if generate_btn:
        with st.spinner("正在归纳中..."):
            if summary_type == "会议纪要":
                final_prompt = config['OLLAMA']['meeting_minutes_prompt'] + text
            elif summary_type == "摘要":
                final_prompt = config['OLLAMA']['summary_prompt'] + text
            else:
                final_prompt = text        
            respone = st.write_stream(generate(final_prompt))
            pyperclip.copy(respone)
            st.success("归纳完成，结果已复制到剪贴板")