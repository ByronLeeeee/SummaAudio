import time
import json
import configparser
import streamlit as st
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from scripts import ollama_scripts, openai_scripts  # ModelScope settings are simpler
from scripts.utils import CONFIG_INI_PATH, setup_logger

logger = setup_logger("SettingsPage")

# Load existing configuration
config = configparser.ConfigParser()
config.read(CONFIG_INI_PATH, encoding="utf-8")


# Helper function to save config
def save_configuration(show_success_toast=True):
    """将当前配置对象保存到INI文件。"""
    try:
        with open(CONFIG_INI_PATH, "w", encoding="utf-8") as configfile:
            config.write(configfile)
        if show_success_toast:
            st.toast("配置保存成功！", icon="✅")
        logger.info("Configuration saved successfully.")
        return True
    except Exception as e:
        st.error(f"保存配置失败: {e}", icon="❌")
        logger.error(f"Failed to save configuration: {e}")
        return False


st.header("⚙️ 应用设置")
st.caption("在此页面配置应用的核心参数和模型连接信息。")

tab_system, tab_modelscope, tab_ollama, tab_openai = st.tabs(
    ["🖥️ 系统设置", "🗣️ ModelScope", "🦙 Ollama", "🧠 OpenAI"]
)

with tab_system:
    st.subheader("LLM 后端选择")
    current_llm_mode = config.get("SYSTEM", "llm_mode", fallback="Ollama")
    llm_mode_options = ["Ollama", "OpenAI"]
    selected_llm_mode = st.radio(
        "选择默认的LLM服务:",
        llm_mode_options,
        index=(
            llm_mode_options.index(current_llm_mode)
            if current_llm_mode in llm_mode_options
            else 0
        ),
        horizontal=True,
        help="选择用于文本修正和归纳任务的大语言模型后端。",
    )
    if st.button("保存系统设置", key="save_system_settings", type="primary"):
        if "SYSTEM" not in config:
            config.add_section("SYSTEM")
        config["SYSTEM"]["llm_mode"] = selected_llm_mode
        save_configuration()

with tab_modelscope:
    st.subheader("ModelScope (语音识别) 设置")
    if "MODELSCOPE" not in config:
        config.add_section("MODELSCOPE")

    modelscope_cache_path = st.text_input(
        "模型缓存路径:",
        config.get(
            "MODELSCOPE",
            "MODELSCOPE_CACHE",
            fallback=os.path.join(os.getcwd(), "modelscope_cache"),
        ),  # Sensible default
        help="ModelScope下载和加载模型的本地缓存目录。",
    )
    output_dir_path = st.text_input(
        "转录结果输出路径:",
        config.get(
            "MODELSCOPE",
            "output_dir",
            fallback=os.path.join(os.getcwd(), "transcription_results"),
        ),  # Sensible default
        help="保存音频转录结果的根目录。",
    )

    if st.button("保存ModelScope配置", key="save_modelscope_settings", type="primary"):
        config["MODELSCOPE"]["MODELSCOPE_CACHE"] = modelscope_cache_path
        config["MODELSCOPE"]["output_dir"] = output_dir_path
        if save_configuration():
            # Create directories if they don't exist after saving config
            if not os.path.exists(modelscope_cache_path):
                os.makedirs(modelscope_cache_path, exist_ok=True)
            if not os.path.exists(output_dir_path):
                os.makedirs(output_dir_path, exist_ok=True)


