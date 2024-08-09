import streamlit as st
from scholar.lens_metadata import *
from patents.lens_metadata import *
from utils.llm import *
from openai import OpenAI

token = st.secrets["mytoken"]
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title('🤖 👨‍🍳 ')
tab1, tab2, tab3 = st.tabs(["Haku", "Ohjeita", "Tietoja"])

with tab1:
    search_type = st.radio("Valitse hakukohde", ('Julkaisut', 'Patentit'))

    with st.form("query_form"):
        start_date = st.text_input("Aloituspäivä (YYYY-MM-DD)", "2024-05-01")
        end_date = st.text_input("Lopetuspäivä (YYYY-MM-DD)", "2024-05-02")
        query = st.text_area("Kirjoita kysely", '(cement OR concrete) AND (sustainable OR renewable)')
        
        if search_type == 'Patentit':
            class_cpc_prefix = st.text_input("CPC luokitus tai sen alku (valinnainen)", "")
        
        col1, col2, _ = st.columns([1,1,4])
        submit_button = col1.form_submit_button("Hae data")

        if submit_button:
            token = token
            if search_type == 'Julkaisut':
                results = get_publication_data_with_query(start_date, end_date, query, token)
                st.write(f"Julkaisujen osumien määrä: {len(results['data'])}")
                df = publication_table(results)
                authors = author_table(results)
                fs = fields_of_study_table(results)
                st.dataframe(df)
                st.dataframe(authors)
                st.dataframe(fs)

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

