import requests
import pandas as pd
import json
import streamlit as st
import time

token = st.secrets["mytoken"]


def build_patent_query(query_string, start_date, end_date, class_cpc_prefix=None, other_filters=None):
    must_clauses = [
        {
            "query_string": {
                "query": query_string,
                "fields": ["title", "abstract", "claim", "description", "full_text"]
            }
        },
        {
            "range": {
                "date_published": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }
    ]

    
    if class_cpc_prefix:
        must_clauses.append({
            "prefix": {
                "class_cpc.symbol": class_cpc_prefix
            }
        })

    if other_filters:
        for field, value in other_filters.items():
            must_clauses.append({
                "term": {
                    field: value
                }
            })

    return {
        "query": {
            "bool": {
                "must": must_clauses
            }
        },
        "size": 500,
        "scroll": "1m",
        "include": [
            "lens_id", "date_published", "jurisdiction", "biblio", "doc_key", 
            "publication_type", "families", "biblio.publication_reference", 
            "biblio.invention_title.text", "abstract.text", "claims.claims.claim_text"
        ]
    }

def get_patent_data_with_query(start_date, end_date, query_string, token, class_cpc_prefix=None, **other_filters):
    url = 'https://api.lens.org/patent/search'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    query_body = build_patent_query(query_string, start_date, end_date, class_cpc_prefix, other_filters)
    
    patents = []
    scroll_id = None
    progress_bar = st.progress(0)
    placeholder = st.empty()

    while True:
        if scroll_id:
            request_body = json.dumps({"scroll_id": scroll_id}, ensure_ascii=False)
        else:
            request_body = json.dumps(query_body, ensure_ascii=False)
        
        response = requests.post(url, data=request_body.encode('utf-8'), headers=headers)
        
        if response.status_code == requests.codes.too_many_requests:
            print("TOO MANY REQUESTS, waiting...")
            time.sleep(8)
            continue
        elif response.status_code != requests.codes.ok:
            print(f"ERROR: {response.status_code} - {response.text}")
            break
        
        response_data = response.json()
        total_patents = response_data.get('total', 0)

        if total_patents == 0:
            placeholder.text("Hakutuloksia ei löytynyt")
            progress_bar.progress(0.0)
            break

        patents.extend(response_data['data'])
        placeholder.text(f"{len(patents)} / {total_patents} patents read...")

        # Avoid ZeroDivisionError by checking total_patents
        if total_patents > 0:
            progress_bar.progress(len(patents) / total_patents)

        print(len(patents), "/", total_patents, "patents read...")
        
        scroll_id = response_data.get('scroll_id')
        if len(patents) >= total_patents or not response_data['data']:
            break

    # Only update to 100% if patents were fetched
    if total_patents > 0:
        placeholder.text("Patents fetched successfully!")
        progress_bar.progress(1.0)
        

    return patents
        



def patents_table(json_data):

    table_data = []

    for record in json_data:
        biblio = record.get('biblio', {})
        publication_reference = biblio.get('publication_reference', {})
        application_reference = biblio.get('application_reference', {})
        priority_claims = biblio.get('priority_claims', {})
        invention_titles = biblio.get('invention_title', [])
        parties = biblio.get('parties', {}) or {}
        abstract = record.get('abstract',[])
        
        owners_all = parties.get('owners_all', [{}])
        extracted_name = None
        if owners_all:
            extracted_name = owners_all[0].get('extracted_name', None)
        
        selected_abstract_lang = None
        selected_title = None
        for lang in ['en', 'fi']:
            for title in invention_titles:
                if title.get('lang') == lang:
                    selected_title = title.get('text')
                    selected_abstract_lang = abstract[0].get('lang') if abstract else None
                    break
            if selected_title:
                break
        if not selected_title:
            selected_title = invention_titles[0].get('text') if invention_titles else None
        
        selected_abstract = None
        for lang in ['en', 'fi']:
            for ab in abstract:
                if ab.get('lang') == lang:
                    selected_ab = ab.get('text')
                    
                    break
            if selected_abstract:
                break
        if not selected_abstract:
            selected_abstract = abstract[0].get('text') if abstract else None
            
        row = {
            'lens_id': record.get('lens_id', None),
            'jurisdiction': record.get('jurisdiction', None),
            'date_published': record.get('date_published', None),
            'doc_key': record.get('doc_key', None),
            'publication_type': record.get('publication_type', None),
            'publication_reference_jurisdiction': publication_reference.get('jurisdiction', None),
            #'publication_reference_doc_number': publication_reference.get('doc_number', None),
            'publication_reference_kind': publication_reference.get('kind', None),
            'publication_reference_date': publication_reference.get('date', None),
            'application_reference_jurisdiction': application_reference.get('jurisdiction', None),
            #'application_reference_doc_number': application_reference.get('doc_number', None),
            'application_reference_kind': application_reference.get('kind', None),
            'application_reference_date': application_reference.get('date', None),
            'priority_claims_earliest_claim_date': priority_claims.get('earliest_claim', {}).get('date', None),
            'invention_title': selected_title,
            'numApplicants': len(parties.get('applicants', [])),
            'numInventors': len(parties.get('inventors', [])),
            'references_cited_patent_count': biblio.get('references_cited', {}).get('patent_count', None),
            'references_cited_npl_count': biblio.get('references_cited', {}).get('npl_count', None),
            'priority_claim_jurisdiction': priority_claims.get('claims', [{}])[0].get('jurisdiction', None),
            'abstract': selected_abstract,
            'abstract_lang': selected_abstract_lang,
            'owner': extracted_name  #
        }
        table_data.append(row)

    df = pd.DataFrame(table_data)
    return df

def cpc_classifications_table(json_data):
    table_data = []
    for record in json_data:
        lens_id = record.get('lens_id', None)
        classifications_cpc = record.get('biblio', {}).get('classifications_cpc', {}).get('classifications', [])

        for classification in classifications_cpc:
            row = {
                'lens_id': lens_id,
                'cpc_classification': classification.get('symbol', None),
                'class': classification['symbol'][0] if classification.get('symbol', None) else None,
                'cpc_code_split': classification['symbol'].split('/')[0] if classification.get('symbol', None) else None,
            }
            table_data.append(row)
    
    df = pd.DataFrame(table_data)
    return df

def applicants_table(json_data):
    
    table_data = []

    for record in json_data:
        biblio = record.get('biblio', {})
        parties = biblio.get('parties', {}) or {}
        applicants = parties.get('applicants', [{}])

        for applicant in applicants:
            row = {
                'lens_id': record.get('lens_id', None),
                'doc_key': record.get('doc_key', None),
                'residence': applicant.get('residence', None),
                'extracted_name': applicant.get('extracted_name', {}).get('value', None),
                'extracted_address': applicant.get('extracted_address', None),
                'nimi': applicant.get('extracted_name', {}).get('value', None),
                'id': applicant.get('sequence', None),
                
            }
            table_data.append(row)

    df = pd.DataFrame(table_data)
    return df

def families_table(json_data):
    table_data = []
    for record in json_data:
        simple_family = record.get('families', {}).get('simple_family', {})
        for member in simple_family.get('members', []):
            document_id = member.get('document_id', {})
            lens_id = member.get('lens_id', None)

            row = {
                'lens_id': record.get('lens_id', None),
                'doc_key': record.get('doc_key', None),
                'family_size': simple_family.get('size', None),
                'family_lens_id': lens_id,
                'family_jurisdiction': document_id.get('jurisdiction', None),
                'doc_number': document_id.get('doc_number', None),
                'family_kind': document_id.get('kind', None),
                'family_date': document_id.get('date', None),
            }
            table_data.append(row)
    df = pd.DataFrame(table_data)
    return df

def breakdown_cpc(code):
    section = code[0]
    c_class = code[:3]
    subclass = code[:4]
    group = code.split('/')[0]
    subgroup = code
    return pd.Series([section, c_class, subclass, group, subgroup])

def make_cpc(df, cpc_json_file):
    
    cpc = pd.read_json(cpc_json_file)

    # Check if 'cpc_classification' column exists in the dataframe
    if 'cpc_classification' in df.columns:

        df[['Section', 'Class', 'Subclass', 'Group', 'Subgroup']] = df['cpc_classification'].apply(breakdown_cpc)
        df['Group'] = df['Group'].apply(lambda x: x + "/00")
        df.drop(['cpc_code_split', 'class'], axis=1, inplace=True)
        df['Section Description'] = df['Section'].map(cpc.set_index('Code')['Description'])
        df['Class Description'] = df['Class'].map(cpc.set_index('Code')['Description'])
        df['Subclass Description'] = df['Subclass'].map(cpc.set_index('Code')['Description'])
        df['Group Description'] = df['Group'].map(cpc.set_index('Code')['Description'])
        df['Subgroup Description'] = df['Subgroup'].map(cpc.set_index('Code')['Description'])
        return df
    else:
        # If 'cpc_classification' column is missing, return a message or handle the case accordingly
        print("Error: 'cpc_classification' column not found in the dataframe.")
        
