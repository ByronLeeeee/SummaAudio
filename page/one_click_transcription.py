import sys
import os
import streamlit as st

# Ensure the project root is in sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from scripts.modelscope_scripts import (
    run_modelscope_recognition,
    organize_recognition_results,
    save_transcription_results,
    display_modelscope_model_selector,
)
from scripts.utils import (
    get_prompts_details,
    copy_text_to_clipboard,
    load_config_section,
    setup_logger,
    extract_and_clean_think_tags,  # MODIFIED
)
from scripts.openai_scripts import generate_openai_completion, get_openai_model_names
from scripts.ollama_scripts import generate_ollama_completion

logger = setup_logger("OneClickTranscriptionPage")
CACHE_DIR = "cache"

# Initialize session state keys
SESSION_STATE_KEYS = {
    "oc_audio_raw_text": "",
    "oc_fixed_text": "",
    "oc_summarized_text": "",
    "oc_current_audio_filename": None,
    "oc_full_transcription": "",
    "oc_speaker_transcription": "",
    "oc_fix_thoughts": "",  # MODIFIED: For fix typo thoughts
    "oc_summary_thoughts": "",  # MODIFIED: For summarization thoughts
}
for key, default_value in SESSION_STATE_KEYS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


def cleanup_session_state():
    """清空与当前处理流程相关的会话状态。"""
    logger.info("Cleaning up one-click transcription session state.")
    for key in SESSION_STATE_KEYS:
        if key != "oc_current_audio_filename":
            st.session_state[key] = SESSION_STATE_KEYS[key]


def perform_text_fix(
    input_text: str, typo_prompt_template: str
) -> tuple[str, str]:  # MODIFIED: returns tuple
    """执行文本修正，并分离思考过程。"""
    if not input_text or not typo_prompt_template:
        return input_text, ""

    final_prompt = typo_prompt_template + "\n" + input_text
    full_raw_response = ""

    system_config = load_config_section("SYSTEM")
    llm_mode = system_config.get("llm_mode", "Ollama")
    response_stream = None

    try:
        if llm_mode == "Ollama":
            response_stream = generate_ollama_completion(final_prompt)
        elif llm_mode == "OpenAI":
            openai_config = load_config_section("OPENAI")
            model_name = openai_config.get("model")
            if not model_name:
                st.error("OpenAI模型未在config.ini中配置。")
                return input_text, "OpenAI模型未配置"
            available_openai_models = (
                get_openai_model_names()
            )  # Check if needed for every call
            if model_name not in available_openai_models:
                st.warning(f"配置的OpenAI模型 '{model_name}' 可能不可用。")
            response_stream = generate_openai_completion(final_prompt, model_name)
        else:
            st.error(f"不支持的LLM模式: {llm_mode}")
            return input_text, f"不支持的LLM模式: {llm_mode}"

        for chunk in response_stream:
            full_raw_response += chunk

        cleaned_text, thoughts = extract_and_clean_think_tags(full_raw_response)
        return cleaned_text, thoughts
    except Exception as e:
        logger.error(f"Error in perform_text_fix: {e}")
        return input_text, f"文本修正时发生错误: {e}"


def perform_summarization(
    input_text: str, summary_prompt_template: str
) -> tuple[str, str]:  # MODIFIED: returns tuple
    """执行文本归纳，并分离思考过程。"""
    if not input_text or not summary_prompt_template:
        return input_text, ""

    final_prompt = summary_prompt_template + "\n" + input_text
    full_raw_response = ""

    system_config = load_config_section("SYSTEM")
    llm_mode = system_config.get("llm_mode", "Ollama")
    response_stream = None

    try:
        if llm_mode == "Ollama":
            response_stream = generate_ollama_completion(final_prompt)
        elif llm_mode == "OpenAI":
            openai_config = load_config_section("OPENAI")
            model_name = openai_config.get("model")
            if not model_name:
                st.error("OpenAI模型未在config.ini中配置。")
                return input_text, "OpenAI模型未配置"
            available_openai_models = get_openai_model_names()
            if model_name not in available_openai_models:
                st.warning(f"配置的OpenAI模型 '{model_name}' 可能不可用。")
            response_stream = generate_openai_completion(final_prompt, model_name)
        else:
            st.error(f"不支持的LLM模式: {llm_mode}")
            return input_text, f"不支持的LLM模式: {llm_mode}"

        for chunk in response_stream:
            full_raw_response += chunk

        cleaned_text, thoughts = extract_and_clean_think_tags(full_raw_response)
        return cleaned_text, thoughts
    except Exception as e:
        logger.error(f"Error in perform_summarization: {e}")
        return input_text, f"文本归纳时发生错误: {e}"


