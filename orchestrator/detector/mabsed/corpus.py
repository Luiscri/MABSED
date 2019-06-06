# coding: utf-8

# std
import string
from datetime import timedelta, datetime
import csv
import os
import shutil
import sys

# math
import math
import numpy as np
from scipy.sparse import *

# mabed
import mabsed.utils as utils
import json

class Corpus:
    def __init__(self, input_files, stopwords, corpus_directory, min_absolute_freq, max_relative_freq,
                 separator, save_voc=False):
        self.input_files = input_files
        self.size = 0 # Numero de tweets en el Corpus
        self.start_date = '3000-01-01 00:00:00' # Fecha del tweet mas antiguo
        self.end_date = '1000-01-01 00:00:00' # Fecha del tweet mas reciente
        self.separator = separator # Separador usado en los ficheros CSV

        # load stop-words
        self.stopwords = utils.load_stopwords(stopwords)
        #stopwords_en = utils.load_stopwords('./detector/data/stopwords/stopwords-en.txt')
        #self.stopwords = stopwords_es.update(stopwords_en)

        # set corpus output directory
        self.corpus_directory = corpus_directory        

        word_frequency = {} # Creamos un diccionario que tenga cuantas veces se ha repetido cada palabra en todos los tweets
        for file in self.input_files:
            with open(file, 'r') as input_file:
                reader = csv.DictReader(input_file, delimiter='\t')
                tweets = list(reader)
                for tweet in tweets:
                    self.size += 1
                    tweet_date = tweet['date']
                    if tweet_date > self.end_date:
                        self.end_date = tweet_date
                    if tweet_date < self.start_date:
                        self.start_date = tweet_date
                    # words = self.tokenize(tweet['text'])
                    words = self.tokenize(tweet['lemmatizedText'])
                    # update word frequency
                    for word in words:
                        if len(word) > 1:
                            frequency = word_frequency.get(word)
                            if frequency is None:
                                frequency = 0
                            word_frequency[word] = frequency + 1

        # Ordenamos el vocabulario con respecto a su frecuencia - La de mayor frecuencia primero
        vocabulary = list(word_frequency.items())
        vocabulary.sort(key=lambda x: x[1], reverse=True)
        if save_voc:
            with open('vocabulary.txt', 'w') as output_file:
                output_file.write(str(vocabulary))
        self.vocabulary = {} # Diccionario en el que las claves son las palabras que no están en las stopwords y que pasan los umbrales de frecuencia, y cuyo valor es el puesto de dicha palabra segun su frecuencia (0 es que es la que mas sale, 1 la segunda...) 
        vocabulary_size = 0
        for word, frequency in vocabulary:
            if frequency > min_absolute_freq and float(frequency / self.size) < max_relative_freq and word not in self.stopwords:
                self.vocabulary[word] = vocabulary_size
                vocabulary_size += 1
        if save_voc:
            with open('self_vocabulary.txt', 'w') as output_file:
                output_file.write(str(self.vocabulary))

        self.start_date = datetime.strptime(self.start_date, "%Y-%m-%d %H:%M:%S") # Lo pasamos a formato Date (estaba en String) 
        self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d %H:%M:%S") # Lo pasamos a formato Date (estaba en String)

        print('   Corpus: %i tweets, spanning from %s to %s' % (self.size,
                                                                self.start_date,
                                                                self.end_date))
        print('   Vocabulary: %d distinct words' % vocabulary_size)
        self.time_slice_count = None # El numero de time_slices necesario para dividir el Dataset
        self.tweet_count = None # Numero de tweets en cada time_slice
        self.global_freq = None # Matriz en formato CSR con la frecuencia de cada palabra en cada time_slice (para comprobar si aumenta mucho respecto a los demas)
        self.mention_freq = None # Matriz en formato CSR con la cantidad de menciones que tiene cada palabra en cada time_slice (suma de todos los tweets)
        self.user_freq = None # Matriz en formato CSR con la cantidad de usuarios distintos que han usado cada palabra en cada time_slice (suma de todos los tweets)
        self.time_slice_length = None # Los minutos que dura el time_slice

    # Devuelve una lista de lemas eliminando los signos de puntuacion y los links
    def tokenize(self, text):
        # split the documents into tokens based on whitespaces
        words = text.split()
        # Nos quitamos los enalces
        words_without_links = [word for word in words if 'http' not in word]
        # Sustituimos los signos de puntuacion por espacios por si van pegadas las palabras
        t = str.maketrans("'!¡?¿.,\"()…“", "            ") # Translate solo se le puede aplicar a un string
        raw_tokens = ' '.join(words_without_links).translate(t).split()
        # Strip solo quita los signos de puntuacion al principio y al final de la palabra
        # string.punctuation tiene estos caracteres: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
        punctuation = string.punctuation #.replace('@', '').replace('#', '')
        return [token.strip(punctuation).lower() for token in raw_tokens if len(token) > 1]

    # Creamos las matrices que usaremos para el proceso de deteccion
    def compute_matrices(self, time_slice_length):
        self.time_slice_length = time_slice_length

        # clean the data directory
        if os.path.exists(self.corpus_directory):
            shutil.rmtree(self.corpus_directory)
        os.makedirs(self.corpus_directory)

        # compute the total number of time-slices
        time_delta = (self.end_date - self.start_date)
        time_delta = time_delta.total_seconds()/60
        self.time_slice_count = int(math.ceil(time_delta / self.time_slice_length)) # Redondeamos para arriba siempre (5.0 lo redondea a 5.0)
        self.tweet_count = np.zeros(self.time_slice_count)
        print('   Number of time-slices: %d' % self.time_slice_count)

        # create empty files
        for time_slice in range(self.time_slice_count):
            dummy_file = open(self.corpus_directory + str(time_slice), 'w')
            dummy_file.write('')

        # compute word frequency
        # dok_matrix es de SciPy
        self.global_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.int32) 
        self.mention_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.int32)
        self.user_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.int32)

        for file in self.input_files:
            with open(file, 'r') as input_file:
                reader = csv.DictReader(input_file, delimiter='\t')
                tweets = list(reader)
                # lemmatized_text_column_index = header.index('lemmatizedText')
                user_buffer = {} # Diccionario en el que la clave sera una palabra y el valor un set con los usuarios que la han tweeteado en este time_slice
                for tweet in tweets:
                    tweet_date = datetime.strptime(tweet['date'], "%Y-%m-%d %H:%M:%S")
                    tweet_user = tweet['authorId']
                    time_delta = (tweet_date - self.start_date)
                    time_delta = time_delta.total_seconds() / 60 # El tiempo transcurrido entre el tweet actual y el primero del Dataset en minutos
                    time_slice = int(time_delta / self.time_slice_length) # Un numero entre 0 y time_slice_count-1
                    self.tweet_count[time_slice] += 1
                    # tokenize the tweet and update word frequency
                    # tweet_text = tweet['text']
                    tweet_text = tweet['lemmatizedText']
                    words = self.tokenize(tweet_text)
                    mention = '@' in tweet_text
                    for word in set(words): # Transformandolo en set me quito las palabras repetidas en un mismo tweet
                        word_id = self.vocabulary.get(word)
                        if word_id is not None:
                            self.global_freq[word_id, time_slice] += 1 # Se accede asi por ser un dok_matrix
                            if mention:
                                self.mention_freq[word_id, time_slice] += 1
                            if word in user_buffer:
                                if tweet_user in user_buffer[word]:
                                    continue
                                self.user_freq[word_id, time_slice] += 1
                                user_buffer[word].add(tweet_user)
                                continue
                            user_buffer[word] = set()
                            self.user_freq[word_id, time_slice] += 1
                            user_buffer[word].add(tweet_user)
                    with open(self.corpus_directory + str(time_slice), 'a') as time_slice_file:
                        tweet_json = {
                            'tweetId': tweet['tweetId'],
                            'authorId': tweet['authorId'],
                            'coordinates': tweet['coordinates'],
                            'date': tweet['date'],
                            'text': tweet['text'],
                            'lemmatizedText': tweet['lemmatizedText']
                        }
                        saving_tweet = json.dumps(tweet_json, ensure_ascii=False)
                        time_slice_file.write(saving_tweet+'\n')

        self.global_freq = self.global_freq.tocsr()
        self.mention_freq = self.mention_freq.tocsr()
        self.user_freq = self.user_freq.tocsr()

    # Pasa el time_slice (0, 13, 27...) a la correspondiente fecha que era en un principio
    def to_date(self, time_slice):
        a_date = self.start_date + timedelta(minutes=time_slice*self.time_slice_length)
        return a_date

    # Metodo que devuelve las P (parametro) palabras que mas veces aparezcan con la palabra principal del evento
    def cooccurring_words(self, event, p):
        main_word = event[2]
        word_frequency = {} # Diccionario que contiene la frecuencia con la que coincide cada palabra con la palabra principal del evento
        for i in range(event[1][0], event[1][1] + 1):
            with open(self.corpus_directory + str(i), 'r') as input_file:
                for line in input_file.readlines():
                    line_json = json.loads(line)
                    # tweet_text = line_json['text']
                    tweet_text = line_json['lemmatizedText']
                    words = self.tokenize(tweet_text)
                    if main_word in words:
                        for word in words:
                            if word != main_word:
                                if self.vocabulary.get(word) is not None:
                                    frequency = word_frequency.get(word)
                                    if frequency is None:
                                        frequency = 0
                                    word_frequency[word] = frequency + 1
        # Ordenamos las palabras con respecto a su frecuencia - La de mayor frecuencia primero
        vocabulary = list(word_frequency.items())
        vocabulary.sort(key=lambda x: x[1], reverse=True) # Ordena 
        top_cooccurring_words = []
        for word, frequency in vocabulary:
            top_cooccurring_words.append(word)
            if len(top_cooccurring_words) == p:
                # return the p words that co-occur the most with the main word
                return top_cooccurring_words