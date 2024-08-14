import streamlit as st
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai_api_key"])

def get_LLM_response(user_text, task_description, system_prompt):
    try:
        formatted_task_description = task_description.format(user_text)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_task_description}
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4-0125-preview",  
            messages=messages,
        )

        if chat_completion.choices:
            return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "Error"

system_prompt1= "you are a helpful assistant specializing in scientific publications"
task_description1 = """The following is a description of what user wants to find in a big database that contains either scientific publications or patent data. The database supports boolean queries. Formulate the following description into a comprehensive, nuanced and valid boolean query. Provide the suggested query as one line query string formatted as code:\n {}"""

def filter_dataframe(df, fs, selected_fields):
    if selected_fields:
        filtered_fs = fs[fs['field_of_study'].isin(selected_fields)]
        lens_ids = filtered_fs['lens_id'].unique()
        df = df[df['lens_id'].isin(lens_ids)]
    return df

css_style = """
<style>
a.custom-link {
    color: blue;           /* Blue color text */
    text-decoration: none; /* No underline */
    font-size: 24px;       /* Larger font size */
}
</style>
"""

st.markdown(css_style, unsafe_allow_html=True) 
