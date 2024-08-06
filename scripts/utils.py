import json
import streamlit as st
import pyperclip
import configparser

JSON_PATH = 'config/prompts.json'


def load_prompt_json(section: str) -> list:
    with open(JSON_PATH, 'r', encoding="utf-8") as f:
        all_prompts_info = json.load(f)

    target_prompts = all_prompts_info[section]
    return target_prompts


def get_prompts_details(section: str):
    prompt_list = load_prompt_json(section)
    return prompt_list


def copy_text(text):
    pyperclip.copy(str(text))
    st.toast("结果已复制到剪贴板")


def load_config(section: str):
    config = configparser.ConfigParser()
    config.read('config/config.ini', encoding='utf-8')
    return config[section]
