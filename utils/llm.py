import streamlit as st
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
query_task_description = """The following is a description of what user wants to find in a big database that contains either scientific publications or patent data. The database supports boolean queries. Formulate the following description into a comprehensive, nuanced and valid boolean query. Provide the suggested query as one line query string formatted as code:\n {}"""
LDA_task_description = "The following is a printout of LDA topic model topics made with gensim library. Top 20 keywords per topic are listed. Go through each topic and then provide a fititng name for each topic and textual description for each topic: \n {}"


def filter_dataframe(df, fs, selected_fields):
    if selected_fields:
        filtered_fs = fs[fs['field_of_study'].isin(selected_fields)]
        lens_ids = filtered_fs['lens_id'].unique()
        df = df[df['lens_id'].isin(lens_ids)]
    return df

def initialize_session_state():
    session_vars = ['df', 'fs', 'authors', 'patents', 'applicants', 'cpc_classes', 'search_type', 'pub_len', 'total_len']
    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = None

css_style = """
<style>
a.custom-link {
    color: blue;           /* Blue color text */
    text-decoration: none; /* No underline */
    font-size: 24px;       /* Larger font size */
}
</style>
"""

def display_publication_results():
    df = st.session_state['df']
    fs = st.session_state['fs']
    unique_fields_of_study = fs['field_of_study'].unique().tolist()
    selected_fields_of_study = st.multiselect('Select Fields of Study', unique_fields_of_study, key='select_fs')

    if selected_fields_of_study:
        relevant_lens_ids = fs[fs['field_of_study'].isin(selected_fields_of_study)]['lens_id'].tolist()
        filtered_publications_df = df[df['lens_id'].isin(relevant_lens_ids)]
    else:
        filtered_publications_df = df
        
    total_results = len(filtered_publications_df)
    st.write(f"Total results: {total_results}")

    if not filtered_publications_df.empty:
        for index, row in filtered_publications_df.head(200).iterrows():
            with st.container():
                link_html = f"<a href='{row['link']}' target='_blank' class='custom-link'>{row['title']}</a>"
                st.markdown(link_html, unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Published on:** {row['date_published']}")
                    st.write(f"**References Count:** {row['references_count']}")

                with col2:
                    st.write(f"**Publisher:** {row['source_publisher']}")
                    st.write(row['publication_type'])

                st.markdown("---")
    else:
        st.write("No publications found for the selected fields of study.")

def display_patent_results():
    patents = st.session_state['patents']
    applicants = st.session_state['applicants']
    cpc_classes = st.session_state['cpc_classes']

    st.write(f"Patenttien osumien määrä: {len(patents)}")
    st.dataframe(patents)
    st.dataframe(applicants)
    st.dataframe(cpc_classes)


