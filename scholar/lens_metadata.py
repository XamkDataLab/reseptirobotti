import requests
import pandas as pd
import streamlit as st
import time

token = st.secrets["mytoken"]

def get_publication_data_with_query(start_date, end_date, query_string, token):
    url = 'https://api.lens.org/scholarly/search'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    query_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": query_string,
                            "fields": ["title", "abstract", "full_text", "fields_of_study"],
                            "default_operator": "and"
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
            }
        },
        "size": 500,
        "scroll": "1m"
    }

    publications = []
    scroll_id = None
    
    progress_bar = st.progress(0)
    placeholder = st.empty()

    while True:
        if scroll_id is not None:
            query_body = {"scroll_id": scroll_id, "scroll": "1m"}

        response = requests.post(url, json=query_body, headers=headers)

        if response.status_code == requests.codes.too_many_requests:
            print("TOO MANY REQUESTS, waiting...")
            time.sleep(8)
            continue

        if response.status_code != requests.codes.ok:
            print("ERROR:", response.status_code, response.text)
            break

        response_data = response.json()
        total_publications = response_data.get('total', 0)

        if total_publications == 0:
            # No results, handle and exit early
            placeholder.text("Hakutuloksia ei löytynyt")
            progress_bar.progress(0.0)
            break

        publications += response_data['data']
        placeholder.text(f"{len(publications)} / {total_publications} julkaisua luettu...")

        # Update progress only when total_publications > 0
        progress_bar.progress(len(publications) / total_publications)
        print(f"{len(publications)} / {total_publications} publications read...")

        if response_data.get('scroll_id'):
            scroll_id = response_data['scroll_id']

        if len(publications) >= total_publications or len(response_data['data']) == 0:
            break

    # Only update progress to 100% if there were publications fetched
    if total_publications > 0:
        placeholder.text("Julkaisut haettu!")
        progress_bar.progress(1.0)

    data_out = {"total": len(publications), "data": publications}
    return data_out


def publication_table(json_data):

    # Check if 'data' key exists and is non-empty
    if 'data' not in json_data or not json_data['data']:
        return pd.DataFrame()  # Return an empty DataFrame if no data
    
    data_list = json_data['data']

    columns = ["lens_id", "title", "publication_type", "year_published", 
               "date_published_parts", "date_published", "created", 
               "references_count", "start_page", "end_page", "author_count", 
               "abstract", "source", "source_urls", "external_ids", "is_open_access", 
               "patent_citations_count", "scholarly_citations_count"]  

    data = [{key: item[key] if key in item else None for key in columns} for item in data_list]

    df = pd.DataFrame(data)

    df["source_title"] = df["source"].apply(lambda x: x.get("title") if x else None)
    df["source_publisher"] = df["source"].apply(lambda x: x.get("publisher") if x else None)
    df = df.drop(columns="source")
    df['date_published'] = pd.to_datetime(df['date_published']).dt.strftime('%Y-%m-%d')
    df["url"] = df["source_urls"].apply(lambda x: x[0]["url"] if x else None)

    df["url"] = df["source_urls"].apply(lambda x: x[0]["url"] if x else None)

    df = df.drop(columns="source_urls")

    def extract_doi(external_ids):
        if external_ids:
            for eid in external_ids:
                if eid['type'] == 'doi':
                    return eid['value']
        return None

    df['DOI'] = df['external_ids'].apply(extract_doi)
    df['link'] = 'https://doi.org/' + df['DOI']
    df = df.drop(columns="external_ids")

    return df

def fields_of_study_table(json_data):
    table_data = []

    for record in json_data['data']:
        lens_id = record.get('lens_id', None)
        fields_of_study = record.get('fields_of_study', [])

        for field in fields_of_study:
            row = {
                'lens_id': lens_id,
                'field_of_study': field
            }
            table_data.append(row)

    df = pd.DataFrame(table_data)
    return df
    
def author_table(json_data):
    
    authors = []
    
    for data_entry in json_data.get('data',[]):
        
        lens_id = data_entry.get('lens_id', None)

        for author_data in data_entry.get('authors', []):
            
            for affiliation in author_data.get('affiliations', []):
                author = author_data.copy()
                
                author.pop('affiliations', None)           
                author['affiliation_name'] = affiliation.get('name', None)
                author['affiliation_name_original'] = affiliation.get('name_original', None)
                author['country_code'] = affiliation.get('country_code', None)
                author['lens_id'] = lens_id
                authors.append(author)

    
    authors_df = pd.DataFrame(authors)
    
    # Safely remove the 'ids' column if it exists
    if 'ids' in authors_df.columns:
        del authors_df['ids']

    return authors_df
