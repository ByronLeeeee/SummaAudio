from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os
import sys
import json
import configparser

# Ensure the project root is in sys.path for consistent imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import CONFIG_INI_PATH  # Use defined constant

CONFIG_DIR = "config"
OPENAI_CONFIG_JSON_FILE = "openai.json"
OPENAI_JSON_PATH = os.path.join(CONFIG_DIR, OPENAI_CONFIG_JSON_FILE)


def set_openai_client(model_name: str) -> OpenAI:
    """
    根据模型名称设置并返回OpenAI客户端。

    :param model_name: str, 使用的OpenAI模型名称.
    :return: OpenAI, 配置好的OpenAI客户端实例.
    :raises ValueError: 如果模型配置未找到.
    """
    load_dotenv(find_dotenv(usecwd=True))  # Ensure .env is loaded from project root

    with open(OPENAI_JSON_PATH, "r", encoding="utf-8") as f:
        openai_settings = json.load(f)

    model_config = next(
        (
            model
            for model in openai_settings.get("models", [])
            if model.get("model") == model_name
        ),
        None,
    )
    if not model_config:
        raise ValueError(
            f"Model configuration for '{model_name}' not found in '{OPENAI_JSON_PATH}'."
        )

    # Construct the environment variable name for the API key
    # e.g., "gpt-3.5-turbo" -> "GPT_3_5_TURBO_API_KEY"
    api_key_env_var = (
        f"{model_name.upper().replace('-', '_').replace('.', '_')}_API_KEY"
    )
    api_key = os.getenv(api_key_env_var)

    if not api_key:
        raise ValueError(
            f"API key environment variable '{api_key_env_var}' not set for model '{model_name}'."
        )
    if not model_config.get("base_url"):
        raise ValueError(
            f"Base URL not configured for model '{model_name}' in '{OPENAI_JSON_PATH}'."
        )

    client = OpenAI(base_url=model_config["base_url"], api_key=api_key)
    return client


def get_openai_model_names() -> list[str]:
    """
    获取OpenAI配置文件中定义的模型名称列表。

    :return: list[str], 模型名称列表.
    """
    try:
        with open(OPENAI_JSON_PATH, "r", encoding="utf-8") as f:
            openai_settings = json.load(f)
        models = [
            model["model"]
            for model in openai_settings.get("models", [])
            if "model" in model
        ]
        return models
    except FileNotFoundError:
        # st.error(f"OpenAI configuration file not found: {OPENAI_JSON_PATH}") # Avoid st in backend scripts
        print(f"Error: OpenAI configuration file not found: {OPENAI_JSON_PATH}")
        return []
    except Exception as e:
        print(f"Error reading OpenAI model list: {e}")
        return []


def generate_openai_completion(prompt: str, model_name: str):
    """
    使用OpenAI生成文本补全（流式）。

    :param prompt: str, 输入给模型的提示.
    :param model_name: str, 要使用的OpenAI模型名称.
    :return: 生成器, 逐块产生生成的文本.
    """
    client = set_openai_client(model_name)
    config = configparser.ConfigParser()
    config.read(CONFIG_INI_PATH, encoding="utf-8")

    if "OPENAI" not in config:
        raise ValueError(f"Section 'OPENAI' not found in '{CONFIG_INI_PATH}'.")

    options_settings = config["OPENAI"]
    temperature = float(options_settings.get("temperature", 0.7))
    max_tokens = int(options_settings.get("max_tokens", 2560))  # Increased default
    top_p = float(options_settings.get("top_p", 1.0))

    response_stream = client.completions.create(
        model=model_name,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stream=True,
    )
    for part in response_stream:
        if part.choices and len(part.choices) > 0 and part.choices[0].text:
            yield part.choices[0].text


def update_openai_model_info(model_info_list: list[dict]) -> bool:
    """
    更新OpenAI模型配置信息（JSON文件和.env文件）。

    :param model_info_list: list[dict], 包含模型信息的字典列表.
    :return: bool, 操作是否成功.
    :raises Exception: 如果保存过程中发生错误.
    """
    try:
        # Load existing settings to preserve other potential data
        try:
            with open(OPENAI_JSON_PATH, "r", encoding="utf-8") as f:
                openai_settings = json.load(f)
        except FileNotFoundError:
            openai_settings = {}  # Create new if not exists

        new_model_config_list = []
        for model_entry in model_info_list:
            # Basic validation
            if not model_entry.get("model") or not model_entry.get(
                "base_url"
            ):  # API key can be empty if not immediately set
                raise ValueError("Each model entry must have 'model' and 'base_url'.")

            update_model = {
                "model": model_entry.get("model"),
                "base_url": model_entry.get("base_url"),
                # API key is not stored in openai.json, but in .env
            }
            new_model_config_list.append(update_model)

        openai_settings["models"] = new_model_config_list

        with open(OPENAI_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(openai_settings, f, indent=4, ensure_ascii=False)

        env_path = find_dotenv(usecwd=True, raise_error_if_not_found=False)
        if not env_path:
            # If .env file doesn't exist, create one in the current working directory (project root)
            env_path = os.path.join(os.getcwd(), ".env")
            with open(env_path, "w") as f:  # Create empty .env
                pass

        # Load all existing env variables
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, "r") as env_file:
                for line in env_file:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

        # Update or add API keys from the input model_info_list
        for model_data in model_info_list:
            model_name = model_data.get("model", "")
            api_key = model_data.get("api_key", "")
            if model_name and api_key:  # Only write if API key is provided
                env_key_name = (
                    f"{model_name.upper().replace('-', '_').replace('.', '_')}_API_KEY"
                )
                env_vars[env_key_name] = api_key
            elif (
                model_name and not api_key
            ):  # If API key is empty, remove it or ensure it's not written if new
                env_key_name = (
                    f"{model_name.upper().replace('-', '_').replace('.', '_')}_API_KEY"
                )
                if env_key_name in env_vars:
                    del env_vars[env_key_name]

        # Rewrite the .env file with updated keys
        with open(env_path, "w") as env_file:
            for key, value in env_vars.items():
                env_file.write(f"{key}={value}\n")

        load_dotenv(dotenv_path=env_path, override=True)  # Reload environment variables
        return True
    except Exception as e:
        raise Exception(f"保存错误: {e}")


def get_openai_model_info() -> list[dict]:
    """
    获取所有已配置的OpenAI模型及其API密钥（从.env文件）和URL（从JSON文件）。

    :return: list[dict], 模型信息列表.
    :raises Exception: 如果获取信息时发生错误.
    """
    try:
        model_info_list = []
        load_dotenv(find_dotenv(usecwd=True))  # Ensure .env is loaded

        try:
            with open(OPENAI_JSON_PATH, "r", encoding="utf-8") as f:
                openai_models_config = json.load(f).get("models", [])
        except FileNotFoundError:
            openai_models_config = []
            print(
                f"Warning: OpenAI configuration file '{OPENAI_JSON_PATH}' not found. No models loaded."
            )

        for model_conf in openai_models_config:
            model_name = model_conf.get("model")
            if not model_name:
                continue

            api_key_env_var = (
                f"{model_name.upper().replace('-', '_').replace('.', '_')}_API_KEY"
            )

            model_info = {
                "model": model_name,
                "base_url": model_conf.get("base_url"),
                "api_key": os.getenv(
                    api_key_env_var, ""
                ),  # Default to empty string if not found
            }
            model_info_list.append(model_info)

        return model_info_list
    except Exception as e:
        raise Exception(f"获取模型信息错误: {e}")
