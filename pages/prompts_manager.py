import streamlit as st
import json
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JSON_PATH = "config/prompts.json"

st.subheader("提示词管理")

st.info(
    "提示:\n1. 添加新的提示词时，请确保每个提示器都有唯一的标题。\n2. 填写完内容后，请点击一下表格外的空白处，以确认填写内容。\n3. 请使用`Shift`+`Enter`换行。"
)


def json_load():
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def rewrite_data(updated_data):
    """
    将所有更新的数据保存到JSON文件中。

    参数:
    - updated_data: 包含所有更新数据的字典。

    返回值:
    无返回值，但会在前端显示相关信息。
    """
    try:
        all_data = json_load()
        all_data.update(updated_data)

        with open(JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)

        st.success("所有数据已保存")
    except Exception as e:
        st.error(f"保存失败: {e}")


# 加载数据
data = json_load()

# 创建标签页
summary_tab, fix_tab, meeting_tab = st.tabs(["归纳", "修正", "会议记录"])

# 在每个标签页中创建数据编辑器
with summary_tab:
    st_editor = st.data_editor(
        data["summary_prompt"],
        num_rows="dynamic",
        use_container_width=True,
        key="summary",
        column_config={
            "title": st.column_config.TextColumn(
                "提示词标题", help="请输入标题，确保每个标题都是唯一的。"
            ),
            "content": st.column_config.TextColumn("提示词", help="请输入提示词。"),
        },
    )

with fix_tab:
    ft_editor = st.data_editor(
        data["fix_typo_prompt"],
        num_rows="dynamic",
        use_container_width=True,
        key="fix",
        column_config={
            "title": st.column_config.TextColumn(
                "提示词标题", help="请输入标题，确保每个标题都是唯一的。"
            ),
            "content": st.column_config.TextColumn("提示词", help="请输入提示词。"),
        },
    )

with meeting_tab:
    mt_editor = st.data_editor(
        data["meeting_minutes_prompt"],
        num_rows="dynamic",
        use_container_width=True,
        key="meeting",
        column_config={
            "title": st.column_config.TextColumn(
                "提示词标题", help="请输入标题，确保每个标题都是唯一的。"
            ),
            "content": st.column_config.TextColumn("提示词", help="请输入提示词。"),
        },
    )

# 保存按钮
if st.button("保存所有更改"):
    updated_data = {
        "summary_prompt": [
            prompt
            for prompt in st_editor
            if prompt["title"] != "" and prompt["title"] is not None
        ],
        "fix_typo_prompt": [
            prompt
            for prompt in ft_editor
            if prompt["title"] != "" and prompt["title"] is not None
        ],
        "meeting_minutes_prompt": [
            prompt
            for prompt in mt_editor
            if prompt["title"] != "" and prompt["title"] is not None
        ],
    }
    rewrite_data(updated_data)
