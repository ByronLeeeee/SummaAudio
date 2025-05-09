import json
import streamlit as st
import pyperclip
import configparser
import logging
import os
import re

# Define constants for paths
CONFIG_DIR = "config"
PROMPTS_JSON_FILE = "prompts.json"
CONFIG_INI_FILE = "config.ini"
LOGGER_DIR = "logger"
DEFAULT_LOG_FILE = "log.log"

PROMPTS_JSON_PATH = os.path.join(CONFIG_DIR, PROMPTS_JSON_FILE)
CONFIG_INI_PATH = os.path.join(CONFIG_DIR, CONFIG_INI_FILE)


def load_prompt_json(section: str) -> list:
    """
    从JSON文件中加载指定部分的提示词列表。

    :param section: str, JSON文件中的区域名称 (例如 "fix_typo_prompt").
    :return: list, 包含提示词信息的列表.
    """
    with open(PROMPTS_JSON_PATH, 'r', encoding="utf-8") as f:
        all_prompts_info = json.load(f)
    return all_prompts_info.get(section, [])


def get_prompts_details(section: str) -> list:
    """
    获取指定部分提示词的详细信息。

    :param section: str, 提示词类别 (例如 "fix_typo_prompt").
    :return: list, 提示词详情列表.
    """
    return load_prompt_json(section)


def copy_text_to_clipboard(text_to_copy: str):
    """
    将文本复制到剪贴板。

    :param text_to_copy: str, 需要复制的文本.
    """
    pyperclip.copy(str(text_to_copy))
    st.toast("结果已复制到剪贴板")


def load_config_section(section: str) -> configparser.SectionProxy:
    """
    从INI配置文件中加载指定区域的配置。

    :param section: str, INI文件中的区域名称 (例如 "SYSTEM", "OPENAI").
    :return: configparser.SectionProxy, 配置项代理对象.
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_INI_PATH, encoding='utf-8')
    if section not in config:
        raise ValueError(f"Section '{section}' not found in config file '{CONFIG_INI_PATH}'")
    return config[section]

def setup_logger(name: str, log_filename: str = DEFAULT_LOG_FILE, level=logging.INFO) -> logging.Logger:
    """
    设置并返回一个日志记录器。

    :param name: str, 日志记录器的名称.
    :param log_filename: str, 日志文件的名称 (位于LOGGER_DIR下).
    :param level: int, 日志级别.
    :return: logging.Logger, 配置好的日志记录器实例.
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    full_log_path = os.path.join(LOGGER_DIR, log_filename)
    log_dir = os.path.dirname(full_log_path)

    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_handler = logging.FileHandler(full_log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if logger already exists
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def extract_and_clean_think_tags(text_with_tags: str) -> tuple[str, str]:
    """
    从文本中提取所有 <think>...</think> 标签的内容，并返回清理后的文本和提取的思考内容。

    :param text_with_tags: 包含 <think> 标签的原始文本。
    :return: 一个元组 (cleaned_text, thoughts_text)，
             其中 cleaned_text 是移除了 <think> 标签及其内容的文本，
             thoughts_text 是所有提取到的思考内容（用换行符连接，如果没有则为空字符串）。
    """
    if not text_with_tags:
        return "", ""

    thoughts_list = []
    # 使用非贪婪模式 (.*?) 来匹配标签内容，并使用 re.DOTALL 使 . 匹配换行符
    pattern = r"<think>(.*?)</think>"

    def extract_thought(match):
        thoughts_list.append(match.group(1).strip())
        return ""  # 用空字符串替换匹配到的 <think>...</think> 块

    cleaned_text = re.sub(pattern, extract_thought, text_with_tags, flags=re.DOTALL | re.IGNORECASE)
    
    thoughts_text = "\n\n---\n\n".join(thoughts_list) # 用分隔符连接多个思考块
    
    return cleaned_text.strip(), thoughts_text.strip()