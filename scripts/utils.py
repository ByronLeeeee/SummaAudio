import json
import streamlit as st
import pyperclip
import configparser
import logging


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

def setup_logger(name, log_file='logger/log.log', level=logging.INFO):
    """Function to create a logging object and set the level."""
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    handler = logging.FileHandler(log_file)  # 创建一个FileHandler，用于写到本地
    handler.setFormatter(formatter)  # 设置文件日志格式

    console_handler = logging.StreamHandler()  # 创建一个StreamHandler，用于输出到控制台
    console_handler.setFormatter(formatter)  # 设置控制台日志格式

    logger = logging.getLogger(name)
    logger.setLevel(level)  # 设置日志级别

    logger.addHandler(handler)  # 添加文件处理器
    logger.addHandler(console_handler)  # 添加控制台处理器

    return logger