st.header("🎙️ 一键转录、修正与归纳")
st.markdown("上传音频文件，应用将自动完成语音转文字、文本校对和内容总结。")

# --- Sidebar for configurations ---
with st.sidebar:
    st.title("⚙️ 处理配置")

    st.subheader("步骤 1: 语音转录")
    distinguish_speakers = st.checkbox("区分说话人 (若模型支持)", value=True)
    with st.expander("选择转录模型 (ModelScope)", expanded=False):
        (model_id, model_rev, vad_id, vad_rev, punc_id, punc_rev, spk_id, spk_rev) = (
            display_modelscope_model_selector()
        )

    st.subheader("步骤 2: 文本修正 (可选)")
    enable_fix_typo = st.checkbox("启用文本修正", value=True)
    selected_fix_prompt_content = ""
    if enable_fix_typo:
        with st.expander("选择修正提示词", expanded=False):
            fix_prompt_list = get_prompts_details("fix_typo_prompt")
            if fix_prompt_list:
                fix_prompt_titles = [p["title"] for p in fix_prompt_list]
                selected_fix_title = st.selectbox(
                    "选择修正模板:", fix_prompt_titles, key="oc_fix_prompt_selector"
                )
                if selected_fix_title:  # Ensure a title is selected
                    selected_fix_prompt_content = next(
                        (
                            p["content"]
                            for p in fix_prompt_list
                            if p["title"] == selected_fix_title
                        ),
                        "",
                    )
            else:
                st.warning("未找到修正提示词。")

    st.subheader("步骤 3: 内容归纳 (可选)")
    enable_summarization = st.checkbox("启用内容归纳", value=True)
    selected_summary_prompt_content = ""
    if enable_summarization:
        with st.expander("选择归纳提示词", expanded=False):
            summary_mode = st.selectbox(
                "选择归纳类型:", ["摘要", "会议记录"], key="oc_summary_mode_selector"
            )
            prompt_category = (
                "summary_prompt" if summary_mode == "摘要" else "meeting_minutes_prompt"
            )

            summary_prompt_list = get_prompts_details(prompt_category)
            if summary_prompt_list:
                summary_prompt_titles = [p["title"] for p in summary_prompt_list]
                selected_summary_title = st.selectbox(
                    f"选择{summary_mode}模板:",
                    summary_prompt_titles,
                    key="oc_summary_prompt_selector",
                )
                if selected_summary_title:  # Ensure a title is selected
                    selected_summary_prompt_content = next(
                        (
                            p["content"]
                            for p in summary_prompt_list
                            if p["title"] == selected_summary_title
                        ),
                        "",
                    )
            else:
                st.warning(f"未找到{summary_mode}提示词。")

# --- Main content area ---
uploaded_audio_file = st.file_uploader(
    "上传音频文件 (MP3, WAV, FLAC, M4A)",
    type=["mp3", "wav", "flac", "m4a"],
    key="oc_audio_uploader",
)

