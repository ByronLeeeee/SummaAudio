import streamlit as st
import json
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Use constants for paths from utils or define locally if utils not imported for this
CONFIG_DIR = "config" # Assuming this script is in page/
PROMPTS_JSON_FILE = "prompts.json"
PROMPTS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), CONFIG_DIR, PROMPTS_JSON_FILE)


st.subheader("📝 提示词管理")
st.info(
    """
    **提示:**
    1.  添加新的提示词时，请确保每个提示词标题的**唯一性**。
    2.  编辑完成后，请**点击表格外的空白区域**以确认更改。
    3.  在文本框内使用 `Shift` + `Enter` 进行换行。
    4.  空标题或空内容的条目在保存时将被忽略。
    """
)

def load_prompts_from_json() -> dict:
    """从JSON文件加载所有提示词数据。"""
    try:
        with open(PROMPTS_JSON_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        # Ensure all expected keys exist
        for key in ["fix_typo_prompt", "summary_prompt", "meeting_minutes_prompt"]:
            if key not in data:
                data[key] = []
        return data
    except FileNotFoundError:
        st.error(f"提示词文件 '{PROMPTS_JSON_PATH}' 未找到。将使用空数据结构。")
        return {"fix_typo_prompt": [], "summary_prompt": [], "meeting_minutes_prompt": []}
    except json.JSONDecodeError:
        st.error(f"提示词文件 '{PROMPTS_JSON_PATH}' 格式错误。将使用空数据结构。")
        return {"fix_typo_prompt": [], "summary_prompt": [], "meeting_minutes_prompt": []}


def save_prompts_to_json(updated_data: dict):
    """
    将所有更新的提示词数据保存到JSON文件。

    :param updated_data: dict, 包含所有更新数据的字典。
    """
    try:
        # Filter out entries with empty titles or content before saving
        for key in updated_data:
            updated_data[key] = [
                prompt for prompt in updated_data[key] 
                if prompt.get("title", "").strip() and prompt.get("content", "").strip()
            ]

        with open(PROMPTS_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(updated_data, file, ensure_ascii=False, indent=4)
        st.success("所有提示词已成功保存！")
    except Exception as e:
        st.error(f"保存提示词失败: {e}")


# Load current prompt data
prompt_data = load_prompts_from_json()

# Define column configuration for the data editor
column_config = {
    "title": st.column_config.TextColumn(
        "提示词标题", 
        help="请输入唯一的提示词标题。",
        required=True, # Make title required
    ),
    "content": st.column_config.TextColumn(
        "提示词内容", 
        help="请输入具体的提示词内容。",
        required=True, # Make content required
    ),
}

# Create tabs for different prompt categories
tab_fix, tab_summary, tab_meeting = st.tabs(["✏️ 修正文本提示词", "📄 归纳总结提示词", "📅 会议记录提示词"])

with tab_fix:
    st.markdown("#### 用于修正文本（如拼写、语法错误）的提示词模板。")
    edited_fix_prompts = st.data_editor(
        prompt_data.get("fix_typo_prompt", []),
        num_rows="dynamic",
        use_container_width=True,
        key="fix_typo_editor",
        column_config=column_config,
        height=400 # Set a fixed height
    )

with tab_summary:
    st.markdown("#### 用于生成文本摘要的提示词模板。")
    edited_summary_prompts = st.data_editor(
        prompt_data.get("summary_prompt", []),
        num_rows="dynamic",
        use_container_width=True,
        key="summary_editor",
        column_config=column_config,
        height=400
    )

with tab_meeting:
    st.markdown("#### 用于生成会议记录的提示词模板。")
    edited_meeting_prompts = st.data_editor(
        prompt_data.get("meeting_minutes_prompt", []),
        num_rows="dynamic",
        use_container_width=True,
        key="meeting_minutes_editor",
        column_config=column_config,
        height=400
    )

st.markdown("---")
if st.button("💾 保存所有更改", type="primary", use_container_width=True):
    # Consolidate potentially edited data
    # The st.data_editor directly returns the edited list of dictionaries
    data_to_save = {
        "fix_typo_prompt": edited_fix_prompts,
        "summary_prompt": edited_summary_prompts,
        "meeting_minutes_prompt": edited_meeting_prompts,
    }
    save_prompts_to_json(data_to_save)
    # No need to st.rerun() usually, unless load_prompts_from_json needs to re-fetch for some reason.
    # The data editors will reflect the current state of their input data.