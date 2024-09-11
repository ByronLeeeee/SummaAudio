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

import logging

import logging
import os

def setup_logger(name, log_file='logger/log.log', level=logging.INFO):
    """Function to create a logging object and set the level."""
    
    # 参数验证
    if not isinstance(name, str) or not isinstance(log_file, str) or not isinstance(level, int):
        raise ValueError("Invalid parameter type.")
    
    # 确保日志文件所在的目录存在
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            print(f"Failed to create log directory {log_dir}: {e}")
            return None
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 文件处理器
    try:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)
    except Exception as e:
        print(f"Failed to create file handler for {log_file}: {e}")
        return None
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        logger.addHandler(handler)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(console_handler)
    
    return logger
