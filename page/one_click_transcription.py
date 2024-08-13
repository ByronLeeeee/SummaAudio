import sys
import os
import streamlit as st

from scripts.modelscope_scripts import *
from scripts.utils import *
from scripts.openai_scripts import *
from scripts.openai_scripts import grenerate as openai_grenerate
from scripts.ollama_scripts import grenerate as ollama_grenerate
from scripts.ollama_scripts import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if 'oc_audio_text' not in st.session_state:
    st.session_state['oc_audio_text'] = ""

if 'oc_ft_in_text' not in st.session_state:
    st.session_state['oc_ft_in_text'] = ""

if 'oc_sm_in_text' not in st.session_state:
    st.session_state['oc_sm_in_text'] = ""

if 'oc_sm_out_text' not in st.session_state:
    st.session_state['oc_sm_out_text'] = ""


def oc_ft(typo_prompt_lists,typo_prompt_seletor):
    original_text = st.session_state.oc_ft_in_text
    with st.spinner('修正中...'):
            using_prompt = [prompt['content']
                            for prompt in typo_prompt_lists if prompt['title'] == typo_prompt_seletor][0]
            final_prompt = using_prompt + original_text
            if load_config("SYSTEM")['llm_mode'] == 'ollama':
                respone = st.write_stream(ollama_grenerate(final_prompt))
            elif load_config("SYSTEM")['llm_mode'] == 'openai':
                respone = st.write_stream(openai_grenerate(final_prompt))
            st.session_state['oc_sm_in_text'] = respone

def oc_sm(prompt_lists,prompt_seletor):
    original_text = st.session_state.oc_sm_in_text
    using_prompt = [prompt['content']
                            for prompt in prompt_lists if prompt['title'] == prompt_seletor][0]
    final_prompt = using_prompt + original_text 
    if load_config("SYSTEM")['llm_mode'] == 'ollama':
        respone = st.write_stream(ollama_grenerate(final_prompt))
    elif load_config("SYSTEM")['llm_mode'] == 'openai':
        respone = st.write_stream(openai_grenerate(final_prompt))
    st.session_state['oc_sm_out_text'] = respone

def oc_audio_re():
    result = recognition(audio_in=audio_file_path, model=model_selector, model_revision=model_revision, vad_model=vad_model_selector,
                            vad_model_revision=vad_model_revision, punc_model=punc_model_selector, punc_model_revision=punc_model_revision,spk_model=speaker_model_selector,spk_model_revision=speaker_model_revision)
    full_text, organise_text = organise_recognition(result)
    if needSpk:
        oc_audio_text = organise_text
    else:
        oc_audio_text = full_text
    
    st.session_state['oc_audio_text'] = oc_audio_text
    st.session_state['oc_ft_in_text'] = oc_audio_text


st.subheader("一键转录")

with st.sidebar:
    st.write("配置")
    needSpk = st.checkbox("区分说话人")
    with st.expander("转录模型"):
        model_selector, model_revision, vad_model_selector, vad_model_revision, punc_model_selector, punc_model_revision, speaker_model_selector, speaker_model_revision = modolscope_model_selector()
    
    with st.expander("修正提示词"):
        typo_prompt_lists = get_prompts_details("fix_typo_prompt")
        typo_prompt_titles = [prompt['title'] for prompt in typo_prompt_lists]
        typo_prompt_seletor = st.selectbox("选择归纳模板:", typo_prompt_titles)
    
    with st.expander("摘要/归纳提示词"):
        summart_mode = st.selectbox("选择总结模式", ["摘要", "会议记录"])
        if summart_mode == "摘要":
            prompt_lists = get_prompts_details("summary_prompt")
            prompt_titles = [prompt['title'] for prompt in prompt_lists]
            prompt_seletor = st.selectbox("选择摘要模板:", prompt_titles)
        elif summart_mode == "会议记录":
            prompt_lists = get_prompts_details("meeting_minutes_prompt")     
            prompt_titles = [prompt['title'] for prompt in prompt_lists]   
            prompt_seletor = st.selectbox("选择会议记录模板:", prompt_titles)


with st.container(border=True):
    audio_file = st.file_uploader("上传音频文件", type=["mp3", "wav", "flac"])
    if audio_file:
        with open(f'cache/{audio_file.name}', 'wb') as f:
            f.write(audio_file.getbuffer())
            audio_file_path = f'cache/{audio_file.name}'
        st.audio(audio_file_path)

        if st.button("一键开始"):
            oc_audio_re()
            oc_ft(typo_prompt_lists,typo_prompt_seletor)
            oc_sm(prompt_lists,prompt_seletor)
    
    if st.session_state.oc_audio_text != "":
        new_oc_audio_text = st.text_area("结果预览", value=st.session_state.oc_audio_text)
        if st.button("用此文本再次生成"):
            st.session_state.oc_audio_text = new_oc_audio_text
            st.session_state.oc_ft_in_text = new_oc_audio_text
            oc_ft(typo_prompt_lists,typo_prompt_seletor)
            oc_sm(prompt_lists,prompt_seletor)
            st.rerun()


if st.session_state.oc_ft_in_text != "":
    with st.container(border=True):
        st.text_area("原转录文本", value=st.session_state.oc_ft_in_text)
        if st.button("用此文本再次生成"):
            oc_ft(typo_prompt_lists,typo_prompt_seletor)
            oc_sm(prompt_lists,prompt_seletor)
            st.rerun()
        st.text_area("修正文本", value=st.session_state.oc_sm_in_out)
        
if st.session_state.oc_sm_text != "":
    with st.container(border=True):
        st.write("归纳")
        st.text_area("原文本", value=st.session_state.oc_sm_in_text)
        st.text_area("结果", value=st.session_state.oc_sm_out_text)
        if st.button("重试"):
            oc_sm(prompt_lists,prompt_seletor)
            st.rerun()
