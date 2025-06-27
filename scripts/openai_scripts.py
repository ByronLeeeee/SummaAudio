from openai import OpenAI
import os
import sys
import json
import configparser

# Ensure the project root is in sys.path for consistent imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import CONFIG_INI_PATH  # Use defined constant

CONFIG_DIR = "config"
OPENAI_CONFIG_JSON_FILE = "openai.json" # This file will now store API keys too
OPENAI_JSON_PATH = os.path.join(CONFIG_DIR, OPENAI_CONFIG_JSON_FILE)


def set_openai_client(model_name: str) -> OpenAI:
    """
    根据模型名称设置并返回OpenAI兼容客户端。
    API Key 和 Base URL 从 openai.json 读取。

    :param model_name: str, 使用的模型名称.
    :return: OpenAI, 配置好的客户端实例.
    :raises ValueError: 如果模型配置未找到或不完整.
    """
    try:
        with open(OPENAI_JSON_PATH, "r", encoding="utf-8") as f:
            openai_settings = json.load(f)
    except FileNotFoundError:
        raise ValueError(
            f"在线模型配置文件 '{OPENAI_JSON_PATH}' 未找到。"
        )
    except json.JSONDecodeError:
        raise ValueError(
            f"在线模型配置文件 '{OPENAI_JSON_PATH}' 格式错误。"
        )


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
            f"模型 '{model_name}' 的配置未在 '{OPENAI_JSON_PATH}' 中找到。"
        )

    api_key = model_config.get("api_key")
    base_url = model_config.get("base_url")

    if not api_key:
        raise ValueError(
            f"模型 '{model_name}' 的 API Key 未在 '{OPENAI_JSON_PATH}' 中配置。"
        )
    if not base_url:
        raise ValueError(
            f"模型 '{model_name}' 的 Base URL 未在 '{OPENAI_JSON_PATH}' 中配置。"
        )

    client = OpenAI(base_url=base_url, api_key=api_key)
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
        print(f"错误: 在线模型配置文件 '{OPENAI_JSON_PATH}' 未找到。")
        return []
    except Exception as e:
        print(f"读取在线模型列表错误: {e}")
        return []


def generate_openai_completion(prompt: str, model_name: str):
    """
    使用OpenAI兼容的 Chat Completions API 生成文本补全（流式）。

    :param prompt: str, 用户的完整输入提示。
    :param model_name: str, 要使用的模型名称。
    :return: 生成器, 逐块产生生成的文本。
    """
    try:
        client = set_openai_client(model_name)
        config = configparser.ConfigParser()
        config.read(CONFIG_INI_PATH, encoding="utf-8")

        if "OPENAI" not in config:
            raise ValueError(f"区域 'OPENAI' 未在 '{CONFIG_INI_PATH}' 中找到。")

        options_settings = config["OPENAI"]
        temperature = float(options_settings.get("temperature", 0.7))
        max_tokens = int(options_settings.get("max_tokens", 2560))
        top_p = float(options_settings.get("top_p", 1.0))

        response_stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
        )

        for part in response_stream:
            if part.choices and len(part.choices) > 0 and part.choices[0].delta and part.choices[0].delta.content:
                yield part.choices[0].delta.content
    
    except Exception as e:
        yield f"处理OpenAI响应时发生错误: {e}"


def update_openai_model_info(model_info_list: list[dict]) -> bool:
    """
    更新在线模型配置信息（model, base_url, api_key）到 openai.json 文件。

    :param model_info_list: list[dict], 包含模型信息的字典列表.
                           每个字典应包含 'model', 'base_url', 'api_key'.
    :return: bool, 操作是否成功.
    :raises Exception: 如果保存过程中发生错误.
    """
    try:
        # Load existing settings to preserve other potential data not related to "models"
        try:
            with open(OPENAI_JSON_PATH, "r", encoding="utf-8") as f:
                openai_settings = json.load(f)
        except FileNotFoundError:
            openai_settings = {}  # Create new if not exists
        except json.JSONDecodeError:
            # If JSON is corrupted, start fresh but warn user or log
            print(f"警告: '{OPENAI_JSON_PATH}' 格式错误，将创建新的配置。")
            openai_settings = {}


        new_model_config_list = []
        for model_entry in model_info_list:
            # Basic validation
            if not model_entry.get("model") or not model_entry.get("base_url"):
                 # API key can be optional if a model doesn't require it, though most do.
                 # For consistency, we'll expect it, but it could be an empty string.
                raise ValueError("每个模型条目必须包含 'model' 和 'base_url'。API Key 也建议填写。")

            update_model = {
                "model": model_entry.get("model").strip(),
                "base_url": model_entry.get("base_url").strip(),
                "api_key": model_entry.get("api_key", "").strip(), # Store API key directly
            }
            new_model_config_list.append(update_model)

        openai_settings["models"] = new_model_config_list

        # Ensure config directory exists
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        with open(OPENAI_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(openai_settings, f, indent=4, ensure_ascii=False)
        
        return True
    except Exception as e:
        # Consider logging this error instead of raising generic Exception
        # For now, re-raise with a message
        raise Exception(f"保存在线模型配置错误: {e}")


def get_openai_model_info() -> list[dict]:
    """
    获取所有已配置的在线模型及其API密钥和URL（从openai.json文件）。

    :return: list[dict], 模型信息列表, 每个字典包含 'model', 'base_url', 'api_key'.
    :raises Exception: 如果获取信息时发生错误.
    """
    try:
        model_info_list = []
        try:
            with open(OPENAI_JSON_PATH, "r", encoding="utf-8") as f:
                openai_models_config = json.load(f).get("models", [])
        except FileNotFoundError:
            openai_models_config = []
            print(
                f"警告: 在线模型配置文件 '{OPENAI_JSON_PATH}' 未找到。无模型加载。"
            )
        except json.JSONDecodeError:
            openai_models_config = []
            print(
                f"警告: 在线模型配置文件 '{OPENAI_JSON_PATH}' 格式错误。无模型加载。"
            )


        for model_conf in openai_models_config:
            model_name = model_conf.get("model")
            if not model_name:
                continue

            model_info = {
                "model": model_name,
                "base_url": model_conf.get("base_url", ""),
                "api_key": model_conf.get("api_key", ""), # Get API key from JSON
            }
            model_info_list.append(model_info)

        return model_info_list
    except Exception as e:
        raise Exception(f"获取在线模型信息错误: {e}")
