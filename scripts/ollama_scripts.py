from ollama import Client
import configparser
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_config():
    config = configparser.ConfigParser()
    config.read("config/config.ini", encoding="utf-8")
    return config["OLLAMA"]


def get_model_list():
    config = get_config()
    base = config["base_url"]
    client = Client(host=base)
    model_list = client.list()
    models = [model["name"] for model in model_list["models"]]
    return models


def grenerate(prompt: str):
    try:
        config = get_config()
        base = config["base_url"]
        model = config["model"]
        max_tokens = int(config["max_tokens"])
        temperature = float(config["temperature"])
        top_p = float(config["top_p"])
        client = Client(host=base)
        llm_response = client.generate(model=model, prompt=prompt, options={
                                       "temperature": temperature, "num_ctx": max_tokens, "top_p": top_p}, stream=True)
        for part in llm_response:
            yield part['response']
    except Exception as e:
        yield str(f"遇到错误:{e}")
