import streamlit as st
import configparser
import json

def json_load(file_path):
    with open(file_path, 'r',encoding="utf-8") as file:
        data = json.load(file)
    return data

summary_tab,fix_tab,meeting_tab = st.tabs(["归纳","修正","会议记录"])


with summary_tab:
    data = json_load("config/prompts.json")
    df = data["summary_prompt"]
                                                        
    st.data_editor(df, num_rows="dynamic",use_container_width=True)



