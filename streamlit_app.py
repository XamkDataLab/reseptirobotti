import streamlit as st
from scholar.lens_metadata import *
from patents.lens_metadata import *
from utils.llm import *
from utils.lda import *
import utils.visualizations as vis
import re
import plotly.graph_objs as go
import datetime
import streamlit.components.v1 as components


st.set_page_config(layout="wide")

col1, col2, col3 = st.columns([4, 1, 1])

with col1:
    st.title('🤖 👨‍🍳 ')

with col3:
    st.image("./Logos/Logo_yhdistetty.png", width=100)
    
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Haku", "Ohjeita", "Tietoja", "Visualisointeja", "LDA"])

initialize_session_state()

with tab1:

    if 'results_current_page' not in st.session_state:
        st.session_state.results_current_page = 1
    if 'results_per_page' not in st.session_state:
        st.session_state.results_per_page = 10
    
    modify_prompt()
    
    st.subheader("Boolean-kyselyiden aputyökalu")  
    help_query = st.text_area("Kirjoita tähän mitä olet etsimässä ja kielimalli leipoo siitä boolean-kyselyn (toivottavasti)")
    llm_button = st.button("Auta!")


    if 'query' not in st.session_state:
        st.session_state.query = ""

    if llm_button:
            if help_query:  
                response = get_LLM_response(help_query, st.session_state['prompt_user'], st.session_state['prompt_sys'])  
                if response:
                    st.session_state.query = response
                    st.write(response)
                else:
                    st.error("Error: No response from LLM.")
            else:
                st.write("Kerro tukikyselykentässä mitä haluat etsiä ja minä ehdotan.")
    

    search_type = st.radio("Valitse hakukohde", ('Julkaisut', 'Patentit'))
    

    with st.form("query_form"):
 
        col1, col2, col3 = st.columns(3)
  
        with col1:
            min_date = datetime.date(1970, 1, 1)
            start_dateinput = st.date_input("Aloituspäivä (YYYY-MM-DD)", datetime.date(2024, 1, 1), format="YYYY-MM-DD", min_value = min_date)
            start_date = start_dateinput.strftime("%Y-%m-%d")  
            end_dateinput = st.date_input("Lopetuspäivä (YYYY-MM-DD)", datetime.date.today(),format="YYYY-MM-DD", min_value = min_date) 
            end_date = end_dateinput.strftime("%Y-%m-%d")
      
        with col2:
            query = st.text_area("Kirjoita kysely", value = st.session_state.query)
        
        with col3:
            class_cpc_prefix = None 
            if search_type == 'Patentit':
                class_cpc_prefix = st.text_input("CPC luokitus tai sen alku (valinnainen)", "")
                jurisdiction = st.text_input("Jurisdiction (optional)", "")
                applicant_residence = st.text_input('Applicant Residence')
        
        submit_button = st.form_submit_button("Hae data")
        st.session_state.search_type = search_type

        if submit_button:
            st.session_state['data_loaded'] = False
            if search_type == 'Julkaisut':
                results = get_publication_data_with_query(start_date, end_date, query, token)
                st.write(f"Julkaisu-osumien määrä: {len(results['data'])}")
                st.session_state.df = publication_table(results)
                st.session_state.fs = fields_of_study_table(results)
                st.session_state.authors = author_table(results)
                st.session_state['data_loaded'] = True   

            elif search_type == 'Patentit':
                other_filters = {}
                if jurisdiction:
                    other_filters['jurisdiction'] = jurisdiction
                if applicant_residence:
                    other_filters['applicant.residence'] = applicant_residence
                
                results = get_patent_data_with_query(start_date, end_date, query, token, class_cpc_prefix, **other_filters)

                if len(results) > 0:
                    st.write(f"Patenttien osumien määrä: {len(results)}")
                    patents= patents_table(results)
                    applicants = applicants_table(results)
                    c=cpc_classifications_table(results)
                    cpc_classes = make_cpc(c, 'cpc_titles.json')
                    st.session_state.patents = patents
                    st.session_state.applicants = applicants
                    st.session_state.cpc_classes = cpc_classes
           
                else:
                    print("No patent results found for the given query.")

           
           
    if st.session_state.get('data_loaded', False):
        if search_type == 'Julkaisut':
            st.markdown(css_style, unsafe_allow_html=True)
            display_publication_results()
        
        elif st.session_state['patents'] is not None:
            display_patent_results()

    if st.session_state.get('data_loaded', False) and search_type == 'Julkaisut':
        
        publication_excel = to_excel(st.session_state.df)
        fields_of_study_excel = to_excel(st.session_state.fs)
        author_excel = to_excel(st.session_state.authors)

        st.download_button(
            label="Download Publications",
            data=publication_excel,
            file_name='publications.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        st.download_button(
            label="Download Fields of Study",
            data=fields_of_study_excel,
            file_name='fields_of_study.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        st.download_button(
            label="Download Authors",
            data=author_excel,
            file_name='authors.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
                    

    st.caption("Versio 0.22")
    
    
with tab2:
    st.header("Ohjeet boolean-kyselyn muodostamiseen")
    st.markdown("""
    - **AND**: Varmistaa, että molemmat termit löytyvät hakutuloksista. Tämä operaattori on hyödyllinen, kun haluat rajoittaa hakutuloksia siten, että ne sisältävät kaikki annetut hakutermit. Esimerkiksi kysely `omena AND appelsiini` palauttaa vain ne dokumentit, joissa esiintyvät sekä sana "omena" että sana "appelsiini".
    
    - **OR**: Jompikumpi termeistä (tai molemmat) löytyvät hakutuloksista. Tämä operaattori on hyödyllinen laajentamaan hakua, kun etsitään dokumentteja, jotka sisältävät ainakin toisen hakutermeistä. Esimerkki: `omena OR appelsiini` palauttaa dokumentit, joissa on joko "omena", "appelsiini" tai molemmat.
    
    - **NOT**: Ensimmäinen termi sisältyy hakuun, ja toinen termi jätetään pois. Tämä operaattori auttaa poistamaan hakutuloksista ne dokumentit, jotka sisältävät ei-toivotun termin. Esimerkki: `omena NOT appelsiini` palauttaa dokumentit, jotka sisältävät sanan "omena", mutta eivät sanaa "appelsiini".
    
    - **Sulkeiden käyttö** (Parentheses): Käytä sulkeita ryhmittämään termejä ja hallitsemaan operaatioiden järjestystä, mikä on tärkeää monimutkaisten kyselyjen rakentamisessa. Esimerkki: `(omena OR appelsiini) AND trooppinen` varmistaa, että hakutulokset sisältävät joko "omenan" tai "appelsiinin" ja lisäksi sanan "trooppinen".
    
    - **Korvausmerkit** (Wildcards): Käytä `*` usean merkin korvaamiseen ja `?` yhden merkin korvaamiseen. Tämä on hyödyllistä, kun haet sanoja, jotka alkavat tai päättyvät tiettyyn kirjainsarjaan tai kun et ole varma oikeinkirjoituksesta. Esimerkki: `appl*` löytää sanat kuten apple, application, jne.
    
    - **Fraasihaku** (Phrase Search): Käytä lainausmerkkejä tarkan ilmaisun hakemiseen. Tämä on erityisen hyödyllistä, kun etsit tiettyjä ilmaisuja tai kiinteitä sanayhdistelmiä. Esimerkki: `"trooppinen hedelmä"` palauttaa vain ne dokumentit, joissa esiintyvät tämä tarkka ilmaisu.
    
    - **Lähellä haku** (Proximity Search): Käytä `~` merkin jälkeen numeroa osoittamaan, kuinka lähellä toisiaan sanat voivat olla dokumentissa. Tämä on erittäin hyödyllinen, kun haluat löytää dokumentteja, joissa kaksi sanaa esiintyvät tietyllä etäisyydellä toisistaan, mikä osoittaa vahvempaa kontekstuaalista yhteyttä. Esimerkki: `"omena mehu"~10` palauttaa dokumentit, joissa sanat "omena" ja "mehu" esiintyvät enintään kymmenen sanan päässä toisistaan. Tämä voi auttaa löytämään tarkempaa tietoa siitä, miten nämä termit liittyvät toisiinsa kontekstissa.
    
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("Made in XAMK")


with tab4:
    
    if st.session_state.df is not None or st.session_state.patents is not None:
        
        if st.session_state.search_type == 'Julkaisut':

             # Ensure no_pub_by_date returns a valid figure
            fig = vis.no_pub_by_date(st.session_state.df)
            if isinstance(fig, go.Figure):  # Check if it's a valid Plotly figure
                st.plotly_chart(fig)
            
            top_n_pub = st.slider('Valitse top N julkaisijoille:', 
                                  min_value=1, max_value=100, value=10)
            
            fig = vis.barchart_publishers(st.session_state.df, top_n_pub)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)
            
            fig = vis.open_access(st.session_state.df)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)

            fig = vis.fields_of_study_plot(st.session_state.fs)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)

            fig = vis.pub_type(st.session_state.df)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)
            
            st.markdown(
                "<h2 style='font-size: 16px; text-align: left; color: white;'>Eniten viittauksia</h2>",
                unsafe_allow_html=True)

            st.dataframe(vis.most_cited(st.session_state.df))
            
        
            
        elif st.session_state.search_type == 'Patentit':
            fig = vis.no_pub_by_date(st.session_state.patents)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)
            
            top_n_own = st.slider('Valitse top N omistajille:', 
                                  min_value=1, max_value=100, value=10)
            
            fig = vis.owners_barchart(st.session_state.patents, top_n_own)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)

            fig = vis.jurisdiction_barchart(st.session_state.patents)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)

            fig = vis.pub_type(st.session_state.patents)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)

            fig = vis.cpc_treemap(st.session_state.cpc_classes)
            if isinstance(fig, go.Figure):
                st.plotly_chart(fig)
    
    else:
        st.markdown("""
        Hae ensin julkaisuja tai patentteja Haku-välilehdeltä.
        """)

with tab5:
    
    if 'topic_current_page' not in st.session_state:
        st.session_state.topic_current_page = 1
    if 'topic_results_per_page' not in st.session_state:
        st.session_state.topic_results_per_page = 10

    
    st.title('LDA Aihemallinnin')
    if st.session_state.df is not None:
        
        refresh = st.button("Aja uudelleen")
        
        if refresh and 'dataset_analysis_done' in st.session_state:
            st.session_state.dataset_analysis_done = False
    
        df = st.session_state['df']

        # Ensure 'title' and 'abstract' columns exist in the dataframe before accessing them
        if 'title' in df.columns and 'abstract' in df.columns:


            df['text'] = df['title'] + ' ' + df['abstract']
            df = df.dropna(subset=['text'])

            term1 = 'google'
            term2 = 'scholar'
            def check_terms(text):
                text_lower = text.lower()
                return text_lower.count(term1)>=2 and text_lower.count(term2)>=2
            df = df[~df['text'].apply(check_terms)]
            def remove_xml_tags(text):
                return re.sub(r'<.*?>', '', text)
            df['text'] = df['text'].apply(remove_xml_tags)

            
            if 'dataset_analysis_done' not in st.session_state or st.session_state.get('dataset_analysis_done') == False:
                with st.spinner('Analyzing dataset, please wait...'):
                    stats = analyze_dataset(df[['text']])
                    st.session_state['dataset_statistics'] = stats
                    st.session_state['dataset_analysis_done'] = True
                st.success('Dataset analysis complete!')
            
            if 'dataset_statistics' in st.session_state and st.session_state['dataset_statistics'] is not None:
                display_statistics(st.session_state['dataset_statistics'])
            
            else:
                st.write('jee')


            num_topics = st.selectbox('Choose number of topics:', [i for i in range(1, 21)], index=4)
            num_passes = st.slider('Select number of passes:', min_value=1, max_value=50, value=10)

        build_model_clicked = st.button('Build Model')
        if build_model_clicked or 'lda_model' in st.session_state:
            if build_model_clicked:
                lda_model, corpus, dictionary = build_lda_model(df, num_topics, num_passes)
                st.session_state['lda_model'] = lda_model
                st.session_state.corpus = corpus
                st.session_state.dictionary = dictionary
                
                #topics = lda_model.print_topics(num_words=50)
                #formatted_topics = "\n\n".join([f"Topic {i+1}: {topic[1]}" for i, topic in enumerate(topics)])
                #st.session_state['formatted_topics'] = formatted_topics
                st.write("Model built with", num_topics, "topics and", num_passes, "passes!")

                
            if 'lda_model' in st.session_state and 'corpus' in st.session_state and 'dictionary' in st.session_state:
                st.subheader("pyLDAvis Visualization")
                if 'topic_order' not in st.session_state or "lda_vis_html" not in st.session_state:
                    topic_order = display_pyLDAvis(st.session_state['lda_model'], st.session_state['corpus'], st.session_state['dictionary'])
                    st.session_state["topic_order"] = [i - 1 for i in topic_order]
                
                    topics = st.session_state['lda_model'].show_topics(num_topics=-1, num_words=50, formatted = False)
                    st.session_state["reordered_topics"] = [topics[i][1] for i in st.session_state['topic_order']]
               
                components.html(st.session_state["lda_vis_html"], width=1200, height=800)

            if 'reordered_topics' in st.session_state:
                #TOP_WORDS = 10
                st.subheader("LDA Model Topics")
                for idx, topic in enumerate(st.session_state.reordered_topics, start=1):
                    st.subheader(f"Topic {idx}")
                    #st.write(", ".join([f"{word} ({round(float(prob), 3)})" for word, prob in topic]))
                    #top_words = ", ".join([f"{word} ({round(float(prob), 3)})" for word, prob in topic[:TOP_WORDS]])
                    #st.write(f"Top {TOP_WORDS} words: {top_words}")
   
                    with st.expander(f"Show top {len(topic)} words for Topic {idx}"):
                       all_words = ", ".join([f"{word} ({round(float(prob), 3)})" for word, prob in topic])
                       st.write(all_words)
                #st.text(st.session_state.formatted_topics)
                
                if 'analyze_topics_clicked' not in st.session_state:
                    st.session_state['analyze_topics_clicked'] = False
                
                if st.button('Analyze topics'):
                    st.session_state['analyze_topics_clicked'] = True

                if 'reordered_topics' in st.session_state and st.session_state['analyze_topics_clicked']:
                    col1, col2 = st.columns([1, 2])


                    with col1: 
                        if 'llm_response' not in st.session_state:
                            st.session_state['llm_response'] = None
                            
                        if st.session_state['llm_response'] is None:
                            response = get_LLM_response(st.session_state['reordered_topics'], LDA_task_description, system_prompt2)
                            if response:
                                st.session_state['llm_response'] = response
                            else:
                                st.error("Error: No response from LLM.")
                        
                        if st.session_state['llm_response']:
                            st.write(st.session_state['llm_response'])
                            
                    with col2: 
                        documents_in_topic(df)

    else:
        st.write('Tee ensin haku luodaksesi aihemallin')

