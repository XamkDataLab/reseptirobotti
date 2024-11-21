# charts for lens metadata

import plotly.express as px
import pandas as pd
import random
import plotly.graph_objects as go
import streamlit as st
from wordcloud import WordCloud
from io import BytesIO

# articles

# timeseries for number of publications by year and month

def no_pub_by_date(df):

    # Check if 'date_published' column exists
    if 'date_published' not in df.columns:
        return "The 'date_published' column is missing from the data."
    
    df['year_month'] = pd.to_datetime(df['date_published']).dt.to_period('M')
    date_count_df = df.groupby('year_month').size().reset_index(name = 'count')
    date_count_df['year_month'] = date_count_df['year_month'].dt.to_timestamp()
    
    fig = px.line(date_count_df, x='year_month', y='count', 
                  title='Julkaisujen määrä yli ajan')
    fig.update_layout(
        xaxis_title = '',
        yaxis_title = '',
    )
    
    fig.update_xaxes(type='date', tickformat='%Y-%m', dtick='M1')
    fig.update_yaxes(range=[0, date_count_df['count'].max() + 1])
    return fig

# publishers top n barchart 

def barchart_publishers(df, n=10):

    if 'source_publisher' not in df.columns:
        return "Column 'source_publisher' not found in the DataFrame"

    pub_count_df = df.groupby('source_publisher').size().reset_index(name = 'count') 
    pub_count_df = pub_count_df.sort_values(by = 'count', ascending = False).head(n)
    fig = px.bar(pub_count_df, y = "source_publisher", x ='count', 
                 title = f'Top {n} julkaisijat', orientation = 'h',
                 text = 'count')
    fig.update_layout(
            xaxis_title = "Julkaisuja",
            yaxis_title = 'Julkaisija',
            )
   
    fig.update_traces(texttemplate='%{text}', textposition='outside')  
    return fig

# most scholarly citations barchart

def top_most_cited(df, n = 10):
    most_cited = df.sort_values(by = 'scholarly_citations_count', ascending = False).head(n)
    fig = px.bar(most_cited, x = 'scholarly_citations_count', 
                 y = 'title', orientation = 'h', 
                 title = f"Top {n} viitatuimmat artikkelit",
                 text = 'scholarly_citations_count')
    fig.update_layout(
         xaxis_title = "Viittauksia",
         yaxis_title = 'Otsikko',
         )
    fig.update_traces(texttemplate='%{text}', textposition='outside')  
    return fig

# most scholarly citations dataframe

def most_cited(df):

    if df.empty or 'scholarly_citations_count' not in df.columns:
        return None
    
    most_cited = df.sort_values(by = 'scholarly_citations_count', ascending = False)
    return most_cited[['title', 'scholarly_citations_count']]

    
# open access 

def open_access(df):

    if 'is_open_access' not in df.columns:
        return "Column 'is_open_access' not found in the DataFrame"
    
    acc_count_df = df.groupby('is_open_access', dropna = False).size().reset_index(name = 'count')

    acc_count_df ['is_open_access'] = acc_count_df['is_open_access'].replace({
        True : 'Saatavilla',
        None : 'Ei saatavilla'
    })

    fig = px.pie(acc_count_df, values = 'count', names = 'is_open_access',
                 title = 'Avoin saatavuus')
    return fig

# top n fields of study 

def fields_of_study_plot(df, n=10):
   
   if 'field_of_study' not in df.columns:
        return "Column 'field_of_study' not found in the DataFrame"
   
   fos_count_df = df.groupby('field_of_study').size().reset_index(name = 'count') 
   fos_count_df = fos_count_df.sort_values(by = 'count', ascending = False).head(n)
   fig = px.bar(fos_count_df, y = "field_of_study", x ='count', 
                 title = f'Top {n} tutkimusalat', orientation = 'h',
                 text = 'count')
   fig.update_layout(
        xaxis_title = 'Lukumäärä',
        yaxis_title = 'Tutkimusala',
        )
   
   fig.update_traces(texttemplate='%{text}', textposition='outside')  
   return fig

# publication type (can be used for patents also)

