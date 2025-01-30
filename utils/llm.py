import streamlit as st
from openai import OpenAI
from io import BytesIO
from utils.lda import *

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

system_prompt1= "You are a highly skilled assistant specializing in scientific information retrieval. Your task is to help users craft precise and comprehensive Boolean queries for searching large databases containing scientific publications or patent data. Always ensure the queries are nuanced, valid, and formatted correctly for database compatibility."
system_prompt2= "You are a highly skilled assistant specializing in scientific information retrieval and text analytics. Your task is to help user to understand topics in large database containing scientific articles and patents."
query_task_description = """The following is a description of what the user wants to find in a large database containing scientific publications or patent data. The database supports Boolean queries with operators like AND, OR, and NOT. 

Your task is to:
1. Convert the description into a precise, comprehensive, and valid Boolean query.
2. Use logical operators (AND, OR, NOT) appropriately to structure the query.
3. Incorporate synonyms or related terms where relevant to improve coverage.
4. Format the query as a single-line string, enclosed in code formatting.

Here is the user's description:
{}
"""

LDA_task_description = "The following is a printout of LDA topic model topics made with gensim library. Top 20 keywords and their probabilities per topic are listed. Go through each topic and then provide a fitting name for each topic and textual description for each topic: \n {}"
LDA_analysis_task = "The following is a printout of LDA topic model topics made with gensim library. Top 20 keywords and their probabilities per topic are listed. Go through the probabilities of words and see if there seems to be too few or too many topics. Give your own analysis of this: \n {}"

def update_prompt_sys_from_text_area():
    st.session_state['prompt_sys'] = st.session_state['prompt_sys_text_area']
    
def update_prompt_user_from_text_area():
    st.session_state['prompt_user'] = st.session_state['prompt_user_text_area']

def modify_prompt():
    if 'prompt_sys' not in st.session_state:
        st.session_state['prompt_sys'] = system_prompt1
    if 'prompt_user' not in st.session_state:
        st.session_state['prompt_user'] = query_task_description
        
    with st.expander("Ohjeita promptin muuttamiseen"):
        st.write("""
                 - Voit alta vapaasti muuttaa oletus-prompteja. 
                 - Kun olet muuttanut promptia, muista painaa **Ctrl + Enter**, jotta muutos tallentuu.
                 - Jos haluat palata oletus-promptiin, klikkaa tekstiboxin alla olevaa nappulaa.
                 - **Muutetut promptit eivät talletu mihinkään lopullisesti**, eli muista tallettaa hyväksi toteamasi promptit itsellesi.
                 - Tekstiboxin alta löytyy mallille annettava prompti tarkastukseksi, että koodi toimii oikein.
                 - Voit lukea lisää systeemin ja käyttäjän prompteista esim. [täältä](https://www.nebuly.com/blog/llm-system-prompt-vs-user-prompt).
                 - Käyttäjän promptista ei kannata poistaa **Here is the user's description: {}**, jotta malli saa ohjeet oikein.
                 """)
     
    with st.expander("Muuta prompteja"):
        st.subheader("Muuta systeemin promptia:")
        st.text_area("Prompt system", value = st.session_state['prompt_sys'], 
                     key = "prompt_sys_text_area",
                     on_change = update_prompt_sys_from_text_area)
    
        if st.button("Käytä alkuperäistä  systeemin promptia"):
            st.session_state['prompt_sys'] = system_prompt1
            st.rerun()
        
        st.write(st.session_state['prompt_sys'])
        
        st.subheader("Muuta käyttäjän promptia:")
        st.text_area("Prompt user", value = st.session_state['prompt_user'], 
                     height=270,
                     key = "prompt_user_text_area",
                     on_change = update_prompt_user_from_text_area)
        
        if st.button("Käytä alkuperäistä käyttäjä promptia"):
            st.session_state['prompt_user'] = system_prompt1
            st.rerun()
        
        st.write(st.session_state['prompt_user'])
    

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

def get_page_results(page_index, results_per_page, df):
    start_index = page_index * results_per_page
    end_index = start_index + results_per_page
    
    return df.iloc[start_index:end_index]
##
def get_paginated_data(df, current_page, results_per_page):
    return get_page_results(current_page, results_per_page, df)


def update_page(current_page_key):
    st.session_state[current_page_key] = st.session_state[f"{current_page_key}_dropdown"]    

def update_results_per_page(results_per_page_key, current_page_key):
    st.session_state[current_page_key] = 1  # Reset to first page
    st.session_state[results_per_page_key] = st.session_state[f"{results_per_page_key}_dropdown"]
     
        
