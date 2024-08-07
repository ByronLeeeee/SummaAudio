import time
import json
import configparser
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import ollama_scripts, modelscope_scripts, openai_scripts

config = configparser.ConfigParser()
config.read("config/config.ini", encoding='utf-8')


st.subheader("设置")


system_setting, modelscope_setting, ollama_setting, openai_setting = st.tabs(
    ["系统设置", "Modelscope设置", "Ollama设置", "OpenAI设置"])

with system_setting:
    llm_mode_seletor = st.radio("LLM模式", ["Ollama", "OpenAI"], index=[
                                "Ollama", "OpenAI"].index(config['SYSTEM']['llm_mode']))
    if st.button("保存系统设置"):
        try:
            if llm_mode_seletor == "Ollama":
                config['SYSTEM']['llm_mode'] = "Ollama"
            else:
                config['SYSTEM']['llm_mode'] = "OpenAI"
            with open("config/config.ini", "w", encoding='utf-8') as configfile:
                config.write(configfile)
                st.toast("保存成功", icon="✅")
        except Exception as e:
            st.error(f"保存失败: {e}", icon="❌")

with modelscope_setting:
    modelscope_cache_path = st.text_input(
        "缓存路径", config['MODELSCOPE']['MODELSCOPE_CACHE'])
    output_path = st.text_input("结果输出路径", config['MODELSCOPE']['output_dir'])

    if st.button("保存Modelscope配置"):
        try:
            config['MODELSCOPE']['MODELSCOPE_CACHE'] = modelscope_cache_path
            config['MODELSCOPE']['output_dir'] = output_path
            with open("config/config.ini", "w", encoding='utf-8') as configfile:
                config.write(configfile)
                st.toast("保存成功", icon="✅")
        except Exception as e:
            st.error(f"保存失败: {e}", icon="❌")


with ollama_setting:
    ollama_base = st.text_input("Ollama URL", config['OLLAMA']['base_url'])
    ollama_model = st.selectbox("Ollama模型", ollama_scripts.get_model_list(), index=ollama_scripts.get_model_list(
    ).index(config['OLLAMA']['model']) if config['OLLAMA']['model'] != "" else 0)
    ollama_max_tokens = st.text_input(
        "Ollama Tokens上限", config['OLLAMA']['max_tokens'])
    ollama_temperature = st.slider(
        "Ollama Temperature", 0.0, 1.0, float(config['OLLAMA']['temperature']))
    ollama_top_p = st.slider("Ollama Top_p", 0.0, 1.0,
                             float(config['OLLAMA']['top_p']))

    if st.button("保存Ollama配置"):
        try:
            if ollama_base == "":
                raise Exception("Ollama URL不能为空")
            if ollama_max_tokens == "":
                raise Exception("Tokens上限不能为空")
            if ollama_model == "":
                raise Exception("Ollama模型不能为空")

            config['OLLAMA']['base_url'] = ollama_base
            config['OLLAMA']['model'] = ollama_model
            config['OLLAMA']['max_tokens'] = ollama_max_tokens
            config['OLLAMA']['temperature'] = str(ollama_temperature)
            config['OLLAMA']['top_p'] = str(ollama_top_p)

            with open("config/config.ini", "w", encoding='utf-8') as configfile:
                config.write(configfile)
                st.toast("保存成功", icon="✅")
        except Exception as e:
            st.error(f"保存失败: {e}", icon="❌")

with openai_setting:

    @st.dialog("模型管理")
    def model_manager():
        openai_models = openai_scripts.get_model_info()
        model_editor = st.data_editor(
            openai_models,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "model": st.column_config.TextColumn("模型名称"),
                "base_url": st.column_config.TextColumn("模型地址")
            }
        )

        if st.button("保存模型信息"):
            # 验证所有字段是否填写，同时处理可能的 None 值
            is_valid = all(
                all(value is not None and str(value).strip()
                    != "" for value in item.values())
                for item in model_editor
            )

            if is_valid:
                if openai_scripts.update_model_info(model_editor):
                    st.toast("保存成功! 3秒后自动刷新！", icon="✅")
                    time.sleep(3)
                    st.rerun()
            else:
                st.error("请确保所有字段都已填写，不能留空。")

    if st.button("模型管理"):
        model_manager()

    openai_model = st.selectbox("OpenAI模型", openai_scripts.get_model_list())
    openai_max_tokens = st.text_input(
        "OpenAI Tokens上限", config['OPENAI']['max_tokens'])
    openai_temperature = st.slider(
        "OpenAI Temperature", 0.0, 1.0, float(config['OPENAI']['temperature']))
    openai_top_p = st.slider("OpenAI Top_p", 0.0, 1.0,
                             float(config['OPENAI']['top_p']))

    if st.button("保存OpenAI配置"):
        try:
            if openai_max_tokens == "":
                raise Exception("Tokens上限不能为空")

            config['OPENAI']['model'] = openai_model
            config['OPENAI']['max_tokens'] = openai_max_tokens
            config['OPENAI']['temperature'] = str(openai_temperature)
            config['OPENAI']['top_p'] = str(openai_top_p)

            with open("config/config.ini", "w", encoding='utf-8') as configfile:
                config.write(configfile)
                st.toast("保存成功", icon="✅")
        except Exception as e:
            st.error(f"保存失败: {e}", icon="❌")
