import sys
import os
import streamlit as st

from scripts.modelscope_scripts import *
from scripts.utils import *
from scripts.openai_scripts import *
from scripts.openai_scripts import generate as openai_generate
from scripts.ollama_scripts import generate as ollama_generate
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

if 'oc_audio_name' not in st.session_state:
    st.session_state['oc_audio_name'] = ""

def cleanup():
    keys_to_clean = [
        'oc_audio_text',
        'oc_ft_in_text',
        'oc_sm_in_text',
        'oc_sm_out_text'
    ]
    
    for key in keys_to_clean:
        if key in st.session_state:
            st.session_state[key] = ""

def oc_ft(typo_prompt_lists, typo_prompt_seletor):
    original_text = st.session_state.get('oc_ft_in_text', '')
    selected_prompt_content = find_selected_prompt_content(typo_prompt_lists, typo_prompt_seletor)
    
    final_prompt = build_final_prompt(selected_prompt_content, original_text)
    
    with st.spinner('修正中...'):
        system_config = load_config("SYSTEM")
        validate_system_config(system_config)

        if system_config.get('llm_mode') == 'Ollama':
            response = st.write_stream(ollama_generate(final_prompt))
        elif system_config.get('llm_mode') == 'OpenAI':
            response = st.write_stream(openai_generate(final_prompt))
        else:
            raise ValueError("Unsupported LLM mode: " + system_config.get('llm_mode', 'Unknown'))
        
        if response != '':
            st.session_state['oc_sm_in_text'] = response
        else:
            st.error("模型返回了空白结果，请检查各个参数以及是否爆内存/显存。")
            st.session_state['oc_sm_in_text'] = ""

def oc_sm(prompt_lists, prompt_selector):
    original_text = st.session_state.oc_sm_in_text
    
    selected_prompt_content = find_selected_prompt_content(prompt_lists, prompt_selector)
    
    final_prompt = build_final_prompt(selected_prompt_content, original_text)
    
    with st.spinner('修正中...'):
        system_config = load_config("SYSTEM")
        validate_system_config(system_config)
        
        llm_mode = system_config['llm_mode']
        if system_config.get('llm_mode') == 'Ollama':
            response = st.write_stream(ollama_generate(final_prompt))
        elif system_config.get('llm_mode') == 'OpenAI':
            response = st.write_stream(openai_generate(final_prompt))
        else:
            raise ValueError("Unsupported LLM mode: " + system_config.get('llm_mode', 'Unknown'))
        
        if response != '':
            st.session_state['oc_sm_out_text'] = response
        else:
            st.error("模型返回了空白结果，请检查各个参数以及是否爆内存/显存。")
            st.session_state['oc_sm_out_text'] = ""

def find_selected_prompt_content(prompt_lists, prompt_selector):
    try:
        return next((prompt['content'] for prompt in prompt_lists if prompt['title'] == prompt_selector), None)
    except StopIteration:
        raise ValueError(f"Prompt with title '{prompt_selector}' not found.")

def build_final_prompt(selected_prompt, original_text):
    return selected_prompt + original_text

def validate_system_config(config):
    if not config or 'llm_mode' not in config:
        raise ValueError("System configuration is missing or invalid.")

def oc_audio_re():
    result = recognition(audio_in=audio_file_path, model=model_selector, model_revision=model_revision, vad_model=vad_model_selector,
                            vad_model_revision=vad_model_revision, punc_model=punc_model_selector, punc_model_revision=punc_model_revision,spk_model=speaker_model_selector,spk_model_revision=speaker_model_revision)
    try:
        full_text, organise_text = organise_recognition(result)
        if needSpk:
            oc_audio_text = organise_text
        else:
            oc_audio_text = full_text
        
        st.session_state['oc_audio_text'] = oc_audio_text
        st.session_state['oc_ft_in_text'] = oc_audio_text
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.stop()


st.subheader("一键转录")

with st.sidebar:
    st.write("配置")
    needSpk = st.checkbox("区分说话人",value=True)
    with st.expander("转录模型"):
        model_selector, model_revision, vad_model_selector, vad_model_revision, punc_model_selector, punc_model_revision, speaker_model_selector, speaker_model_revision = modolscope_model_selector()
    
    with st.expander("修正提示词"):
        typo_prompt_lists = get_prompts_details("fix_typo_prompt")
        typo_prompt_titles = [prompt['title'] for prompt in typo_prompt_lists]
        typo_prompt_seletor = st.selectbox("选择修正模板:", typo_prompt_titles)
    
    with st.expander("归纳提示词"):
        summart_mode = st.selectbox("选择总结模式", ["摘要", "会议记录"])
        if summart_mode == "摘要":
            sm_prompt_lists = get_prompts_details("summary_prompt")
            sm_prompt_titles = [prompt['title'] for prompt in sm_prompt_lists]
            sm_prompt_seletor = st.selectbox("选择摘要模板:", sm_prompt_titles)
        elif summart_mode == "会议记录":
            sm_prompt_lists = get_prompts_details("meeting_minutes_prompt")     
            sm_prompt_titles = [prompt['title'] for prompt in sm_prompt_lists]   
            sm_prompt_seletor = st.selectbox("选择会议记录模板:", sm_prompt_titles)


with st.container(border=True):
    audio_file = st.file_uploader("上传音频文件", type=["mp3", "wav", "flac","m4a"])
    if audio_file:
        if st.session_state['oc_audio_name'] != audio_file.name:
            cleanup()
            st.session_state['oc_audio_name'] = audio_file.name
        with open(f'cache/{audio_file.name}', 'wb') as f:
            f.write(audio_file.getbuffer())
            audio_file_path = f'cache/{audio_file.name}'
        st.audio(audio_file_path)

        if st.button("一键开始"):
            print("开始识别")
            oc_audio_re()
            print("开始修正")
            oc_ft(typo_prompt_lists,typo_prompt_seletor)
            print("开始归纳")
            oc_sm(sm_prompt_lists,sm_prompt_seletor)
            print("完成")
            os.remove(audio_file_path)
            st.rerun()
    
        if st.session_state.oc_audio_text != '':
            new_oc_audio_text = st.text_area("结果预览", value=st.session_state.oc_audio_text)



if st.session_state.oc_ft_in_text != "":
    with st.container(border=True):
        st.text_area("原转录文本", value=st.session_state.oc_ft_in_text)
        if st.button("用此文本再次生成",key='ft_re'):
            oc_ft(typo_prompt_lists,typo_prompt_seletor)
            oc_sm(sm_prompt_lists,sm_prompt_seletor)
            st.rerun()
        st.text_area("修正文本", value=st.session_state.oc_sm_in_text)
        
if st.session_state.oc_sm_in_text != "":
    with st.container(border=True):
        st.write("归纳")
        st.text_area("原文本", value=st.session_state.oc_sm_in_text)
        st.text_area("结果", value=st.session_state.oc_sm_out_text)
        if st.button("重试"):
            oc_sm(sm_prompt_lists,sm_prompt_seletor)
            st.rerun()
        if st.button("保存识别结果"):
            save_output_result(st.session_state.oc_sm_in_text, st.session_state.oc_sm_out_text,st.session_state['oc_audio_name'].split(".")[0])
