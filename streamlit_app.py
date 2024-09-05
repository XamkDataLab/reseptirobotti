import streamlit as st
from scholar.lens_metadata import *
from patents.lens_metadata import *
from utils.llm import *
from utils.lda import *
import utils.visualizations as vis
import re

st.set_page_config(layout="wide")
st.title('🤖 👨‍🍳 ')
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Haku", "Ohjeita", "Tietoja", "Visualisointeja", "LDA"])

initialize_session_state()

with tab1:

    search_type = st.radio("Valitse hakukohde", ('Julkaisut', 'Patentit'))

    with st.form("query_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            start_date = st.text_input("Aloituspäivä (YYYY-MM-DD)", "2024-05-01")
            end_date = st.text_input("Lopetuspäivä (YYYY-MM-DD)", "2024-05-02")
        
        with col2:
            query = st.text_area("Kirjoita kysely", '(drone* OR UAV* OR "unmanned aerial vehicle") AND (war OR military OR conflict)')
        
        with col3:
            class_cpc_prefix = None
            if search_type == 'Patentit':
                class_cpc_prefix = st.text_input("CPC luokitus tai sen alku (valinnainen)", "")
        
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
                results = get_patent_data_with_query(start_date, end_date, query, token, class_cpc_prefix)
                st.write(f"Patenttien osumien määrä: {len(results)}")
                patents= patents_table(results)
                applicants = applicants_table(results)
                c=cpc_classifications_table(results)
                cpc_classes = make_cpc(c, 'cpc_titles.json')
                st.dataframe(patents)
                st.dataframe(applicants)
                st.dataframe(cpc_classes)
                st.session_state.patents = patents
                st.session_state.applicants = applicants
                st.session_state.cpc_classes = cpc_classes

        if st.session_state.get('data_loaded', False):
            if search_type == 'Julkaisut':
                st.markdown(css_style, unsafe_allow_html=True)

                display_publication_results()
        elif search_type == 'Patentit':
            display_patent_results()
                
    st.subheader("Boolean-kyselyiden aputyökalu")  
    help_query = st.text_area("Kirjoita tähän mitä olet etsimässä ja kielimalli leipoo siitä boolean-kyselyn (toivottavasti)")
    llm_button = st.button("Auta!")

    if llm_button:
            if help_query:  
                response = get_LLM_response(help_query, task_description1, system_prompt1)  
                if response:
                    st.write(response)
                else:
                    st.error("Error: No response from LLM.")
            else:
                st.write("Kerro tukikyselykentässä mitä haluat etsiä ja minä ehdotan.")
    
    
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
            st.plotly_chart(vis.no_pub_by_date(st.session_state.df))
            
            top_n_pub = st.slider('Valitse top N julkaisijoille:', 
                                  min_value=1, max_value=100, value=10)
            
            st.plotly_chart(vis.barchart_publishers(st.session_state.df,
                                                    top_n_pub))
            st.plotly_chart(vis.open_access(st.session_state.df))
            st.plotly_chart(vis.fields_of_study_plot(st.session_state.fs))
            st.plotly_chart(vis.pub_type(st.session_state.df))
            
            st.markdown(
                "<h2 style='font-size: 16px; text-align: left; color: white;'>Eniten viittauksia</h2>",
                unsafe_allow_html=True)
            st.dataframe(vis.most_cited(st.session_state.df))
        
            
        elif st.session_state.search_type == 'Patentit':
            st.plotly_chart(vis.no_pub_by_date(st.session_state.patents))
            
            top_n_own = st.slider('Valitse top N omistajille:', 
                                  min_value=1, max_value=100, value=10)
            
            st.plotly_chart(vis.owners_barchart(st.session_state.patents, top_n_own))
            st.plotly_chart(vis.jurisdiction_barchart(st.session_state.patents))
            st.plotly_chart(vis.pub_type(st.session_state.patents))
            st.plotly_chart(vis.cpc_treemap(st.session_state.cpc_classes))
    
    else:
        st.markdown("""
        Hae ensin julkaisuja tai patentteja Haku-välilehdeltä.
        """)

with tab5:
    st.title('LDA Topic Modeler')
    if st.session_state.df is not None: 
    
        df = st.session_state['df']
        df['text'] = df['title'] + ' ' + df['abstract']
        df = df.dropna(subset=['text'])
        #st.dataframe(df)
        term1 = 'google'
        term2 = 'scholar'
        def check_terms(text):
            text_lower = text.lower()
            return text_lower.count(term1)>=2 and text_lower.count(term2)>=2
        df = df[~df['text'].apply(check_terms)]
        def remove_xml_tags(text):
            return re.sub(r'<.*?>', '', text)
        df['text'] = df['text'].apply(remove_xml_tags)

        num_topics = st.selectbox('Choose number of topics:', [i for i in range(1, 21)], index=4)
        num_passes = st.slider('Select number of passes:', min_value=1, max_value=50, value=10)

        build_model_clicked = st.button('Build Model')
        if build_model_clicked or 'lda_model' in st.session_state:
            if build_model_clicked:
                lda_model = build_lda_model(df, num_topics, num_passes)
                st.session_state['lda_model'] = lda_model
                topics = lda_model.print_topics(num_words=20)
                formatted_topics = "\n\n".join([f"Topic {i+1}: {topic[1]}" for i, topic in enumerate(topics)])
                st.session_state['formatted_topics'] = formatted_topics
                st.write("Model built with", num_topics, "topics and", num_passes, "passes!")
                st.text(formatted_topics)

            if 'formatted_topics' in st.session_state and st.button('Analyze topics'):
                response = get_LLM_response(st.session_state['formatted_topics'], LDA_task_description, system_prompt1)
                if response:
                    st.write(response)
                else:
                    st.error("Error: No response from LLM.")
    else:
        st.write('Tee ensin haku luodaksesi aihemallin')
