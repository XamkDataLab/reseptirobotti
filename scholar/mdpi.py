# Functions to parse scholarly articles published my MDPI as XML files
# Full text and tables within the full text are extracted

import xml.etree.ElementTree as ET

def extract_text(element):
    text = ""
    if element.text:
        text += element.text.strip()
    for child in element:
        text += extract_text(child)
        if child.tail:
            text += child.tail.strip()
    return text

def extract_tables(element):
    tables = []
    for table in element.findall('.//table-wrap'):
        table_data = {
            "label": table.findtext('.//label'),
            "caption": table.findtext('.//caption/p'),
            "content": []
        }
        for row in table.findall('.//tr'):
            cols = [extract_text(col) for col in row.findall('.//th')] + [extract_text(col) for col in row.findall('.//td')]
            table_data["content"].append(cols)
        tables.append(table_data)
    return tables

def parse_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    article_body = root.find('.//body')
    if article_body is not None:
        full_text = extract_text(article_body)
        print("Full Text:", full_text)

    tables = extract_tables(root)
    for i, table in enumerate(tables, 1):
        print(f"Table {i}: {table['label']}")
        print("Caption:", table['caption'])
        for row in table['content']:
            print(row)
