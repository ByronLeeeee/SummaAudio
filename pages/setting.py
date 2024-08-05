import streamlit as st
import configparser
from scripts import ollama_scripts,modelscope_scripts

config = configparser.ConfigParser()
config.read("config/config.ini",encoding='utf-8')


st.subheader("设置")

modelscope_setting, ollama_setting  = st.tabs(["Modelscope设置","Ollama设置"])


with modelscope_setting:
    modelscope_model_path = st.text_input("模型缓存路径",config['MODELSCOPE']['model_path'])

    pass



with ollama_setting:
    ollama_base = st.text_input("Ollama URL",config['OLLAMA']['ollama_base'])
    ollama_model = st.selectbox("Ollama模型",ollama_scripts.get_model_list(),index=ollama_scripts.get_model_list().index(config['OLLAMA']['model']) if config['OLLAMA']['model'] !="" else 0)
    ollama_max_tokens = st.text_input("Tokens上限",config['OLLAMA']['max_tokens'])
    ollama_temperature = st.slider("Temperature",0.0,1.0,float(config['OLLAMA']['temperature']))
    ollama_top_p = st.slider("Top_p",0.0,1.0,float(config['OLLAMA']['top_p']))

    ftp,sp,mmp = st.tabs(["转录修复prompt","摘要prompt","会议纪要prompt"])
    with ftp:
        fix_typo_prompt = st.text_area("转录修复prompt",eval(f"'{config['OLLAMA']['fix_typo_prompt']}'"),height=500)
    with sp:
        summary_prompt = st.text_area("摘要prompt",eval(f"'{config['OLLAMA']['summary_prompt']}'"),height=500)
    with mmp:
        meeting_minutes_prompt = st.text_area("会议纪要prompt",eval(f"'{config['OLLAMA']['meeting_minutes_prompt']}'"),height=500)

    if st.button("保存"):
        try:
            if ollama_base == "":
                raise Exception("Ollama URL不能为空")
            if ollama_max_tokens == "":
                raise Exception("Tokens上限不能为空")
            if ollama_model == "":
                raise Exception("Ollama模型不能为空")

            config['OLLAMA']['ollama_base'] = ollama_base
            config['OLLAMA']['model'] = ollama_model
            config['OLLAMA']['max_tokens'] = ollama_max_tokens
            config['OLLAMA']['temperature'] = str(ollama_temperature)
            config['OLLAMA']['top_p'] = str(ollama_top_p)
            # 将换行符替换为\n
            summary_prompt_escaped = summary_prompt.replace('\n', '\\n')
            fix_typo_prompt_escaped = fix_typo_prompt.replace('\n', '\\n')
            meeting_minutes_prompt_escaped = meeting_minutes_prompt.replace('\n', '\\n')
            config['OLLAMA']['summary_prompt'] = summary_prompt_escaped
            config['OLLAMA']['fix_typo_prompt'] = fix_typo_prompt_escaped
            config['OLLAMA']['meeting_minutes_prompt'] = meeting_minutes_prompt_escaped
            with open("config/config.ini", "w", encoding='utf-8') as configfile:
                config.write(configfile)
                st.success("保存成功", icon="✅")
        except Exception as e:
            st.error(f"保存失败: {e}", icon="❌")
