import sys
import os
import streamlit as st

from scripts.modelscope_scripts import *
from scripts.utils import *
from scripts.openai_scripts import *
from scripts.ollama_scripts import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.subheader("一键转录")

with st.sidebar:
    st.write("配置")
    with st.expander("转录模型"):
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
    
    with st.expander("修正提示词"):
        typo_prompt_lists = get_prompts_details("fix_typo_prompt")
        typo_prompt_titles = [prompt['title'] for prompt in typo_prompt_lists]
        typo_prompt_seletor = st.selectbox("选择归纳模板:", typo_prompt_titles)
    
    with st.expander("摘要/归纳提示词"):
        summart_mode = st.selectbox("选择总结模式", ["摘要", "会议记录"])
        s_prompt_lists = get_prompts_details("summary_prompt")
        m_prompt_lists = get_prompts_details("meeting_minutes_prompt")
        s_prompt_titles = [prompt['title'] for prompt in s_prompt_lists]
        m_prompt_titles = [prompt['title'] for prompt in m_prompt_lists]


        prompt_seletor = st.selectbox("选择摘要模板:", s_prompt_titles)
        prompt_seletor = st.selectbox("选择会议记录模板:", m_prompt_titles)


with st.container():
    audio_file = st.file_uploader("上传音频文件", type=["mp3", "wav", "flac"])
    if audio_file:
        with open(f'cache/{audio_file.name}', 'wb') as f:
            f.write(audio_file.getbuffer())
            audio_file_path = f'cache/{audio_file.name}'
        st.audio(audio_file_path)
    
        if st.button("一键开始"):
            pass