with tab_ollama:
    st.subheader("Ollama 设置")
    if "OLLAMA" not in config:
        config.add_section("OLLAMA")

    ollama_base_url = st.text_input(
        "Ollama API 地址 (Base URL):",
        config.get("OLLAMA", "base_url", fallback="http://localhost:11434"),
        help="例如: http://localhost:11434",
    )

    # Fetch model list if base_url is set, otherwise provide manual input
    ollama_model_list = []
    if ollama_base_url:
        try:
            # Temporarily set base_url in config for get_ollama_model_list to work during setup
            temp_config = configparser.ConfigParser()
            temp_config.read_dict(config)  # Copy current config
            if "OLLAMA" not in temp_config:
                temp_config.add_section("OLLAMA")
            temp_config["OLLAMA"]["base_url"] = ollama_base_url
            # Save temp config to a temp file to be read by ollama_scripts if it strictly reads from file
            # Or, ideally, ollama_scripts.get_ollama_config_values could take base_url as an arg
            # For now, assume ollama_scripts uses the global config file.
            # This part is tricky if get_ollama_model_list relies on the saved config.
            # A better approach might be to pass base_url to get_ollama_model_list.
            # For this iteration, we'll fetch after saving or rely on pre-existing config.
            ollama_model_list = (
                ollama_scripts.get_ollama_model_list()
            )  # This will use current saved config
        except Exception as e:
            st.warning(
                f"无法从 {ollama_base_url} 获取Ollama模型列表: {e}. 请确保Ollama服务正在运行且地址正确。"
            )

    current_ollama_model = config.get("OLLAMA", "model", fallback="")
    if ollama_model_list:
        selected_ollama_model = st.selectbox(
            "选择Ollama模型:",
            ollama_model_list,
            index=(
                ollama_model_list.index(current_ollama_model)
                if current_ollama_model in ollama_model_list
                else 0
            ),
            help="从Ollama服务获取的可用模型列表。",
        )
    else:
        selected_ollama_model = st.text_input(
            "手动输入Ollama模型名称:",
            current_ollama_model,
            help="如果无法自动获取列表，请手动输入模型名称 (例如: llama2:latest)。",
        )

    ollama_max_tokens_ctx = st.number_input(  # num_ctx for Ollama
        "Ollama 上下文窗口大小 (num_ctx):",
        min_value=512,
        max_value=32768,
        value=int(
            config.get("OLLAMA", "max_tokens", fallback="4096")
        ),  # Renamed in UI from "Tokens上限"
        step=256,
        help="模型处理的最大上下文长度（输入+输出）。",
    )
    ollama_temperature = st.slider(
        "Ollama Temperature:",
        0.0,
        2.0,
        float(config.get("OLLAMA", "temperature", fallback="0.7")),
        step=0.05,
        help="控制生成文本的随机性。较低值更保守，较高值更具创造性。",
    )
    ollama_top_p = st.slider(
        "Ollama Top_p:",
        0.0,
        1.0,
        float(config.get("OLLAMA", "top_p", fallback="1.0")),
        step=0.05,
        help="核心采样参数。模型会考虑累积概率达到top_p的最高概率词汇。",
    )

    if st.button("保存Ollama配置", key="save_ollama_settings", type="primary"):
        if not ollama_base_url.strip():
            st.error("Ollama API 地址不能为空。")
            st.stop()
        if not selected_ollama_model.strip():
            st.error("Ollama 模型名称不能为空。")
            st.stop()

        config["OLLAMA"]["base_url"] = ollama_base_url
        config["OLLAMA"]["model"] = selected_ollama_model
        config["OLLAMA"]["max_tokens"] = str(ollama_max_tokens_ctx)
        config["OLLAMA"]["temperature"] = str(ollama_temperature)
        config["OLLAMA"]["top_p"] = str(ollama_top_p)
        save_configuration()
        st.rerun()  # Rerun to refresh model list if it depends on saved config

