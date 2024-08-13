import re
from scripts.utils import load_config
from scripts.modelscope_scripts import *
from scripts.utils import *
import streamlit as st
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@st.dialog("聊天模式")
def create_chat_messages(text):
    # 分割文本为单独的对话部分
    parts = re.split(r'(说话人\d+:\s*)', text)

    for i in range(1, len(parts), 2):
        speaker = parts[i].strip()[:-1]  # 移除冒号
        content = parts[i+1].strip()

        # 动态创建 st.chat_message
        with st.chat_message("human"):
            st.write(f'{speaker}\n{content}')


def get_modelscope_config():
    return load_config("MODELSCOPE")




if 'audio_name' not in st.session_state:
    st.session_state.audio_name = ''

if 'audio_full_text' not in st.session_state:
    st.session_state.audio_name = ''

if 'audio_spk_text' not in st.session_state:
    st.session_state.audio_name = ''

st.subheader("音频转录")
st.sidebar.write("建议使用默认模型，随意搭配可能有不能预估的BUG")
model_sidebar = st.sidebar.expander("模型选择")

        
with model_sidebar:
    model_selector, model_revision, vad_model_selector, vad_model_revision, punc_model_selector, punc_model_revision, speaker_model_selector, speaker_model_revision = modolscope_model_selector()

audio_file = st.file_uploader("选择音频文件", type=["wav", "mp3", "flac", "m4a"])
# audio_path_input = st.text_input("或输入音频路径（两者都输入时，选择文件优先）",placeholder="如没有安装ffmpeg，则仅支持wav格式音频文件")

if audio_file:
    st.write("音频预览")
    st.audio(audio_file)
    if audio_file.name == st.session_state.audio_name:
        full_text = st.session_state.full_text
        spk_text = st.session_state.spk_text

    if st.button("开始识别"):
        st.session_state.audio_name = audio_file.name
        with open(f'cache/{audio_file.name}', 'wb') as f:
            f.write(audio_file.getbuffer())
            audio_file_path = f'cache/{audio_file.name}'
        with st.spinner("识别中..."):
            result = recognition(audio_in=audio_file_path, model=model_selector, model_revision=model_revision, vad_model=vad_model_selector,
                                 vad_model_revision=vad_model_revision, punc_model=punc_model_selector, punc_model_revision=punc_model_revision,spk_model=speaker_model_selector,spk_model_revision=speaker_model_revision)
            full_text, spk_text = organise_recognition(result)
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("完整识别结果"):
                    st.write(full_text)
                    st.session_state.full_text = full_text
            with col2:
                with st.expander("带说话人识别结果"):
                    st.write(spk_text)
                    st.session_state.spk_text = spk_text
                with st.expander("聊天模式识别结果"):
                    create_chat_messages(spk_text)
            save_output_result(full_text, spk_text, audio_file.name.split(".")[0])
            os.remove(audio_file_path)
