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

from scripts import ollama_scripts, openai_scripts
from scripts.utils import CONFIG_INI_PATH, setup_logger

logger = setup_logger("SettingsPage")

# Load existing configuration
config = configparser.ConfigParser()
config.read(CONFIG_INI_PATH, encoding="utf-8")


# Helper function to save config
def save_configuration(show_success_toast=True):
    """将当前配置对象保存到INI文件。"""
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(CONFIG_INI_PATH), exist_ok=True)
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

tab_system, tab_modelscope, tab_ollama, tab_online_model = st.tabs( # Renamed tab_openai
    ["🖥️ 系统设置", "🗣️ ModelScope", "🦙 Ollama", "🌐 在线模型 (OpenAI兼容)"] # Changed tab label
)

with tab_system:
    st.subheader("LLM 后端选择")
    current_llm_mode = config.get("SYSTEM", "llm_mode", fallback="Ollama")
    llm_mode_options = ["Ollama", "OpenAI"] # Keep 'OpenAI' here as internal identifier for type
    selected_llm_mode = st.radio(
        "选择默认的LLM服务:",
        llm_mode_options,
        index=(
            llm_mode_options.index(current_llm_mode)
            if current_llm_mode in llm_mode_options
            else 0
        ),
        horizontal=True,
        help="选择用于文本修正和归纳任务的大语言模型后端。选择 'OpenAI' 将使用下方“在线模型”标签页配置的默认模型。",
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
        ),
        help="ModelScope下载和加载模型的本地缓存目录。",
    )
    output_dir_path = st.text_input(
        "转录结果输出路径:",
        config.get(
            "MODELSCOPE",
            "output_dir",
            fallback=os.path.join(os.getcwd(), "transcription_results"),
        ),
        help="保存音频转录结果的根目录。",
    )

    if st.button("保存ModelScope配置", key="save_modelscope_settings", type="primary"):
        config["MODELSCOPE"]["MODELSCOPE_CACHE"] = modelscope_cache_path
        config["MODELSCOPE"]["output_dir"] = output_dir_path
        if save_configuration():
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

    ollama_model_list = []
    if ollama_base_url:
        try:
            # This part of fetching model list might need adjustment if ollama_scripts.get_ollama_config_values()
            # strictly reads from the saved file. For now, assume it can work or user saves then reloads.
            ollama_model_list = ollama_scripts.get_ollama_model_list()
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

    ollama_max_tokens_ctx = st.number_input(
        "Ollama 上下文窗口大小 (num_ctx):",
        min_value=512,
        max_value=128000, # Increased max context
        value=int(
            config.get("OLLAMA", "max_tokens", fallback="4096")
        ),
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
        if save_configuration():
            st.rerun()

with tab_online_model: # Changed variable name for the tab
    st.subheader("在线模型 (OpenAI兼容) 设置")
    st.caption(
        "管理通过OpenAI兼容API接口访问的各类在线大模型。请准确填写模型的API地址 (Base URL)、API密钥 (API Key) 和模型名称 (Model Name)。"
    )
    # The [OPENAI] section in config.ini will store default model and parameters for this type
    if "OPENAI" not in config:
        config.add_section("OPENAI")

    @st.dialog("在线模型配置管理")
    def manage_online_models_dialog(): # Renamed dialog function
        st.markdown(
            """
        在这里管理您的在线模型配置。每个模型都有其独立的API地址、API密钥和模型名称。
        这些信息将存储在 `config/openai.json` 文件中。
        **注意**：API密钥在编辑时将以明文显示。确保此配置文件的安全。
        """
        )

        current_online_models = openai_scripts.get_openai_model_info()

        edited_models = st.data_editor(
            current_online_models,
            num_rows="dynamic",
            use_container_width=True,
            key="online_model_editor", # Changed key
            column_config={
                "model": st.column_config.TextColumn(
                    "模型名称 (例如 gpt-4o, deepseek-chat)", required=True
                ),
                "base_url": st.column_config.TextColumn(
                    "API 地址 (Base URL)", required=True
                ),
                "api_key": st.column_config.TextColumn(
                    "API 密钥 (API Key)",
                    help="API密钥将存储在 config/openai.json 中。",
                    required=True, # Making API key required for most online models
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
                key="save_online_models_dialog", # Changed key
            ):
                try:
                    is_valid = True
                    for item in edited_models:
                        if (
                            not item.get("model", "").strip()
                            or not item.get("base_url", "").strip()
                            or not item.get("api_key", "").strip() # Check API key too
                        ):
                            st.error("模型名称、API地址和API密钥均不能为空。请填写所有必填项。")
                            is_valid = False
                            break
                    
                    unique_model_names = {item.get("model", "").strip() for item in edited_models}
                    if len(unique_model_names) != len(edited_models):
                        st.error("模型名称必须唯一。请检查是否有重复的模型名称。")
                        is_valid = False


                    if is_valid:
                        if openai_scripts.update_openai_model_info(edited_models):
                            st.session_state.online_model_dialog_open = False
                            st.toast("在线模型配置已保存！", icon="✅")
                            st.rerun()
                        else:
                            st.error("保存在线模型配置失败。")
                except ValueError as ve: # Catch validation errors from update_openai_model_info
                    st.error(f"配置错误: {ve}")
                except Exception as e:
                    st.error(f"保存时发生错误: {e}")

        with col_cancel:
            if st.button(
                "❌ 取消", use_container_width=True, key="cancel_online_models_dialog" # Changed key
            ):
                st.session_state.online_model_dialog_open = False
                st.rerun()

    if st.button(
        "🛠️ 管理在线模型列表",
        help="添加、编辑或删除在线模型的配置 (模型名称, API Key, Base URL)。",
    ):
        st.session_state.online_model_dialog_open = True # Changed session state key

    if st.session_state.get("online_model_dialog_open", False): # Changed session state key
        manage_online_models_dialog()

    online_model_names_list = openai_scripts.get_openai_model_names()
    current_default_online_model = config.get("OPENAI", "model", fallback="")

    if online_model_names_list:
        selected_default_online_model = st.selectbox(
            "选择默认在线模型:",
            online_model_names_list,
            index=(
                online_model_names_list.index(current_default_online_model)
                if current_default_online_model in online_model_names_list
                else 0
            ),
            help="选择一个在上面“模型管理”中配置好的模型作为默认使用。",
            key="online_default_model_selector", # Changed key
        )
    elif current_default_online_model: # List is empty, but a default was saved
        selected_default_online_model = st.text_input(
            "当前默认在线模型 (列表为空):",
            current_default_online_model,
            disabled=True,
            help="请通过“管理在线模型列表”添加模型后再选择。"
        )
        st.warning("在线模型列表为空。请通过“管理在线模型列表”添加模型配置。")
    else: # List is empty and no default saved
        selected_default_online_model = ""
        st.warning("没有可用的在线模型。请通过“管理在线模型列表”添加和配置模型。")


    # Parameters for the default online model (still stored in [OPENAI] section of config.ini)
    openai_max_tokens = st.number_input(
        "默认Tokens上限 (max_tokens):",
        min_value=50,
        max_value=128000, # Increased max
        value=int(config.get("OPENAI", "max_tokens", fallback="4096")),
        step=10,
        help="所选默认在线模型单次调用可生成的最大Token数量。",
        key="online_model_max_tokens_input", # Changed key
    )
    openai_temperature = st.slider(
        "默认Temperature:",
        0.0,
        2.0,
        float(config.get("OPENAI", "temperature", fallback="0.7")),
        step=0.05,
        help="控制生成文本的随机性。较低值使其更保守，较高值更具创造性。",
        key="online_model_temp_slider", # Changed key
    )
    openai_top_p = st.slider(
        "默认Top_p:",
        0.0,
        1.0,
        float(config.get("OPENAI", "top_p", fallback="1.0")),
        step=0.05,
        help="核心采样参数。模型会考虑累积概率达到top_p的最高概率词汇。",
        key="online_model_top_p_slider", # Changed key
    )

    if st.button("保存在线模型默认设置", key="save_online_model_defaults", type="primary"): # Changed key
        if not selected_default_online_model and online_model_names_list:
            st.error("请选择一个默认的在线模型。")
        elif not online_model_names_list and not selected_default_online_model:
            st.warning("没有配置任何在线模型，无法保存默认设置。请先管理模型列表。")
        else:
            config["OPENAI"]["model"] = selected_default_online_model
            config["OPENAI"]["max_tokens"] = str(openai_max_tokens)
            config["OPENAI"]["temperature"] = str(openai_temperature)
            config["OPENAI"]["top_p"] = str(openai_top_p)
            save_configuration()