if uploaded_audio_file:
    if st.session_state.get("oc_current_audio_filename") != uploaded_audio_file.name:
        cleanup_session_state()
        st.session_state["oc_current_audio_filename"] = uploaded_audio_file.name
        logger.info(f"New audio file uploaded: {uploaded_audio_file.name}")

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        logger.info(f"Cache directory created: {CACHE_DIR}")

    audio_file_path = os.path.join(CACHE_DIR, uploaded_audio_file.name)
    with open(audio_file_path, "wb") as f:
        f.write(uploaded_audio_file.getbuffer())

    st.audio(audio_file_path, format=uploaded_audio_file.type)

    if st.button("🚀 开始一键处理", type="primary", use_container_width=True):
        cleanup_session_state()  # Clear previous full run results
        st.session_state["oc_current_audio_filename"] = uploaded_audio_file.name

        # --- 1. Transcription ---
        with st.status("正在进行语音转录...", expanded=True) as status_transcription:
            st.write("调用ModelScope进行语音识别...")
            try:
                if not model_id:
                    st.error("主转录模型未选择或加载失败，无法进行转录。")
                    status_transcription.update(label="转录失败!", state="error")
                    st.stop()

                raw_recognition_result = run_modelscope_recognition(
                    audio_input_path=audio_file_path,
                    model_id=model_id,
                    model_revision=model_rev,
                    vad_model_id=vad_id,
                    vad_model_revision=vad_rev,
                    punc_model_id=punc_id,
                    punc_model_revision=punc_rev,
                    spk_model_id=spk_id,
                    spk_model_revision=spk_rev,
                )
                (
                    st.session_state.oc_full_transcription,
                    st.session_state.oc_speaker_transcription,
                ) = organize_recognition_results(raw_recognition_result)

                if distinguish_speakers and st.session_state.oc_speaker_transcription:
                    st.session_state.oc_audio_raw_text = (
                        st.session_state.oc_speaker_transcription
                    )
                else:
                    st.session_state.oc_audio_raw_text = (
                        st.session_state.oc_full_transcription
                    )

                if not st.session_state.oc_audio_raw_text:
                    st.warning("语音转录结果为空。")
                    status_transcription.update(
                        label="转录结果为空或失败", state="error"
                    )
                else:
                    st.text_area(
                        "原始转录文本 (预览):",
                        st.session_state.oc_audio_raw_text,
                        height=100,
                        disabled=True,
                        key="oc_raw_text_preview_in_status",
                    )
                    status_transcription.update(label="语音转录完成!", state="complete")
            except Exception as e:
                logger.error(f"Transcription error: {e}", exc_info=True)
                st.error(f"语音转录失败: {e}")
                status_transcription.update(label="转录失败!", state="error")

        # --- 2. Text Fix (if enabled and transcription successful) ---
        if enable_fix_typo and st.session_state.oc_audio_raw_text:
            with st.status("正在修正文本...", expanded=True) as status_fix:
                st.write("调用LLM进行文本修正...")
                if not selected_fix_prompt_content:
                    st.warning("未选择修正提示词，跳过文本修正。")
                    st.session_state.oc_fixed_text = st.session_state.oc_audio_raw_text
                    status_fix.update(label="修正跳过 (无提示词)", state="complete")
                else:
                    try:
                        cleaned_fixed_text, fix_thoughts = perform_text_fix(
                            st.session_state.oc_audio_raw_text,
                            selected_fix_prompt_content,
                        )
                        st.session_state.oc_fixed_text = cleaned_fixed_text
                        st.session_state.oc_fix_thoughts = fix_thoughts

                        st.text_area(
                            "修正后文本 (预览):",
                            st.session_state.oc_fixed_text,
                            height=100,
                            disabled=True,
                            key="oc_fixed_text_preview_in_status",
                        )
                        if fix_thoughts:
                            with st.expander("修正过程中的思考 🤔", expanded=False):
                                st.markdown(fix_thoughts)
                        status_fix.update(label="文本修正完成!", state="complete")
                    except Exception as e:
                        logger.error(f"Text fix error: {e}", exc_info=True)
                        st.error(f"文本修正失败: {e}")
                        st.session_state.oc_fixed_text = (
                            st.session_state.oc_audio_raw_text
                        )
                        status_fix.update(label="文本修正失败!", state="error")
        elif st.session_state.oc_audio_raw_text:
            st.session_state.oc_fixed_text = st.session_state.oc_audio_raw_text

        # --- 3. Summarization (if enabled and previous step provided text) ---
        text_for_summary = st.session_state.get(
            "oc_fixed_text", st.session_state.get("oc_audio_raw_text", "")
        )
        if enable_summarization and text_for_summary:
            with st.status("正在进行内容归纳...", expanded=True) as status_summary:
                st.write("调用LLM进行内容归纳...")
                if not selected_summary_prompt_content:
                    st.warning("未选择归纳提示词，跳过内容归纳。")
                    st.session_state.oc_summarized_text = ""
                    status_summary.update(label="归纳跳过 (无提示词)", state="complete")
                else:
                    try:
                        cleaned_summary_text, summary_thoughts = perform_summarization(
                            text_for_summary, selected_summary_prompt_content
                        )
                        st.session_state.oc_summarized_text = cleaned_summary_text
                        st.session_state.oc_summary_thoughts = summary_thoughts

                        st.text_area(
                            "归纳结果 (预览):",
                            st.session_state.oc_summarized_text,
                            height=150,
                            disabled=True,
                            key="oc_summary_text_preview_in_status",
                        )
                        if summary_thoughts:
                            with st.expander("归纳过程中的思考 🤔", expanded=False):
                                st.markdown(summary_thoughts)
                        status_summary.update(label="内容归纳完成!", state="complete")
                    except Exception as e:
                        logger.error(f"Summarization error: {e}", exc_info=True)
                        st.error(f"内容归纳失败: {e}")
                        status_summary.update(label="内容归纳失败!", state="error")

        # --- 4. Save Results ---
        if st.session_state.oc_audio_raw_text:
            filename_base = os.path.splitext(uploaded_audio_file.name)[0]

            # Determine what text to save as "organized"
            # If summarization is enabled and successful, save the summary.
            # Otherwise, save the speaker-separated text (if available and chosen) or full text.
            text_to_save_as_organized = (
                st.session_state.oc_speaker_transcription
            )  # Default to speaker text
            mode_for_saving = "分说话人"

            if enable_summarization and st.session_state.oc_summarized_text:
                text_to_save_as_organized = st.session_state.oc_summarized_text
                mode_for_saving = "归纳"
            elif (
                not distinguish_speakers
            ):  # If not distinguishing speakers, 'organized' is same as full
                text_to_save_as_organized = st.session_state.oc_full_transcription
                mode_for_saving = (
                    "全文"  # Or a more generic term if not speaker-separated
                )

            if save_transcription_results(
                full_text=st.session_state.oc_full_transcription,
                organized_text=text_to_save_as_organized,
                output_filename_base=filename_base,
                mode=mode_for_saving,
            ):
                st.success(f"处理结果已保存到 '{filename_base}' 文件夹中。")
            else:
                st.error("保存结果失败。")

        if os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                logger.info(f"Cached audio file removed: {audio_file_path}")
            except Exception as e:
                logger.error(f"Error removing cached audio file {audio_file_path}: {e}")

        st.balloons()
        st.rerun()  # Rerun to show results in the expanders below cleanly


