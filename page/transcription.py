import re
import streamlit as st
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from scripts.modelscope_scripts import (
    run_modelscope_recognition,
    organize_recognition_results,
    save_transcription_results,
    display_modelscope_model_selector,  # Renamed and behavior changed
)
from scripts.utils import setup_logger, copy_text_to_clipboard

logger = setup_logger("TranscriptionPage")
CACHE_DIR = "cache"  # Define cache directory

# Initialize session state keys
SESSION_STATE_KEYS_TRANSCRIPTION = {
    "transcription_audio_filename": None,
    "transcription_full_text": "",
    "transcription_speaker_text": "",
}
for key, default_value in SESSION_STATE_KEYS_TRANSCRIPTION.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


def cleanup_transcription_state():
    """清空转录页面的会话状态（除文件名外）。"""
    for key in SESSION_STATE_KEYS_TRANSCRIPTION:
        if key != "transcription_audio_filename":
            st.session_state[key] = SESSION_STATE_KEYS_TRANSCRIPTION[key]


@st.dialog("聊天模式预览")  # Use experimental_dialog for Streamlit < 1.30
def display_chat_preview(speaker_separated_text: str):
    """
    以聊天消息的形式显示区分说话人的文本。

    :param speaker_separated_text: str, 包含说话人标记的文本。
    """
    st.markdown("#### 对话预览")
    if not speaker_separated_text.strip():
        st.info("无内容可预览。")
        return

    # Regex to capture "说话人X: " and the subsequent text until the next speaker or end of string
    # Using re.DOTALL to make '.' match newlines as well
    segments = re.findall(
        r"(说话人\d+):\s*(.*?)(?=\n\n说话人\d+:|$)", speaker_separated_text, re.DOTALL
    )

    if not segments:  # Fallback if regex doesn't match expected format well
        st.warning("无法按聊天格式解析文本，将显示原始分段文本。")
        st.text(speaker_separated_text)
        return

    for i, segment_match in enumerate(segments):
        speaker_tag = segment_match[0]  # e.g., "说话人1"
        content = segment_match[1].strip()

        # Use a simple alternating avatar or derive from speaker_tag if desired
        avatar_icon = (
            "🧑‍💻" if (int(speaker_tag.replace("说话人", "")) % 2 == 0) else "👤"
        )

        with st.chat_message(name=speaker_tag, avatar=avatar_icon):
            st.markdown(
                content
            )  # Use markdown for better text rendering (e.g., newlines)


st.header("🎤 音频转录 (ModelScope)")
st.caption("使用ModelScope模型将音频文件转换为文本。")

# Sidebar for model selection
with st.sidebar:
    st.title("⚙️ 模型配置")
    st.info("建议使用默认模型组合。更改模型可能导致预料之外的行为或错误。")
    with st.expander("选择转录模型", expanded=True):
        # This function now directly returns the selected model_id and revision_str
        (model_id, model_rev, vad_id, vad_rev, punc_id, punc_rev, spk_id, spk_rev) = (
            display_modelscope_model_selector()
        )

# Main area for file upload and results
uploaded_audio_file = st.file_uploader(
    "选择或拖放音频文件 (WAV, MP3, FLAC, M4A)",
    type=["wav", "mp3", "flac", "m4a"],
    key="transcription_audio_uploader",
)

if uploaded_audio_file:
    # If a new file is uploaded, clear previous results
    if st.session_state.get("transcription_audio_filename") != uploaded_audio_file.name:
        cleanup_transcription_state()
        st.session_state["transcription_audio_filename"] = uploaded_audio_file.name
        logger.info(f"New audio file for transcription: {uploaded_audio_file.name}")

    st.subheader("🔊 音频预览")
    st.audio(uploaded_audio_file, format=uploaded_audio_file.type)

    if st.button("▶️ 开始识别", type="primary", use_container_width=True):
        if not model_id:  # Check if model selection from sidebar was successful
            st.error("主转录模型未选择或加载失败。请检查侧边栏配置。")
        else:
            cleanup_transcription_state()  # Clear previous results for this file
            st.session_state["transcription_audio_filename"] = (
                uploaded_audio_file.name
            )  # Keep filename

            # Ensure cache directory exists
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR)

            audio_file_path = os.path.join(CACHE_DIR, uploaded_audio_file.name)
            with open(audio_file_path, "wb") as f:
                f.write(uploaded_audio_file.getbuffer())

            with st.spinner("识别中，请耐心等待..."):
                try:
                    raw_result = run_modelscope_recognition(
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
                        st.session_state.transcription_full_text,
                        st.session_state.transcription_speaker_text,
                    ) = organize_recognition_results(raw_result)

                    if (
                        not st.session_state.transcription_full_text
                        and not st.session_state.transcription_speaker_text
                    ):
                        st.warning("识别结果为空。请检查音频文件或模型配置。")
                    else:
                        st.success("音频识别完成！")
                        # Save results automatically
                        filename_base = os.path.splitext(uploaded_audio_file.name)[0]
                        if save_transcription_results(
                            st.session_state.transcription_full_text,
                            st.session_state.transcription_speaker_text,
                            filename_base,
                            mode="normal",  # 'normal' for transcription page context
                        ):
                            st.toast(f"结果已保存到 '{filename_base}' 文件夹。")
                        else:
                            st.error("保存识别结果失败。")

                except Exception as e:
                    logger.error(f"Transcription process error: {e}", exc_info=True)
                    st.error(f"识别过程中发生严重错误: {e}")
                finally:
                    # Clean up cached audio file
                    if os.path.exists(audio_file_path):
                        try:
                            os.remove(audio_file_path)
                            logger.info(f"Cached audio file removed: {audio_file_path}")
                        except OSError as e:
                            logger.error(
                                f"Error removing cached file {audio_file_path}: {e}"
                            )
            st.rerun()  # Rerun to display new results from session state

# Display results if available in session state
if st.session_state.get("transcription_full_text") or st.session_state.get(
    "transcription_speaker_text"
):
    st.markdown("---")
    st.subheader("📋 识别结果")

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📄 完整识别结果 (无说话人区分)", expanded=True):
            if st.session_state.transcription_full_text:
                st.text_area(
                    "全文:",
                    st.session_state.transcription_full_text,
                    height=300,
                    disabled=True,
                    key="full_text_display",
                )
                st.button(
                    "复制全文",
                    on_click=copy_text_to_clipboard,
                    args=(st.session_state.transcription_full_text,),
                    key="copy_full_text",
                )
            else:
                st.info("无完整识别结果。")

    with col2:
        with st.expander("🗣️ 带说话人识别结果", expanded=True):
            if st.session_state.transcription_speaker_text:
                st.text_area(
                    "分段文本:",
                    st.session_state.transcription_speaker_text,
                    height=300,
                    disabled=True,
                    key="speaker_text_display",
                )

                button_col_copy, button_col_chat = st.columns(2)
                with button_col_copy:
                    st.button(
                        "复制分段文本",
                        on_click=copy_text_to_clipboard,
                        args=(st.session_state.transcription_speaker_text,),
                        key="copy_speaker_text",
                        use_container_width=True,
                    )
                with button_col_chat:
                    if st.button(
                        "💬 聊天模式预览",
                        key="chat_mode_button",
                        use_container_width=True,
                    ):
                        display_chat_preview(
                            st.session_state.transcription_speaker_text
                        )
            else:
                st.info("无说话人识别结果 (可能模型不支持或未启用)。")
