import sys
import os
import json
import streamlit as st

# Ensure the project root is in sys.path for consistent imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import load_config_section, setup_logger  # Corrected import
from modelscope.utils.constant import Tasks
from modelscope.pipelines import pipeline

# Setup logger for this module
logger = setup_logger("MODELSCOPE_SCRIPTS")

CONFIG_DIR = "config"
MODELSCOPE_MODELS_JSON_FILE = "modelscope_models.json"
MODELSCOPE_MODELS_JSON_PATH = os.path.join(CONFIG_DIR, MODELSCOPE_MODELS_JSON_FILE)


def get_modelscope_setting(setting_key: str) -> str:
    """
    从配置中获取ModelScope的特定设置项。

    :param setting_key: str, 配置项的键名.
    :return: str, 配置项的值.
    """
    return load_config_section("MODELSCOPE")[setting_key]


def run_modelscope_recognition(
    audio_input_path: str,
    model_id: str,
    model_revision: str,
    vad_model_id: str,
    vad_model_revision: str,
    punc_model_id: str,
    punc_model_revision: str,
    spk_model_id: str,
    spk_model_revision: str,
) -> list:
    """
    使用指定的ModelScope模型对音频进行识别。

    :param audio_input_path: str, 输入音频文件的路径.
    :param model_id: str, 主模型ID.
    :param model_revision: str, 主模型版本.
    :param vad_model_id: str, VAD模型ID.
    :param vad_model_revision: str, VAD模型版本.
    :param punc_model_id: str, 标点模型ID.
    :param punc_model_revision: str, 标点模型版本.
    :param spk_model_id: str, 说话人模型ID.
    :param spk_model_revision: str, 说话人模型版本.
    :return: list, 识别结果列表.
    :raises ValueError: 如果MODELSCOPE_CACHE未配置.
    """
    cache_path = get_modelscope_setting("MODELSCOPE_CACHE")
    if not cache_path:
        raise ValueError("MODELSCOPE_CACHE is not configured in config.ini.")
    os.environ["MODELSCOPE_CACHE"] = cache_path  # Set cache path for ModelScope

    try:
        inference_pipeline = pipeline(
            task=Tasks.auto_speech_recognition,
            model=model_id,
            model_revision=model_revision,
            vad_model=vad_model_id,
            vad_model_revision=vad_model_revision,
            punc_model=punc_model_id,
            punc_model_revision=punc_model_revision,
            spk_model=spk_model_id,
            spk_model_revision=spk_model_revision,
        )
        rec_result = inference_pipeline(audio_input_path)
        return rec_result if rec_result else []

    except Exception as e:
        logger.error(f"ModelScope recognition error: {e}")
        st.error(f"语音识别时发生错误: {e}")  # Show error in UI as well
        return []


def organize_recognition_results(recognition_output: list) -> tuple[str, str]:
    """
    根据语音识别结果组织文本和说话人信息。

    :param recognition_output: list, ModelScope ASR管道的输出.
    :return: tuple[str, str], (完整文本, 按说话人组织的文本).
    :raises ValueError: 如果输入格式不正确.
    """
    if (
        not recognition_output
        or not isinstance(recognition_output, list)
        or not isinstance(recognition_output[0], dict)
    ):
        # logger.warning("Invalid input format for organize_recognition_results or empty result.")
        return "", ""  # Return empty strings for invalid/empty input

    result_info = recognition_output[0]
    full_text = result_info.get("text", "")
    sentence_details = result_info.get("sentence_info", [])

    organized_text_parts = []
    if sentence_details and isinstance(sentence_details, list):
        current_speaker = None
        current_speaker_text = ""

        for segment in sentence_details:
            speaker_id = segment.get("spk")  # Speaker ID is often an int
            text_segment = segment.get("text", "")

            if current_speaker is None or speaker_id != current_speaker:
                if (
                    current_speaker is not None and current_speaker_text
                ):  # Append previous speaker's text
                    organized_text_parts.append(
                        f"说话人{current_speaker + 1}: {current_speaker_text.strip()}"
                    )
                current_speaker = speaker_id
                current_speaker_text = text_segment
            else:
                current_speaker_text += (
                    " " + text_segment
                )  # Add space between segments from same speaker

        if (
            current_speaker is not None and current_speaker_text
        ):  # Append last speaker's text
            organized_text_parts.append(
                f"说话人{current_speaker + 1}: {current_speaker_text.strip()}"
            )

    return full_text, "\n\n".join(organized_text_parts)


