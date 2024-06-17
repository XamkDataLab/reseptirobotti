import streamlit as st
import pandas as pd
from scholar.lens_metadata import *
import time

st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center;'>Julkaisuhaku</h1>", unsafe_allow_html=True)

if 'publications_df' not in st.session_state:
    st.session_state.publications_df = pd.DataFrame()
if 'fields_of_study_df' not in st.session_state:
    st.session_state.fields_of_study_df = pd.DataFrame()

main_row = st.columns([2, 1, 2])

with main_row[1]:
    start_date = st.date_input('Alkaen', value=pd.to_datetime('2024-01-01'))
    end_date = st.date_input('Päättyen', value=pd.to_datetime('2024-03-01'))

with main_row[2]:
    terms = st.text_area('Hakutermit (erota pilkulla, operaattori OR)', 
                         value='chatbot', 
                         height=300).split(',')

if st.button('Hae Data'):
    token = st.secrets["mytoken"]
    publication_data = get_publication_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), [term.strip() for term in terms], token)
    
    if publication_data and publication_data['data']:
        st.write(f"Löytyi {publication_data['total']} julkaisua")
        st.session_state.publications_df = publication_table(publication_data)
        st.session_state.fields_of_study_df = fields_of_study_table(publication_data)

display_full_df = True
columns_to_display = ['year_published', 'is_open_access', 'title', 'link', 'publication_type', 'source_publisher', 'source_title']

if not st.session_state.fields_of_study_df.empty:
    unique_fields_of_study = st.session_state.fields_of_study_df['field_of_study'].unique().tolist()
    selected_field_of_study = st.selectbox('Select a Field of Study', ['All'] + unique_fields_of_study, key="field_of_study_select")

    if selected_field_of_study == 'All':
        st.write("Full Publications DataFrame:")
        st.dataframe(st.session_state.publications_df[columns_to_display])
    else:
        display_full_df = False
        relevant_lens_ids = st.session_state.fields_of_study_df[st.session_state.fields_of_study_df['field_of_study'] == selected_field_of_study]['lens_id'].tolist()
        
        if relevant_lens_ids:
            filtered_publications_df = st.session_state.publications_df[st.session_state.publications_df['lens_id'].isin(relevant_lens_ids)]
            
            if not filtered_publications_df.empty:
                st.write(f"Filtered Publications for {selected_field_of_study}:")
                st.dataframe(filtered_publications_df[columns_to_display])
            else:
                st.write("No publications found for the selected field of study.")
        else:
            st.write("No lens_ids found for the selected field of study.")