def display_paginated_results(df, 
                              render_item_callback,
                              current_page_key,
                              results_per_page_key,
                              layout_small = False):
    

        
    total_results = len(df)
    st.write(f"Total results: {total_results}")
    

    if total_results > 0:
        total_pages = (total_results - 1) // st.session_state[results_per_page_key] + 1

        col1, col2 = st.columns([2, 7])
        with col1:
            st.selectbox(
                "Results per page",
                options=[5, 10, 20, 50, 100],
                index=1,  # Default to 10 results per page
                key=f"{results_per_page_key}_dropdown",
                on_change=lambda: update_results_per_page(results_per_page_key, current_page_key)
            )
        if layout_small == True:
            col1, col2, col3, col4, spacer, col5 = st.columns([2, 1, 1, 1, 1, 1])
        else:
            col1, col2, col3, col4, spacer, col5 = st.columns([3, 1, 1, 1, 3, 1])
        with col1:
            if st.button("Previous", key=f"{current_page_key}_previous_button") and st.session_state[current_page_key] > 1:
                st.session_state[current_page_key] -= 1

                
        with col2:
            st.write("Page")

        with col4:
            st.write(f"of {total_pages}")

        with col5:
            if st.button("Next", key=f"{current_page_key}_next_button") and st.session_state[current_page_key] < total_pages:
                st.session_state[current_page_key] += 1
	
        with col3:
            st.session_state[current_page_key] = st.selectbox(
                "",
                options=list(range(1, total_pages + 1)),
                index=st.session_state[current_page_key] - 1,
                key=f"{current_page_key}_dropdown",
                label_visibility="collapsed",
                on_change=lambda: update_page(current_page_key)
            )
                     
        current_page_df = get_paginated_data(df, st.session_state[current_page_key] - 1, 
                                           st.session_state[results_per_page_key])

        for _, row in current_page_df.iterrows():
            render_item_callback(row)
    else:
        st.write("No results found.")
        
def render_publication_item(row):
    with st.container():
        link_html = f"<a href='{row['link']}' target='_blank' class='custom-link'>{row['title']}</a>"
        st.markdown(link_html, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Published on:** {row['date_published']}")
            st.write(f"**References Count:** {row['references_count']}")

        with col2:
            st.write(f"**Publisher:** {row['source_publisher']}")
            st.write(row['source_title'])

        st.markdown("---")
        
def display_publication_results():
    df = st.session_state['df']
    fs = st.session_state['fs']

    selected_fields_of_study = st.multiselect(
        'Select Fields of Study',
        sorted(fs['field_of_study'].unique().tolist()),
        key='select_fs'
    )

    if selected_fields_of_study:
        relevant_lens_ids = fs[fs['field_of_study'].isin(selected_fields_of_study)]['lens_id'].tolist()
        filtered_publications_df = df[df['lens_id'].isin(relevant_lens_ids)]
        st.session_state["results_current_page"] = 1
    else:
        filtered_publications_df = df

    display_paginated_results(
        df=filtered_publications_df,
        render_item_callback=render_publication_item,
        current_page_key="results_current_page",
        results_per_page_key="results_per_page"
    )
    
def documents_in_topic(df):
    if 'selected_topic_id' not in st.session_state:
        st.session_state['selected_topic_id'] = 0

    if 'topic_probs' not in st.session_state:
        topic_probs = get_topic_probabilities(st.session_state.lda_model, 
                                              st.session_state.corpus)

        if len(topic_probs) == len(df):
            df['topic_probs'] = topic_probs
        else:
            st.error("The length of topic probabilities does not match the number of documents in the DataFrame.")

    st.write("### Select a Topic to Filter Articles")
    selected_topic = st.selectbox("Choose a topic", 
                                  [f"Topic {i+1}" for i in range(st.session_state.lda_model.num_topics)])

    st.session_state['selected_topic_id'] = int(selected_topic.split()[-1]) - 1

    threshold = st.slider("Set the topic probability threshold", 0.0, 1.0, 0.5)
    filtered_df = df[df['topic_probs'].apply(lambda probs: probs[st.session_state.selected_topic_id] >= threshold)]

    display_paginated_results(
        df=filtered_df,
        render_item_callback=render_publication_item,
        current_page_key="topic_current_page",
        results_per_page_key="topic_results_per_page",
        layout_small=True
    )
        

def display_patent_results():
    patents = st.session_state['patents']
    applicants = st.session_state['applicants']
    cpc_classes = st.session_state['cpc_classes']

    st.write(f"Patenttien osumien määrä: {len(patents)}")
    st.dataframe(patents)
    st.dataframe(applicants)
    st.dataframe(cpc_classes)
    
def to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='Sheet1')
    return output.getvalue()


