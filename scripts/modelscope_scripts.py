from scripts.utils import load_config,setup_logger
from modelscope.utils.constant import Tasks
from modelscope.pipelines import pipeline
import sys
import json
import os
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = setup_logger('MODELSCOPE_SCRIPTS')

def get_MODELSCOPE_config(config):
    return load_config('MODELSCOPE')[config]


def recognition(audio_in, model, model_revision, vad_model, vad_model_revision, punc_model, punc_model_revision, spk_model, spk_model_revision) -> list:
    """
    使用指定的模型对音频进行识别，并返回识别结果。

    :param audio_in: 输入的音频数据
    :param model: 主模型名称
    :param model_revision: 主模型版本
    :param vad_model: 语音活动检测模型名称
    :param vad_model_revision: 语音活动检测模型版本
    :param punc_model: 标点符号预测模型名称
    :param punc_model_revision: 标点符号预测模型版本
    :param spk_model: 说话人识别模型名称
    :param spk_model_revision: 说话人识别模型版本
    :return: 识别结果列表
    """
    cache_path = get_MODELSCOPE_config('MODELSCOPE_CACHE')
    if not cache_path:
        raise ValueError("MODELSCOPE_CACHE is not configured.")
    os.environ["MODELSCOPE_CACHE"] = cache_path

    try:
        # 创建推理管道
        inference_pipeline = pipeline(
            task=Tasks.auto_speech_recognition,
            model=model,
            model_revision=model_revision,
            vad_model=vad_model,
            vad_model_revision=vad_model_revision,
            punc_model=punc_model,
            punc_model_revision=punc_model_revision,
            spk_model=spk_model,
            spk_model_revision=spk_model_revision,
        )

        # 执行识别
        rec_result = inference_pipeline(audio_in)

        return rec_result

    except Exception as e:
        # 异常处理
        logger.error(f"Error occurred during recognition: {e}")
        return []


def organise_recognition(result: list):
    """
    根据语音识别结果组织文本和说话人信息。

    :param result: 包含字典元素的列表，每个字典包含文本和句子详细信息。
    
    :return: 
        - full_text: 识别出的完整文本。

        - organised_text: 按照说话人组织的文本，每个说话人的文本单独显示。

    :raises ValueError: 如果输入格式不正确或列表为空或列表元素不是字典。
    """
    if not result or not isinstance(result[0], dict):
        raise ValueError(
            "Invalid input format: 'result' should be a non-empty list with dictionaries as elements.")

    result_info = result[0]
    full_text = result_info.get('text', "")
    sentence_details = result_info.get('sentence_info', "")

    organised_text = ""
    if sentence_details and isinstance(sentence_details, list):
        previous_speaker = None
        speaker_text = ""

        for segment in sentence_details:
            speaker = segment['spk']
            text = segment['text']

            if previous_speaker is None or speaker != previous_speaker:
                if previous_speaker is not None:
                    organised_text += f"说话人{previous_speaker + 1}: {speaker_text}\n\n"
                previous_speaker = speaker
                speaker_text = text
            else:
                speaker_text += text
        if previous_speaker is not None:
            organised_text += f"说话人{previous_speaker + 1}: {speaker_text}"

    return full_text, organised_text


def save_output_result(full_text: str, organise_text: str, output_file: str,mode='normal'):
    """
    保存输出结果。

    根据不同模式（normal或summary）组织文本并保存到指定目录。

    :param:
        - full_text: str, 全文内容。

        - organise_text: str, 根据模式组织后的文本内容。

        - output_file: str, 输出文件的名称。

        - mode: str, 模式，'normal' 表示分说话人模式，其他值表示归纳模式。

    :return:
        - bool
    """
    try:
        output_path = get_MODELSCOPE_config('output_dir')
        
        if not output_file or '/' in output_file or '\\' in output_file:
            raise ValueError("Invalid output_file name")

        output_dir = os.path.join(output_path, output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        txt_name = '分说话人' if mode == 'normal' else '归纳'
        file_contents = {
            "全文.txt": full_text,
            f"{txt_name}.txt": organise_text
        }

        for file_name, content in file_contents.items():
            if content != "":
                file_path = os.path.join(output_dir, file_name)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

        return True
    except Exception as e:
        logger.error(f"Failed to save output result: {e}")
        return False

def get_modelscope_model_list():
    with open("config/modelscope_models.json", "r") as f:
        model_info = json.load(f)
        model_list = model_info["models"]
        vad_model_list = model_info["vad_models"]
        punc_model_list = model_info["punc_models"]
        speaker_model_list = model_info["speaker_models"]
    return model_list, vad_model_list, punc_model_list, speaker_model_list

def modolscope_model_selector():
    audio_models = get_modelscope_model_list()
    model_selector = st.selectbox(
        "选择模型", [model["model"] for model in audio_models[0]])
    model_revision = st.write(
        f"{next(model for model in audio_models[0] if model['model'] == model_selector)['revision']}")
    vad_model_selector = st.selectbox(
        "选择VAD模型", [model["model"] for model in audio_models[1]])
    vad_model_revision = st.write(
        f"{next(model for model in audio_models[1] if model['model'] == vad_model_selector)['revision']}")
    punc_model_selector = st.selectbox(
        "选择PUNC模型", [model["model"] for model in audio_models[2]])
    punc_model_revision = st.write(
        f"{next(model for model in audio_models[2] if model['model'] == punc_model_selector)['revision']}")
    speaker_model_selector = st.selectbox(
        "选择说话人模型", [model["model"] for model in audio_models[3]])
    speaker_model_revision = st.write(
        f"{next(model for model in audio_models[3] if model['model'] == speaker_model_selector)['revision']}")
    return model_selector, model_revision, vad_model_selector, vad_model_revision, punc_model_selector, punc_model_revision, speaker_model_selector, speaker_model_revision