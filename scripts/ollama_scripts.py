import ollama
import configparser


def get_config():
    config = configparser.ConfigParser()
    config.read("config/config.ini",encoding="utf-8")
    return config["OLLAMA"]


def get_model_list():
    model_list = ollama.list()
    models = [model["name"] for model in model_list["models"]]
    return models



def generate(prompt:str):
    try:
        config = get_config()
        base = config["ollama_base"]
        model = config["model"]
        max_tokens = int(config["max_tokens"])
        temperature = float(config["temperature"])
        top_p = float(config["top_p"])
        llm_response = ollama.generate(model=model, prompt=prompt,options={"temperature":temperature,"num_ctx":max_tokens,"top_p":top_p}, stream=True)
        for part in llm_response:
            yield part['response']
    except Exception as e:
        yield str(f"遇到错误:{e}")




