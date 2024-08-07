import streamlit as st
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.modelscope_scripts import *
from scripts.utils import load_config
import re


@st.dialog("聊天模式")
def create_chat_messages(text):
    # 分割文本为单独的对话部分
    parts = re.split(r'(说话人\d+:\s*)', text)
    
    for i in range(1, len(parts), 2):
        speaker = parts[i].strip()[:-1]  # 移除冒号
        content = parts[i+1].strip()
        
        # 动态创建 st.chat_message
        with st.chat_message(speaker):
            st.write(content)


def get_modelscope_config():
    return load_config("MODELSCOPE")


def get_modelscope_model_list():
    with open("config/modelscope_models.json", "r") as f:
        model_info = json.load(f)
        model_list = model_info["models"]
        vad_model_list = model_info["vad_models"]
        punc_model_list = model_info["punc_models"]
    return model_list,vad_model_list,punc_model_list


st.subheader("音频转录")
st.sidebar.write("如不确定，请不要随便修改")
model_sidebar = st.sidebar.popover("模型选择")
with model_sidebar:
    model_selector = st.selectbox("选择模型", [model["model"]  for model in get_modelscope_model_list()[0]])
    model_revision = st.write(f"{next(model for model in get_modelscope_model_list()[0] if model['model'] == model_selector)['revision']}")
    vad_model_selector = st.selectbox("选择VAD模型", [model["model"]  for model in get_modelscope_model_list()[1]])
    vad_model_revision = st.write(f"{next(model for model in get_modelscope_model_list()[1] if model['model'] == vad_model_selector)['revision']}")
    punc_model_selector = st.selectbox("选择PUNC模型", [model["model"]  for model in get_modelscope_model_list()[2]])
    punc_model_revision = st.write(f"{next(model for model in get_modelscope_model_list()[2] if model['model'] == punc_model_selector)['revision']}")

audio_file = st.file_uploader("选择音频文件", type=["wav","mp3","flac","m4a"])
# audio_path_input = st.text_input("或输入音频路径（两者都输入时，选择文件优先）",placeholder="如没有安装ffmpeg，则仅支持wav格式音频文件")

if audio_file:
    st.write("音频预览")
    st.audio(audio_file)
    if st.button("开始识别"):
        with open(f'cache/{audio_file.name}', 'wb') as f:
            f.write(audio_file.getbuffer())
            audio_file_path = f'cache/{audio_file.name}'
        with st.spinner("识别中..."):
            result = recognition(audio_in=audio_file_path, model=model_selector, model_revision=model_revision, vad_model=vad_model_selector, vad_model_revision=vad_model_revision, punc_model=punc_model_selector, punc_model_revision=punc_model_revision)
            full_text,spk_text = organise_recognition(result)
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("完整识别结果"):
                    st.write(full_text)
            with col2:
                with st.expander("带说话人识别结果"):
                    st.write(spk_text)
                with st.expander("聊天模式识别结果"):
                    create_chat_messages(spk_text)
            os.remove(audio_file_path)

