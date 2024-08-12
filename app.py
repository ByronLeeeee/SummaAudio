import streamlit as st
from page import *

home_page = st.Page("page/home.py",title="首页",icon=":material/home:")
one_click_transcription_page = st.Page("page/one_click_transcription.py",title="一键转录",icon=":material/graphic_eq:")
transcription_page = st.Page("page/transcription.py",title="音频转录",icon=':material/speech_to_text:')
fix_typo_page = st.Page("page/fix_typo.py",title="修正文本",icon=':material/edit_note:')
summary_page = st.Page("page/summary.py",title="文本归纳",icon=":material/summarize:")
setting_page = st.Page("page/setting.py",title="设置",icon=":material/settings:")
prompt_manager_page = st.Page("page/prompts_manager.py",title="提示词管理",icon=":material/library_books:")


pg = st.navigation({
    "首页": [home_page],
    "一键转录":[one_click_transcription_page],
    "分步处理":[transcription_page,fix_typo_page,summary_page],
    "设置":[setting_page,prompt_manager_page]
})

pg.run()