with tab_openai:  # Corrected to use the defined tab variable
    st.subheader("OpenAI 设置")
    st.caption(
        "同样支持OpenAI兼容模型，请准确填写base_url/api_key和模型名字（model_name）（例如：deepseek-chat）。"
    )
    if "OPENAI" not in config:
        config.add_section("OPENAI")

    # Dialog for managing OpenAI models (base_url, api_key per model)
    @st.dialog("OpenAI 模型配置管理")
    def manage_openai_models_dialog():
        st.markdown(
            """
        在这里管理您的OpenAI兼容模型的配置。每个模型可以有其独立的API地址和API密钥。
        API密钥将存储在项目根目录下的 `.env` 文件中。
        模型名称和API地址将存储在 `config/openai.json` 文件中。
        **注意**：API密钥在编辑时将以明文显示。
        """
        )

        # Fetch current models from openai_scripts.py
        current_openai_models = openai_scripts.get_openai_model_info()

        edited_models = st.data_editor(
            current_openai_models,
            num_rows="dynamic",
            use_container_width=True,
            key="openai_model_editor",
            column_config={
                "model": st.column_config.TextColumn(
                    "模型名称 (例如 gpt-4o)", required=True
                ),
                "base_url": st.column_config.TextColumn(
                    "API 地址 (Base URL)", required=True
                ),
                "api_key": st.column_config.TextColumn(  # Corrected this line
                    "API 密钥 (可选, 若模型需要)",
                    help="API密钥在编辑时将以明文显示。它会安全地存储在.env文件中。",  # Added help text
                    required=False,
                ),
            },
            height=300,
        )

        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button(
                "✅ 保存模型配置",
                type="primary",
                use_container_width=True,
                key="save_openai_dialog",
            ):
                try:
                    is_valid = True
                    for item in edited_models:
                        if (
                            not item.get("model", "").strip()
                            or not item.get("base_url", "").strip()
                        ):
                            st.error("模型名称和API地址不能为空。请填写所有必填项。")
                            is_valid = False
                            break

                    if is_valid:
                        if openai_scripts.update_openai_model_info(edited_models):
                            st.session_state.dialog_open = False  # Close dialog
                            st.toast("OpenAI 模型配置已保存！", icon="✅")
                            # No automatic rerun here, let the main page flow continue.
                            # If a rerun is needed to update the selectbox, it will happen
                            # when the user interacts with the main page again or if we force it.
                            # For now, let's see if the selectbox updates naturally or if we need to force it.
                            # A targeted rerun after closing is better.
                            st.rerun()  # Rerun to refresh the selectbox on the main settings page
                        else:
                            st.error("保存OpenAI模型配置失败。")
                except Exception as e:
                    st.error(f"保存时发生错误: {e}")

        with col_cancel:
            if st.button(
                "❌ 取消", use_container_width=True, key="cancel_openai_dialog"
            ):
                st.session_state.dialog_open = False  # Close dialog
                st.rerun()  # Rerun to clear the dialog from the screen

    if st.button(
        "🛠️ 管理OpenAI模型列表",
        help="添加、编辑或删除OpenAI兼容模型的配置 (API Key, Base URL)。",
    ):
        st.session_state.dialog_open = True

    if st.session_state.get("dialog_open", False):
        manage_openai_models_dialog()

    # Selector for the default OpenAI model to use
    openai_model_names_list = openai_scripts.get_openai_model_names()
    current_default_openai_model = config.get("OPENAI", "model", fallback="")

    if openai_model_names_list:
        selected_default_openai_model = st.selectbox(
            "选择默认OpenAI模型:",
            openai_model_names_list,
            index=(
                openai_model_names_list.index(current_default_openai_model)
                if current_default_openai_model in openai_model_names_list
                else 0
            ),
            help="选择一个在上面“模型管理”中配置好的模型作为默认使用。",
            key="openai_default_model_selector",
        )
    elif current_default_openai_model:
        selected_default_openai_model = st.text_input(
            "当前默认OpenAI模型 (列表为空):",
            current_default_openai_model,
            disabled=True,
        )
        st.warning("OpenAI模型列表为空。请通过“管理OpenAI模型列表”添加模型配置。")
    else:
        selected_default_openai_model = (
            ""  # Placeholder if no models and no current default
        )
        st.warning("没有可用的OpenAI模型。请通过“管理OpenAI模型列表”添加和配置模型。")

    openai_max_tokens = st.number_input(
        "OpenAI Tokens上限 (max_tokens):",
        min_value=50,
        max_value=32000,  # Adjusted range
        value=int(config.get("OPENAI", "max_tokens", fallback="2048")),
        step=10,
        help="模型单次调用可生成的最大Token数量。",
        key="openai_max_tokens_input",
    )
    openai_temperature = st.slider(
        "OpenAI Temperature:",
        0.0,
        2.0,
        float(config.get("OPENAI", "temperature", fallback="0.7")),
        step=0.05,
        key="openai_temp_slider",
    )
    openai_top_p = st.slider(
        "OpenAI Top_p:",
        0.0,
        1.0,
        float(config.get("OPENAI", "top_p", fallback="1.0")),
        step=0.05,
        key="openai_top_p_slider",
    )

    if st.button("保存OpenAI默认配置", key="save_openai_settings", type="primary"):
        if (
            not selected_default_openai_model and openai_model_names_list
        ):  # If list not empty, selection must be made
            st.error("请选择一个默认的OpenAI模型。")
        elif not openai_model_names_list and not selected_default_openai_model:
            st.warning("没有配置任何OpenAI模型，无法保存默认设置。请先管理模型列表。")
        else:
            config["OPENAI"]["model"] = selected_default_openai_model
            config["OPENAI"]["max_tokens"] = str(openai_max_tokens)
            config["OPENAI"]["temperature"] = str(openai_temperature)
            config["OPENAI"]["top_p"] = str(openai_top_p)
            if save_configuration():  # save_configuration already shows toast
                pass  # Potentially st.rerun() if other parts of the page need immediate update from this save.