# --- Display results from session state if they exist ---
st.markdown("---")
st.subheader("📄 处理结果预览")

if st.session_state.get("oc_audio_raw_text"):
    with st.expander("原始转录文本", expanded=False):
        st.text_area(
            "原始转录:",
            value=st.session_state.oc_audio_raw_text,
            height=200,
            disabled=True,
            key="disp_raw",
        )
        st.button(
            "复制原始转录",
            on_click=copy_text_to_clipboard,
            args=(st.session_state.oc_audio_raw_text,),
            key="copy_raw",
        )

if st.session_state.get("oc_fixed_text") and enable_fix_typo:
    with st.expander("修正后文本", expanded=True):
        st.text_area(
            "修正后:",
            value=st.session_state.oc_fixed_text,
            height=200,
            disabled=True,
            key="disp_fixed",
        )
        st.button(
            "复制修正后文本",
            on_click=copy_text_to_clipboard,
            args=(st.session_state.oc_fixed_text,),
            key="copy_fixed",
        )
        if st.session_state.get("oc_fix_thoughts"):
            with st.expander("对应思考过程 🤔", expanded=False):
                st.markdown(st.session_state.oc_fix_thoughts)
                st.button(
                    "复制修正思考过程",
                    on_click=copy_text_to_clipboard,
                    args=(st.session_state.oc_fix_thoughts,),
                    key="copy_oc_fix_thoughts",
                )


if st.session_state.get("oc_summarized_text") and enable_summarization:
    with st.expander("归纳结果", expanded=True):
        st.text_area(
            "归纳:",
            value=st.session_state.oc_summarized_text,
            height=250,
            disabled=True,
            key="disp_summary",
        )
        st.button(
            "复制归纳结果",
            on_click=copy_text_to_clipboard,
            args=(st.session_state.oc_summarized_text,),
            key="copy_summary",
        )
        if st.session_state.get("oc_summary_thoughts"):
            with st.expander("对应思考过程 🤔", expanded=False):
                st.markdown(st.session_state.oc_summary_thoughts)
                st.button(
                    "复制归纳思考过程",
                    on_click=copy_text_to_clipboard,
                    args=(st.session_state.oc_summary_thoughts,),
                    key="copy_oc_summary_thoughts",
                )
