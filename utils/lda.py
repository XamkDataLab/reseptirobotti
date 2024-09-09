from gensim import corpora, models
from gensim.utils import simple_preprocess
from gensim.models.coherencemodel import CoherenceModel
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from collections import Counter
import streamlit as st
from joblib import Parallel, delayed
import itertools


if 'nltk_downloaded' not in st.session_state:
    nltk.download('wordnet')
    nltk.download('stopwords')
    nltk.download('omw-1.4')
    st.session_state['nltk_downloaded'] = True

download_nltk_data()

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

custom_stopwords = ['title', 'abstract', 'abstracttext']

stop_words = set(stopwords.words('english'))
stop_words.update(custom_stopwords)

def preprocess(text):
    result = []
    for token in simple_preprocess(text):
        if token not in stop_words and len(token) > 2:
            lemma = lemmatizer.lemmatize(token)  
            result.append(lemma)
    return result

def build_lda_model(dataframe, num_topics, num_passes):
    
    documents = dataframe['text'].tolist()
    processed_docs = [preprocess(doc) for doc in documents]
    dictionary = corpora.Dictionary(processed_docs)
    dictionary.filter_extremes(no_below=15, no_above=0.8, keep_n=1000000)

    corpus = [dictionary.doc2bow(doc) for doc in processed_docs]

    lda_model = models.LdaModel(corpus=corpus,
                                id2word=dictionary,
                                num_topics=num_topics,
                                random_state=100,
                                update_every=1,
                                chunksize=100,
                                passes=num_passes,  
                                alpha='auto',
                                per_word_topics=True)
    
    coherence_model_lda = CoherenceModel(model=lda_model, texts=processed_docs, dictionary=dictionary, coherence='c_v')
    coherence_score = coherence_model_lda.get_coherence()
    st.write(f"Coherence Score: {coherence_score}")

    return lda_model
    

def dataset_statistics(documents):
    with st.spinner('Prosessoidaan dokumentteja...'):
        processed_docs = Parallel(n_jobs=-1)(delayed(preprocess)(doc) for doc in documents)
        
    num_docs = len(processed_docs)
    
    st.write("Lasketaan sanoja ja sanaston kokoa...")
    with st.spinner('Lasketaan sanoja ja sanaston kokoa..."'):
        all_tokens = itertools.chain.from_iterable(processed_docs)
        token_counts = Counter(all_tokens)
        num_words = sum(token_counts.values())
        vocab_size = len(token_counts)

    st.write("Lasketaan dokumenttien pituutta...")
    with st.spinner('Lasketaan dokumenttien pituutta...'):
        doc_lengths = [len(doc) for doc in processed_docs]
        avg_doc_length = sum(doc_lengths) / num_docs if num_docs > 0 else 0
        
    st.write("Poistetaan sanoja...")
    with st.spinner('Poistetaan sanoja..'):
        total_words_raw = sum(len(simple_preprocess(doc)) for doc in documents)
        stopwords_removed = total_words_raw - num_words
        
    st.write("Tunnistetaan yleisimpiä sanoja...")
    with st.spinner('Tunnistetaan yleisimpiä sanoja'):
        top_50_common_words = token_counts.most_common(50)
        least_common_words = [word for word, count in token_counts.items() if count == 1][:10]
    
    return {
        "num_docs": num_docs,
        "num_words": num_words,
        "vocab_size": vocab_size,
        "avg_doc_length": avg_doc_length,
        "doc_lengths": doc_lengths,
        "top_50_common_words": top_50_common_words,
        "least_common_words": least_common_words,
        "stopwords_removed": stopwords_removed
    }

def display_statistics(stats):
    with st.spinner('Näytetään tulokset..'):
        st.write(f"Korpuksen koko: {stats['num_docs']}")
        st.write(f"Sanojen määrä yhteensä: {stats['num_words']}")
        st.write(f"Sanaston koko: {stats['vocab_size']}")
        st.write(f"Keskimääräinen dokumentin pituus: {stats['avg_doc_length']}")
        st.write(f"Dokumenttien pituuden jakauma (min, max, avg): {min(stats['doc_lengths'])}, {max(stats['doc_lengths'])}, {stats['avg_doc_length']}")
        st.write(f"Top 50 yleisimmät sanat: {stats['top_50_common_words']}")
        #st.write(f"Top 10 harvinaisimmat sanat (esiintyy vain kerran): {stats['least_common_words']}")
        st.write(f"Stopwordejä poistettu: {stats['stopwords_removed']}")
        

def analyze_dataset(dataframe):
    documents = dataframe['text'].tolist()
    stats = dataset_statistics(documents)
    return stats



