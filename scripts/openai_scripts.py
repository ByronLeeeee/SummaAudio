from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os
import sys
import json
import configparser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def set_openai_client(model_name):
    load_dotenv()

    with open("config/openai.json", "r") as f:
        openai_settings = json.load(f)

    model_config = next(
        (model for model in openai_settings["models"] if model["model"] == model_name),
        None,
    )
    api_key = os.getenv(model_config["api_key"])

    client = OpenAI(base_url=model_config["base_url"], api_key=api_key)
    return client


def get_model_list():
    with open("config/openai.json", "r") as f:
        openai_settings = json.load(f)

    models = [model["model"] for model in openai_settings["models"]]
    return models


def generate(prompt: str, model_name: str):
    client = set_openai_client(model_name)
    config = configparser.ConfigParser()
    config.read("config/config.ini",encoding="utf-8")

    options_settings = config["OPENAI"]
    response = client.completions.create(
        model=model_name,
        prompt=prompt,
        temperature=options_settings["temperature"],
        max_tokens=options_settings["max_tokens"],
        top_p=options_settings["top_p"],
        stream=True,
    )
    for part in response:
        yield part["response"]


def update_model_info(model_info: list):
    try:
        load_dotenv()
        with open("config/openai.json", "r") as f:
            openai_settings = json.load(f)
        new_model_info_list = []
        for model in model_info:
            update_model = {
                "model": model.get("model"),
                "base_url": model.get("base_url"),
            }
            new_model_info_list.append(update_model)

        openai_settings["models"] = new_model_info_list

        with open("config/openai.json", "w") as f:
            json.dump(openai_settings, f, indent=4)

        env_path = find_dotenv()
        open(env_path, "w").close()
        # 重新写入 API 密钥
        with open(env_path, "w") as env_file:
            for model_data in model_info:
                model = model_data.get("model", "")
                api_key = model_data.get("api_key", "")
                if model and api_key:
                    env_file.write(
                        f"{model.upper().replace('-', '_')}_API_KEY={api_key}\n"
                    )

            # 重新加载环境变量
            load_dotenv(env_path, override=True)
        return True
    except Exception as e:
        raise f"保存错误: {e}"

def get_model_info():
    try:
        model_info_list = []
        load_dotenv()        
        with open("config/openai.json", "r") as f:
            openai_models = json.load(f)["models"]

        for model in openai_models:
            model_info = {
                "model": model["model"],
                "base_url": model["base_url"],
                "api_key": os.getenv(f'''{model["model"].upper().replace('-', '_')}_API_KEY'''),
            }
            model_info_list.append(model_info)
        
        return model_info_list
    except Exception as e:
        raise f"获取错误: {e}"