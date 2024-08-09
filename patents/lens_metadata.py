def get_patent_data_with_query(start_date, end_date, query_string, token, class_cpc_prefix=None):
    url = 'https://api.lens.org/patent/search'
    include = ["lens_id", "date_published", "jurisdiction", "biblio", "doc_key", 
               "publication_type", "families", "biblio.publication_reference", 
               "biblio.invention_title.text", "abstract.text", "claims.claims.claim_text"]

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
        must_clauses = [
            {
                "bool": {
                    "should": [
                        {
                            "query_string": {
                                "query": query_string,
                                "fields": ["title", "abstract", "claim", "description", "full_text"]
                            }
                        },
                        {
                            "prefix": {
                                "class_cpc.symbol": class_cpc_prefix
                            }
                        }
                    ]
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

    query_body = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        },
        "size": 500,
        "scroll": "1m",
        "include": include
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    patents = []
    scroll_id = None

    while True:
        if scroll_id is not None:
            request_body = json.dumps({"scroll_id": scroll_id, "include": include}, ensure_ascii=False)
        else:
            request_body = json.dumps(query_body, ensure_ascii=False)
        
        response = requests.post(url, data=request_body.encode('utf-8'), headers=headers)
        if response.status_code == requests.codes.too_many_requests:
            print("TOO MANY REQUESTS, waiting...")
            time.sleep(8)
            continue
        if response.status_code != requests.codes.ok:
            print("ERROR:", response)
            break
        
        response = response.json()
        patents.extend(response['data'])
        print(len(patents), "/", response['total'], "patents read...")
        
        if response.get('scroll_id'):
            scroll_id = response['scroll_id']
        if len(patents) >= response['total'] or len(response['data']) == 0:
            break

    data_out = {"total": len(patents), "data": patents}
    return data_out["data"]