def save_transcription_results(
    full_text: str, organized_text: str, output_filename_base: str, mode: str = "normal"
) -> bool:
    """
    保存转录结果到文件。

    :param full_text: str, 识别出的完整文本.
    :param organized_text: str, 按说话人组织的文本.
    :param output_filename_base: str, 输出文件名的基础部分 (不含扩展名).
    :param mode: str, 模式 ('normal' 或 'summary').
    :return: bool, 保存是否成功.
    """
    try:
        output_base_dir = get_modelscope_setting("output_dir")

        if (
            not output_filename_base
            or "/" in output_filename_base
            or "\\" in output_filename_base
        ):
            logger.error(f"Invalid output_filename_base: {output_filename_base}")
            return False

        # Create a subdirectory for this specific audio's results
        specific_output_dir = os.path.join(output_base_dir, output_filename_base)
        os.makedirs(specific_output_dir, exist_ok=True)

        txt_suffix = "分说话人" if mode == "normal" else "归纳"

        files_to_save = {
            os.path.join(specific_output_dir, "全文.txt"): full_text,
            os.path.join(specific_output_dir, f"{txt_suffix}.txt"): organized_text,
        }

        for file_path, content in files_to_save.items():
            if content:  # Only save if content is not empty
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
        logger.info(f"Results saved to directory: {specific_output_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to save output result: {e}")
        st.error(f"保存结果失败: {e}")
        return False


def get_modelscope_model_lists() -> tuple[list, list, list, list]:
    """
    从JSON配置文件加载ModelScope模型列表。

    :return: tuple, 包含各类模型列表 (主模型, VAD模型, 标点模型, 说话人模型).
    """
    try:
        with open(MODELSCOPE_MODELS_JSON_PATH, "r", encoding="utf-8") as f:
            model_info = json.load(f)
        return (
            model_info.get("models", []),
            model_info.get("vad_models", []),
            model_info.get("punc_models", []),
            model_info.get("speaker_models", []),
        )
    except FileNotFoundError:
        st.error(f"ModelScope模型配置文件未找到: {MODELSCOPE_MODELS_JSON_PATH}")
        return [], [], [], []
    except Exception as e:
        st.error(f"读取ModelScope模型列表失败: {e}")
        return [], [], [], []


def display_modelscope_model_selector():
    """
    在Streamlit界面上显示ModelScope模型选择器，并返回所选模型及其版本。

    :return: tuple, 包含所选各项模型ID和版本号的元组.
    """
    main_models, vad_models, punc_models, speaker_models = get_modelscope_model_lists()

    def get_revision(model_list, selected_model_id):
        """Helper to get revision for a selected model."""
        model_detail = next(
            (m for m in model_list if m["model"] == selected_model_id), None
        )
        return model_detail["revision"] if model_detail else "Unknown"

    st.subheader("语音识别模型")
    if not main_models:
        st.warning("未能加载语音识别主模型列表。请检查配置文件。")
        return (None,) * 8  # Return None for all if main models are missing

    selected_model_id = st.selectbox(
        "选择主模型",
        [m["model"] for m in main_models],
        help="选择用于语音转文字的核心模型。",
    )
    model_revision = get_revision(main_models, selected_model_id)
    st.caption(f"版本号: {model_revision}")

    st.subheader("语音活动检测 (VAD) 模型")
    if not vad_models:
        st.info("无VAD模型可选或未配置。")
    selected_vad_id = (
        st.selectbox(
            "选择VAD模型",
            [m["model"] for m in vad_models],
            index=0 if vad_models else None,
            help="选择用于检测语音片段的模型。",
        )
        if vad_models
        else None
    )
    vad_revision = (
        get_revision(vad_models, selected_vad_id) if selected_vad_id else "N/A"
    )
    if selected_vad_id:
        st.caption(f"VAD模型版本号: {vad_revision}")

    st.subheader("标点恢复 (PUNC) 模型")
    if not punc_models:
        st.info("无标点恢复模型可选或未配置。")
    selected_punc_id = (
        st.selectbox(
            "选择PUNC模型",
            [m["model"] for m in punc_models],
            index=0 if punc_models else None,
            help="选择用于在转录文本中添加标点的模型。",
        )
        if punc_models
        else None
    )
    punc_revision = (
        get_revision(punc_models, selected_punc_id) if selected_punc_id else "N/A"
    )
    if selected_punc_id:
        st.caption(f"PUNC模型版本号: {punc_revision}")

    st.subheader("说话人日志 (Speaker Diarization) 模型")
    if not speaker_models:
        st.info("无说话人日志模型可选或未配置。")
    selected_speaker_id = (
        st.selectbox(
            "选择说话人模型",
            [m["model"] for m in speaker_models],
            index=0 if speaker_models else None,
            help="选择用于区分不同说话人的模型。",
        )
        if speaker_models
        else None
    )
    speaker_revision = (
        get_revision(speaker_models, selected_speaker_id)
        if selected_speaker_id
        else "N/A"
    )
    if selected_speaker_id:
        st.caption(f"说话人模型版本号: {speaker_revision}")

    return (
        selected_model_id,
        model_revision,
        selected_vad_id,
        vad_revision,
        selected_punc_id,
        punc_revision,
        selected_speaker_id,
        speaker_revision,
    )
