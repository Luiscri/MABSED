import sys
sys.dont_write_bytecode = True

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import *

def filter_spam(tweets, max_relative_sim):
    vectorizer = train_vectorizer(tweets)
    non_sense_word = 'nonsensewordusedtoinitializebuffer'
    tweet_buffer_vector = vectorizer.transform([non_sense_word])
    tweet_buffer_text = [non_sense_word]

    filtered_tweets = []
    spam = []
    for tweet in tweets:
        text = clear_mentions_links(tweet['text'])
        text_vector = vectorizer.transform([text])
        similarity_list = cosine_similarity(text_vector.reshape(1,-1), tweet_buffer_vector)
        similarity = similarity_list.max()
        if similarity >= max_relative_sim:
            i, j = np.where(similarity_list == similarity)
            saving_spam = {
                'detected': text,
                'from': tweet_buffer_text[j[0]]
            }
            spam.append(saving_spam)
            continue
        tweet_buffer_vector = vstack([tweet_buffer_vector, text_vector])
        tweet_buffer_text.append(text)
        filtered_tweets.append(tweet)
    return filtered_tweets, spam

def clear_mentions_links(text):
    words = text.split()
    cleaned_words = [word for word in words if ('@' not in word and 'http' not in word)]
    return ' '.join(cleaned_words)

def train_vectorizer(tweets):
    tweets_text = read_files(tweets)
    vectorizer = TfidfVectorizer()
    vectorizer.fit(tweets_text)
    return vectorizer

def read_files(tweets):
    tweets_text = []
    for tweet in tweets:
        tweets_text.append(tweet['text'])
    return tweets_text