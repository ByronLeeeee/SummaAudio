import streamlit as st
import os
# from page import * # Assuming page.py contains necessary Streamlit page handlers if not using st.Page directly

# Define constants for page paths if they are very complex or used multiple times,
# otherwise, direct string literals are fine.
PAGE_DIR = "page/"

if not os.path.exists("cache"):
    os.makedirs("cache")


home_page = st.Page(f"{PAGE_DIR}home.py", title="首页", icon=":material/home:")
one_click_transcription_page = st.Page(f"{PAGE_DIR}one_click_transcription.py", title="一键转录", icon=":material/graphic_eq:")
transcription_page = st.Page(f"{PAGE_DIR}transcription.py", title="音频转录", icon=':material/speech_to_text:')
fix_typo_page = st.Page(f"{PAGE_DIR}fix_typo.py", title="修正文本", icon=':material/edit_note:')
summary_page = st.Page(f"{PAGE_DIR}summary.py", title="文本归纳", icon=":material/summarize:")
setting_page = st.Page(f"{PAGE_DIR}setting.py", title="设置", icon=":material/settings:")
prompt_manager_page = st.Page(f"{PAGE_DIR}prompts_manager.py", title="提示词管理", icon=":material/library_books:")


pg = st.navigation({
    "首页": [home_page],
    "一键转录": [one_click_transcription_page],
    "分步处理": [transcription_page, fix_typo_page, summary_page],
    "设置": [setting_page, prompt_manager_page]
})

pg.run()