import streamlit as st
from scholar.lens_metadata import *
from patents.lens_metadata import *
from utils.llm import *

st.title('🤖 👨‍🍳 ')
tab1, tab2, tab3, tab4 = st.tabs(["Haku", "Ohjeita", "Tietoja", "Visualisointeja"])

initialize_session_state()

with tab1:
    search_type = st.radio("Valitse hakukohde", ('Julkaisut', 'Patentit'))

    with st.form("query_form"):
        start_date = st.text_input("Aloituspäivä (YYYY-MM-DD)", "2024-01-01")
        end_date = st.text_input("Lopetuspäivä (YYYY-MM-DD)", "2024-08-01")
        query = st.text_area("Kirjoita kysely")
        
        if search_type == 'Patentit':
            class_cpc_prefix = st.text_input("CPC luokitus tai sen alku (valinnainen)", "")
        
        submit_button = st.form_submit_button("Hae data")

        if submit_button:
            token = token
            if search_type == 'Julkaisut':
                results = get_publication_data_with_query(start_date, end_date, query, token)
                st.write(f"Julkaisu-osumien määrä: {len(results['data'])}")
                st.session_state.df = publication_table(results)
                st.session_state.fs = fields_of_study_table(results)
                st.session_state.authors = author_table(results)   

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
                
    if st.session_state.df is not None and st.session_state.fs is not None:
        selected_fields = st.multiselect("Valitse tutkimusalueet", options=st.session_state.fs['field_of_study'].unique())
        filtered_df = filter_dataframe(st.session_state.df, st.session_state.fs, selected_fields)
        
        sort_by = st.selectbox("Järjestä tulokset", options=["date_published", "references_count"])
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=False)
    
        for index, row in filtered_df.head(100).iterrows():
            with st.container():
                link_html = f"<a href='{row['link']}' target='_blank' class='custom-link'>{row['title']}</a>"
                st.markdown(css_style, unsafe_allow_html=True) 
                st.markdown(link_html, unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Published on:** {row['date_published']}")
                    st.write(f"**References Count:** {row['references_count']}")

                with col2:
                    st.write(f"**Publisher:** {row['source_publisher']}")
                    st.write(row['source_title'])

                st.markdown("---")
                
    dfp = st.session_state.df
    st.dataframe(dfp)
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
    st.markdown("Haku-sivun `session_state` dataframeista tehtyjä kuvia")

