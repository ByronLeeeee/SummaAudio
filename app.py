import streamlit as st
from pages import *

home_page = st.Page("pages/home.py",title="首页",icon="🏠")
one_click_transcription_page = st.Page("pages/one_click_transcription.py",title="一键转录")
transcription_page = st.Page("pages/transcription.py",title="音频转录")
fix_typo_page = st.Page("pages/fix_typo.py",title="修正文本")
summary_page = st.Page("pages/summary.py",title="文本归纳")
setting_page = st.Page("pages/setting.py",title="设置",icon=":material/settings:")
prompt_manager_page = st.Page("pages/prompts_manager.py",title="提示词管理",icon="📝")

pg = st.navigation({
    "首页": [home_page],
    "一键转录":[one_click_transcription_page],
    "分步处理":[transcription_page,fix_typo_page,summary_page],
    "设置":[setting_page,prompt_manager_page]
})

pg.run()