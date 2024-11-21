import streamlit as st
from openai import OpenAI
from io import BytesIO

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

def get_page_results(page_index, results_per_page ,df):
    start_index = page_index * results_per_page
    end_index = start_index + results_per_page
    return df.iloc[start_index:end_index]

def update_page():
    st.session_state.current_page = st.session_state.page_dropdown
    
def update_results_per_page():
    st.session_state.current_page = 1  # Reset to first page
    st.session_state.results_per_page = st.session_state.results_dropdown


def display_publication_results():
    
    df = st.session_state['df']
    fs = st.session_state['fs']
    authors = st.session_state['authors']
    
    # Check if 'field_of_study' column exists
    if 'field_of_study' not in fs.columns:
        return  # Exit the function if the column doesn't exist
    
    unique_fields_of_study = sorted(fs['field_of_study'].unique().tolist())

    selected_fields_of_study = st.multiselect('Select Fields of Study', unique_fields_of_study, key='select_fs')

    if selected_fields_of_study:
        relevant_lens_ids = fs[fs['field_of_study'].isin(selected_fields_of_study)]['lens_id'].tolist()
        filtered_publications_df = df[df['lens_id'].isin(relevant_lens_ids)]
        st.session_state.current_page = 1
            
    else:
        filtered_publications_df = df
        
    total_results = len(filtered_publications_df)
    st.write(f"Total results: {total_results}")
    

    if not filtered_publications_df.empty:
        total_pages = (len(filtered_publications_df) - 1) // st.session_state.results_per_page +1
        
        col1, col2 = st.columns([1, 7])
        
        with col1:
            st.selectbox(
                "Results per page", options=[5, 10, 20, 50, 100], index=1,  # Default to 10 results per page
                key="results_dropdown", on_change=update_results_per_page
                )
        
        col1, col2, col3, col4, spacer, col5 = st.columns([3, 1, 1, 1, 3, 1])
        with col1:
            if st.button("Previous") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
            
        with col2:
            st.write("Page")
            
        with col3:
            st.session_state.current_page = st.selectbox(
                "", options=list(range(1, total_pages + 1)), index=st.session_state.current_page - 1, 
                key="page_dropdown", label_visibility = "collapsed",
                on_change = update_page
            )
            
        with col4:
            st.write(f"of {total_pages}")
        
        with col5: 
            if st.button("Next") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
            
        current_page_df = get_page_results(st.session_state.current_page - 1, st.session_state.results_per_page, filtered_publications_df)
        
        
        
        for index, row in current_page_df.iterrows():
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
    
def to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='Sheet1')
    return output.getvalue()


