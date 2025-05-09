import requests  # Using requests instead of ollama library
import json
import configparser
import sys
import os
import streamlit as st  # For st.error in case of UI interaction needs

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils import CONFIG_INI_PATH  # Use defined constant

# Ollama API endpoints (confirm these with your Ollama version if issues arise)
OLLAMA_API_LIST_MODELS_ENDPOINT = "/api/tags"
OLLAMA_API_GENERATE_ENDPOINT = "/api/generate"


def get_ollama_config_values() -> tuple:
    """
    获取Ollama的配置信息。

    :return: tuple, (base_url, model_name, max_tokens/num_ctx, temperature, top_p).
    :raises ValueError: 如果Ollama配置区域或关键配置项缺失.
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_INI_PATH, encoding="utf-8")
    if "OLLAMA" not in config:
        raise ValueError(f"Section 'OLLAMA' not found in '{CONFIG_INI_PATH}'.")

    ollama_config = config["OLLAMA"]
    base_url = ollama_config.get("base_url")
    model_name = ollama_config.get("model")
    # max_tokens in config for Ollama is num_ctx (context window size)
    # num_predict (max tokens to generate) is not explicitly in current config.
    num_ctx = int(ollama_config.get("max_tokens", 4096))  # Default if not set
    temperature = float(ollama_config.get("temperature", 0.7))
    top_p = float(ollama_config.get("top_p", 1.0))

    if not base_url:
        raise ValueError("Ollama 'base_url' is not configured in config.ini.")
    if not model_name:
        raise ValueError("Ollama 'model' is not configured in config.ini.")

    return base_url, model_name, num_ctx, temperature, top_p


def get_ollama_model_list() -> list[str]:
    """
    使用requests从Ollama API获取可用的模型列表。

    :return: list[str], 模型名称列表.
    """
    try:
        base_url, _, _, _, _ = get_ollama_config_values()
    except ValueError as e:
        # st.error(f"Ollama配置错误: {e}") # Avoid st if not directly in UI flow
        print(f"Error accessing Ollama config for model list: {e}")
        return []

    try:
        response = requests.get(
            f"{base_url.rstrip('/')}{OLLAMA_API_LIST_MODELS_ENDPOINT}"
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4XX or 5XX)
        models_data = response.json()
        return [
            model["name"] for model in models_data.get("models", []) if "name" in model
        ]
    except requests.exceptions.RequestException as e:
        # st.error(f"无法连接到 Ollama ({base_url}) 或获取模型列表失败: {e}")
        print(f"Error fetching Ollama models from {base_url}: {e}")
        return []
    except json.JSONDecodeError:
        # st.error(f"从 Ollama API ({OLLAMA_API_LIST_MODELS_ENDPOINT}) 收到的模型列表JSON格式无效。")
        print(
            f"Error: Invalid JSON response from Ollama API ({OLLAMA_API_LIST_MODELS_ENDPOINT}) when fetching models."
        )
        return []


def generate_ollama_completion(prompt: str):
    """
    使用requests向Ollama API发送生成请求并处理流式响应。

    :param prompt: str, 输入给模型的提示.
    :return: 生成器, 逐块产生生成的文本.
    """
    try:
        base_url, model_name, num_ctx, temperature, top_p = get_ollama_config_values()
    except ValueError as e:
        yield f"Ollama配置错误: {e}"
        return

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_ctx": num_ctx,
            "temperature": temperature,
            "top_p": top_p,
            # "num_predict": num_predict, # If you want to control max generated tokens explicitly
        },
    }

    try:
        with requests.post(
            f"{base_url.rstrip('/')}{OLLAMA_API_GENERATE_ENDPOINT}",
            json=payload,
            stream=True,
            timeout=120,  # Added a timeout
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        decoded_line = line.decode("utf-8")
                        part = json.loads(decoded_line)
                        yield part.get("response", "")
                        if (
                            part.get("done", False)
                            and part.get("done_reason") == "stop"
                        ):  # Check for done signal
                            break
                    except json.JSONDecodeError:
                        # Log this, as it might indicate an issue or non-JSON line
                        print(
                            f"Warning: Could not decode JSON from Ollama stream: {decoded_line}"
                        )
                        continue
    except requests.exceptions.Timeout:
        yield f"Ollama请求超时 ({base_url}{OLLAMA_API_GENERATE_ENDPOINT})。"
    except requests.exceptions.RequestException as e:
        yield f"连接Ollama时发生网络错误: {e}"
    except Exception as e:  # Catch any other unexpected errors
        yield f"处理Ollama响应时发生未知错误: {e}"
