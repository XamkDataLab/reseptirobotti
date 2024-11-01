# charts for lens metadata

import plotly.express as px
import pandas as pd



# articles

# timeseries for number of publications by year and month

def no_pub_by_date(df):
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
    most_cited = df.sort_values(by = 'scholarly_citations_count', ascending = False)
    return most_cited[['title', 'scholarly_citations_count']]

    
# open access 

def open_access(df):
    acc_count_df = df.groupby('is_open_access', dropna = False).size().reset_index(name = 'count')
    fig = px.pie(acc_count_df, values = 'count', names = 'is_open_access',
                 title = 'Avoin saatavuus')
    return fig

# top n fields of study 

def fields_of_study_plot(df, n=10):
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
                 title = "Top 50 yleisintä sanaa")
    fig.update_layout(
        xaxis_title = 'Lukumäärä',
        yaxis_title = 'Sana',
        )
    
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


