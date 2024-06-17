# This code fetches full texts, tables and metadata from springer publications that are open source.
# Article text and article metadata are stored in pandas dataframes

import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time

def get_springer_full_texts(dois, api_key, delay=1):
    results = []
    
    for doi in dois:
        url = f"https://api.springernature.com/openaccess/jats?q=doi:{doi}&api_key={api_key}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            results.append(response.text)
        else:
            results.append(f"Failed to retrieve article. Status code: {response.status_code}, Message: {response.text}")
        
        time.sleep(delay)

    return results

def get_springer_metadata(api_key, dois):
    base_url = "https://api.springernature.com/meta/v2/json"
    headers = {"Accept": "application/json"}
    
    all_data = []  
    for doi in dois:
        params = {
            "q": f"doi:{doi}",
            "api_key": api_key
        }
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            if 'records' in data:
    
                for record in data['records']:
                    
                    record_data = {
                        "contentType": record.get("contentType"),
                        "identifier": record.get("identifier"),
                        "title": record.get("title"),
                        "creators": ", ".join([creator['creator'] for creator in record.get("creators", [])]),
                        "publicationName": record.get("publicationName"),
                        "issn": record.get("issn"),
                        "eissn": record.get("eissn"),
                        "openaccess": record.get("openaccess"),
                        "journalid": record.get("journalid"),
                        "doi": record.get("doi"),
                        "publisher": record.get("publisher"),
                        "publicationDate": record.get("publicationDate"),
                        "onlineDate": record.get("onlineDate"),
                        "coverDate": record.get("coverDate"),
                        "printDate": record.get("printDate"),
                        "volume": record.get("volume"),
                        "number": record.get("number"),
                        "issuetype": record.get("issuetype"),
                        "startingPage": record.get("startingPage"),
                        "endingPage": record.get("endingPage"),
                        "copyright": record.get("copyright"),
                        "genre": record.get("genre"),
                        "articleCategory": record.get("articleCategory"),
                        "abstract": record.get("abstract"),
                        "subjects": ", ".join(record.get("subjects", []))   
                    }
                    
                    all_data.append(record_data)
        else:
            print(f"Failed to fetch data for DOI {doi}: {response.status_code}")
    
    df = pd.DataFrame(all_data)
    return df

def get_all_text(elem):
    text = []
    if elem.text:
        text.append(elem.text.strip())
    for sub_elem in elem:
        sub_text = get_all_text(sub_elem)
        if isinstance(sub_text, list):
            text.extend(sub_text)
        else:
            text.append(sub_text)
    if elem.tail:
        text.append(elem.tail.strip())
    return ''.join(filter(None, text))


def extract_text_tables(xml_data_list):
    
    data_rows = []
    
    for xml_data in xml_data_list:
        root = ET.fromstring(xml_data)
    
        full_text_sections = []
        for sec in root.findall(".//sec"):
            for p in sec.findall(".//p"):
                if p.text:
                    full_text_sections.append(p.text.strip())
        full_text = "\n".join(full_text_sections)
        
        tables_list = []
        tables = root.findall('.//table-wrap')
        for table in tables:
            table_data = {}
            table_data['title'] = get_all_text(table.find('.//label')) if table.find('.//label') else 'No Title'
            caption = table.find('.//caption')
            table_data['caption'] = get_all_text(caption) if caption else 'No Caption'
            
            headers = [get_all_text(th) for th in table.findall('.//thead/tr/th')]
            rows = []
            for tr in table.findall('.//tbody/tr'):
                row_data = [get_all_text(td) for td in tr.findall('.//td')]
                rows.append(row_data)
            table_data['headers'] = headers
            table_data['rows'] = rows
            tables_list.append(table_data)
        
        data_rows.append({
            "Full Text": full_text,
            "Tables": tables_list
        })
    
    df = pd.DataFrame(data_rows)
    return df