def pub_type(df):

    if 'publication_type' not in df.columns:
        return "Column 'publication_type' not found in the DataFrame"
    
    type_count_df = df.groupby('publication_type').size().reset_index(name = 'count')
    type_count_df = type_count_df.sort_values(by = 'count', ascending = False)
    fig = px.bar(type_count_df, y = "publication_type", x ='count', 
                 title = 'Julkaisujen tyypit', orientation = 'h',
                 text = 'count')
    fig.update_layout(
        xaxis_title = 'Lukumäärä',
        yaxis_title = 'Julkaisujen tyypit',
        )
   
    fig.update_traces(texttemplate='%{text}', textposition='outside')  
    return fig

# bar chart for word frequency from texts 

def word_frequency_barplot(df, n=50):
    fig = px.bar(df.head(n), y = "Word", x = "Count", 
                 title = f"Top {n} yleisintä sanaa", orientation = 'h',
                 text = 'Count')
    fig.update_layout(
        xaxis_title = 'Lukumäärä',
        yaxis_title = 'Sana',
        )
   
    fig.update_traces(texttemplate='%{text}', textposition='outside')  
    return fig

def word_freq_barplot(counts):
    words, counts = zip(*counts)
    fig = px.bar(x = words, y = counts,
                 title = "Top 50 yleisintä sanaa",
                 text = counts)
    fig.update_layout(
        xaxis_title = 'Sana',
        yaxis_title = 'Lukumäärä',
        xaxis_tickangle=45
        )
    
    fig.update_traces(textposition="outside")
    return fig


# patents

# jurisdictions barchart
def jurisdiction_barchart(df):
    count_df = df.groupby('jurisdiction').size().reset_index(name = 'count')
    count_df = count_df.sort_values(by = 'count', ascending = False)
    fig = px.bar(count_df, y = "jurisdiction", x ='count', 
                 title = 'Hallintoalueet', orientation = 'h',
                 text = 'count')
    fig.update_layout(
        xaxis_title = 'Lukumäärä',
        yaxis_title = 'Hallintoalue',
        )
   
    fig.update_traces(texttemplate='%{text}', textposition='outside')  
    return fig

# language 
def lang(df):
    count_df = df.groupby('lang', dropna = False).size().reset_index(name = 'count')
    fig = px.pie(count_df, values = 'count', names = 'lang',
                 title = 'Patenttidokumentin alkuperäinen kieli')
    return fig

# owner

def owners_barchart(df, n = 10):
    owners = df['owner'].apply(lambda x: x['value'] if isinstance(x, dict) else None)
    count_df = owners.value_counts().reset_index(name = 'count').head(n)
    count_df.columns = ['owner', 'count']
    fig = px.bar(count_df, y = "owner", x ='count', 
                 title = f'Top {n} patenttien omistajat', orientation = 'h',
                 text = 'count')
    fig.update_layout(
        xaxis_title = 'Lukumäärä',
        yaxis_title = 'Omistaja',
        )
   
    fig.update_traces(texttemplate='%{text}', textposition='outside')  
    return fig


#cpc treemap

def cpc_treemap(df):
    count_df = df.value_counts(subset=['Section Description', 
                                       'Class Description',
                                       'Subclass Description']).reset_index(name = 'count')
    fig = px.treemap(count_df, path=['Section Description', 
                                     'Class Description',
                                     'Subclass Description'],
                     values = 'count', title = 'CPC luokitukset')
    fig.update_traces(root_color="lightgrey")
    return fig

def generate_coordinates(num_words):
    return [(random.uniform(-1, 1), random.uniform(-1, 1)) for _ in range(num_words)]


def create_wordcloud(topic_data):
    coordinates = generate_coordinates(len(topic_data))
    fig = go.Figure()
    
    for (word, prob), (x, y) in zip(topic_data, coordinates):
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                text=[f"{word}"],
                mode="text",
                textfont=dict(size=prob * 2000),
                hoverinfo="text",
            )
        )
    
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="white",
        showlegend=False,
    )
    return fig

def topic_word_clouds(topics):
    for idx, topic in enumerate(topics, start=1):
        st.subheader(f"Word Cloud for Topic {idx}")

        word_freq = dict(topic)

        wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)

        buffer = BytesIO()
        wordcloud.to_image().save(buffer, format="PNG")
        buffer.seek(0)

        st.image(buffer, caption=f"Word Cloud for Topic {idx}", use_column_width=True)