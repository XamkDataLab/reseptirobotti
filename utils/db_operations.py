from utils.db_connection import connect_to_db

# Function to extract DOI from external_ids
def extract_doi(external_ids):
    if not external_ids or not isinstance(external_ids, list):
        return None
    for item in external_ids:
        if item.get("type") == "doi":
            return item.get("value")
    return None  # Return None if no DOI is found

def insert_pubmetadata(publications):

    conn = connect_to_db()

    if not conn:
        print("Database is not connected")
        return
    
    if not publications or not isinstance(publications, list):
        print("Invalid publications data")
        return
    
    try:
        with conn.cursor() as cur:
            for publication in publications:

                # Extract DOI from external_ids
                external_ids = publication.get("external_ids")
                doi = extract_doi(external_ids)

                cur.execute(
                    """
                    INSERT INTO publications_metadata (lens_id, created, publication_type, title,
                      start_page, end_page, volume, issue, references_count, references_resolved_count,
                      scholarly_citations_count, patent_citations_count, abstract, date_published, year_published,
                      author_count, is_open_access, doi)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (lens_id) DO NOTHING;
                    """,
                    (
                        publication.get("lens_id"),
                        publication.get("created"),
                        publication.get("publication_type"),
                        publication.get("title"),
                        publication.get("start_page"),
                        publication.get("end_page"),
                        publication.get("volume"),
                        publication.get("issue"), 
                        publication.get("references_count"),
                        publication.get("references_resolved_count"),
                        publication.get("scholarly_citations_count"),
                        publication.get("patent_citations_count"), 
                        publication.get("abstract"),
                        publication.get("date_published"),
                        publication.get("year_published"),
                        publication.get("author_count"), 
                        publication.get("is_open_access"),
                        doi        
                    )
                )
        conn.commit()
        print("Data inserted successfully!")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()