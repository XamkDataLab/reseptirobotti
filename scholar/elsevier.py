# Search from Scopus database using specific searchterms. Returns DOIs fro scientific articles
# Using those DOIs functions search articles and metadata from Science Direct database. Returns dataframes for metadata and full text

import requests
import pandas as pd
import xml.etree.ElementTree as ET

# Replace with your actual API key
API_KEY = 'YOUR_APIKEY_HERE'
HEADERS = {'X-ELS-APIKey': API_KEY}

# Base URL for the Scopus API
scopus_base_url = "https://api.elsevier.com/content/search/scopus"

# Search terms
terms = ["low carbon concrete", "green concrete", "eco concrete", "sustainable concrete"]

# Construct the query string
query_terms = ' OR '.join(f'TITLE-ABS-KEY("{term}")' for term in terms) #TITLE only from titles, TITLE-ABS-KEY from title, abstract and keywords, ALL from every possible field
query = f'({query_terms})'

# By default this retrieves only 25 results. Following code allows you to change number of results as you want
num_results_per_page = 25  # Maximum number of results per page
start_page = 0  # Starting page number
total_results_to_fetch = 1000  # Total number of results you want to fetch
total_results_fetched = 0  # Counter for total results fetched
prev_total_results_fetched = total_results_fetched # Previous total results fetched
dois = [] 

# Loop through pages and fetch results
try:
    while total_results_fetched < total_results_to_fetch:
        # Construct the request URL
        scopus_url = f"{scopus_base_url}?query={query}&apiKey={API_KEY}&start={start_page}&count={num_results_per_page}&date=2023-2024"
        
        # Make the API request
        response = requests.get(scopus_url)
        
        # Check for errors
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
        
        data = response.json()

        # Extract article DOI
        articles = data.get("search-results", {}).get("entry", [])
        
        # Process the results
        for article in articles:
            doi = article.get("prism:doi")

            if doi:
                dois.append(doi)
                total_results_fetched += 1
            
                # Check if new results were fetched
        if total_results_fetched == prev_total_results_fetched:
            print("No new results found. Stopping search. Results found:",total_results_fetched)
            print(dois)
            break

        # Update the previous total results fetched
        prev_total_results_fetched = total_results_fetched
        
        # Move to the next page
        start_page += num_results_per_page

except Exception as e:
    print(f"An error occurred: {str(e)}")

# Function to get metadata for a single DOI
def get_metadata(doi):

    url = f'https://api.elsevier.com/content/article/doi/{doi}'
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise an error for bad status codes
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            print(f"Error parsing XML for DOI: {doi}, Response text: {response.text}")
            return None
        try:
            ns = {
                'dc': 'http://purl.org/dc/elements/1.1/',
                'prism': 'http://prismstandard.org/namespaces/basic/2.0/',
                'dcterms': 'http://purl.org/dc/terms/'
            }
            title = root.find('.//dc:title', ns).text if root.find('.//dc:title', ns) is not None else ''
            abstract = root.find('.//dc:description', ns).text if root.find('.//dc:description', ns) is not None else ''
            keywords = [kw.text for kw in root.findall('.//dcterms:subject', ns)]
            publication_name = root.find('.//prism:publicationName', ns).text if root.find('.//prism:publicationName', ns) is not None else ''
            publication_date = root.find('.//prism:coverDate', ns).text if root.find('.//prism:coverDate', ns) is not None else ''
            doi = root.find('.//prism:doi', ns).text if root.find('.//prism:doi', ns) is not None else ''
            issn = root.find('.//prism:issn', ns).text if root.find('.//prism:issn', ns) is not None else ''
            volume = root.find('.//prism:volume', ns).text if root.find('.//prism:volume', ns) is not None else ''
            issue = root.find('.//prism:issueIdentifier', ns).text if root.find('.//prism:issueIdentifier', ns) is not None else ''
            page_range = root.find('.//prism:pageRange', ns).text if root.find('.//prism:pageRange', ns) is not None else ''
            authors = [author.text for author in root.findall('.//dc:creator', ns)]
          
            return {
                'DOI': doi,
                'Title': title,
                'Abstract': abstract,
                'Keywords': keywords,
                'Publication Name': publication_name,
                'Publication Date': publication_date,
                'ISSN': issn,
                'Volume': volume,
                'Issue': issue,
                'Page Range': page_range,
                'Authors': authors
            }
        except Exception as e:
            print(f"Error extracting data for DOI: {doi} - {e}")
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for DOI: {doi} - {http_err}")
        return None
    except Exception as err:
        print(f"Other error occurred for DOI: {doi} - {err}")
        return None

def get_full_text_articles(dois):
    headers = {
        'X-ELS-APIKey': API_KEY,
        'Accept': 'application/xml'
    }
    
    articles = []
    
    for doi in dois:
        url = f"https://api.elsevier.com/content/article/doi/{doi}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            articles.append({
                'doi': doi,
                'xml_content': response.content
            })
            
        else:
            print(f"Error: Unable to retrieve article for DOI {doi} (Status code: {response.status_code})")
    
    return articles

def parse_article_xml(xml_content):
    root = ET.fromstring(xml_content)
    ns = {'ce': 'http://www.elsevier.com/xml/common/dtd'}
    full_text = []
    for elem in root.findall('.//ce:section', ns):
        paragraphs = elem.findall('.//ce:para', ns)
        for para in paragraphs:
            if para.text:
                full_text.append(para.text)
    return ' '.join(full_text)

articles = get_full_text_articles(dois)

# Parse articles and collect data in a structured format
parsed_articles = []

for article in articles:
    article_text = parse_article_xml(article['xml_content'])
    parsed_articles.append({
        'doi': article['doi'],
        'full_text': article_text
    })

# Convert to DataFrame
df_fulltext = pd.DataFrame(parsed_articles)

# Optionally save DataFrame to Excel file
output_filename = 'elsevier_fulltext.xlsx'
df_fulltext.to_excel(output_filename, index=False)

print(df_fulltext)

# List to store the metadata
metadata_list = []

# Retrieve metadata for each DOI
for doi in dois:
    metadata = get_metadata(doi)
    if metadata:
        metadata_list.append(metadata)

# Create a DataFrame from the metadata list
df_metadata = pd.DataFrame(metadata_list)

# Display the DataFrame
print(df_metadata)

# Optionally save the DataFrame to a excel file
df_metadata.to_excel('elsevier_metadata.xlsx', index=False)
