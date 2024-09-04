from gensim import corpora, models
from gensim.utils import simple_preprocess
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords')


def preprocess(text):
    result = []
    for token in simple_preprocess(text):
        if token not in stopwords.words('english'):
            result.append(token)
    return result

def build_lda_model(dataframe, num_topics, num_passes):
    
    documents = dataframe['text'].tolist()
    processed_docs = [preprocess(doc) for doc in documents]
    dictionary = corpora.Dictionary(processed_docs)
    dictionary.filter_extremes(no_below=15, no_above=0.5, keep_n=100000)

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
    
    return lda_model
