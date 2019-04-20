# coding: utf-8

# std
import string
from datetime import timedelta, datetime
import csv
import os
import shutil
import sys

# math
import numpy as np
from scipy.sparse import *

# mabed
import utils as utils
import json

class Corpus:
    def __init__(self, source_directory_path, stopwords_file_path, min_absolute_freq=10, max_relative_freq=0.4, separator='\t', save_voc=False):
        if source_directory_path[-1] != '/':
            source_directory_path = source_directory_path + '/'
        self.source_directory_path = source_directory_path
        self.size = 0 # Numero de tweets en el Corpus
        self.start_date = '3000-01-01 00:00:00' # Fecha del tweet mas antiguo
        self.end_date = '1000-01-01 00:00:00' # Fecha del tweet mas reciente
        self.separator = separator # Separador usado en los ficheros CSV

        # load stop-words
        self.stopwords = utils.load_stopwords(stopwords_file_path)

        # Lista con el path de todos los ficheros CSV del directorio indicado
        files_path = [os.path.join(self.source_directory_path, f) for f in os.listdir(self.source_directory_path) if os.path.isfile(os.path.join(self.source_directory_path, f))]

        # Creamos un diccionario que tenga cuantas veces se ha repetido cada palabra en todos los tweets
        word_frequency = {} 
        for file in files_path:
            with open(file, 'r') as input_file:
                csv_reader = csv.reader(input_file, delimiter=self.separator)
                header = next(csv_reader)
                text_column_index = header.index('text')
                date_column_index = header.index('date')
                tweet_buffer = [] # Buffer para añadir los tweets que vamos analizando para evitar spam
                for line in csv_reader:
                    # Quitamos las menciones y los enlaces al tweet, y vemos si el resto del texto es igual
                    text = self.clear_mentions_links(line[text_column_index])
                    if text in tweet_buffer:
                        continue
                    tweet_buffer.append(text)
                    self.size += 1
                    words = self.tokenize(line[text_column_index]) # Ver metodo mas abajo
                    date = line[date_column_index]
                    if date > self.end_date:
                        self.end_date = date
                    elif date < self.start_date:
                        self.start_date = date
                    # update word frequency
                    for word in words:
                        if len(word) > 1:
                            frequency = word_frequency.get(word)
                            if frequency is None:
                                frequency = 0
                            word_frequency[word] = frequency + 1


        # sort words w.r.t (with respect to) frequency
        vocabulary = list(word_frequency.items())
        vocabulary.sort(key=lambda x: x[1], reverse=True)
        if save_voc:
            with open('vocabulary.txt', 'w') as output_file:
                output_file.write(str(vocabulary))
        self.vocabulary = {} # Diccionario en el que las claves son las palabras que no están en las stopwords y que pasan los umbrales de frecuencia, y cuyo valor es el puesto de dicha palabra segun su frecuencia (0 es que es la que mas sale, 1 la segunda...) 
        vocabulary_size = 0
        # No entiendo bien el criterio que sigue para formar el vocabulario (< max_relative_freq?, self.vocabulary[word] = vocabulary_size?)
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
        self.mention_freq = None # Matiz en formato CSR con la cantidad de menciones que tiene cada palabra en cada time_slice (suma de todos los tweets)
        self.time_slice_length = None # Los minutos que dura el time_slice

    # Elimina las menciones y los enlaces de un string devolviendo otro string con el resto del texto
    def clear_mentions_links(self, text):
        words = text.split()
        cleaned_words = [word for word in words if ('@' not in word and 'http' not in word)]
        return ' '.join(cleaned_words)

    # Devuelve un array con cada palabra del texto que le pasemos eliminando los signos de puntuacion y las urls
    def tokenize(self, text):
        # split the documents into tokens based on whitespaces
        words = text.split()
        # Nos quitamos los enalces
        words_without_links = [word for word in words if 'http' not in word]
        # Sustituimos los signos de puntuacion por espacios por si van pegadas las palabras
        t = str.maketrans("'!¡?¿.,\"()", "          ")
        text = ' '.join(words_without_links).translate(t)
        raw_tokens = text.split()
        # Strip solo quita los signos de puntuacion al principio y al final de la palabra
        # string.punctuation tiene estos caracteres: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
        return [token.strip(string.punctuation).lower() for token in raw_tokens if len(token) > 1]

    # Este metodo lo usamos en el detect_event
    # Sirve para particionar los tweets en los time_slices del Corpus
    def discretize(self, time_slice_length):
        self.time_slice_length = time_slice_length

        # clean the data directory
        if os.path.exists('./data/corpus'):
            shutil.rmtree('./data/corpus')
        os.makedirs('./data/corpus')

        # compute the total number of time-slices
        time_delta = (self.end_date - self.start_date)
        time_delta = time_delta.total_seconds()/60
        self.time_slice_count = int(time_delta // self.time_slice_length) + 1 # La doble barra (//) es para que devuelva solo la parte entera
        self.tweet_count = np.zeros(self.time_slice_count)
        print('   Number of time-slices: %d' % self.time_slice_count)

        # create empty files
        for time_slice in range(self.time_slice_count):
            dummy_file = open('./data/corpus/' + str(time_slice), 'w')
            dummy_file.write('')

        # compute word frequency
        # dok_matrix es de SciPy
        self.global_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.short) 
        self.mention_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.short)

        files_path = [os.path.join(self.source_directory_path, f) for f in os.listdir(self.source_directory_path) if os.path.isfile(os.path.join(self.source_directory_path, f))]
        for file in files_path:      
            with open(file, 'r') as input_file:
                csv_reader = csv.reader(input_file, delimiter=self.separator)
                header = next(csv_reader)
                text_column_index = header.index('text')
                date_column_index = header.index('date')
                tweet_buffer = [] # Buffer para añadir los tweets que vamos analizando para evitar spam
                for line in csv_reader:
                    # Quitamos las menciones y los enlaces al tweet, y vemos si el resto del texto es igual
                    text = self.clear_mentions_links(line[text_column_index])
                    if text in tweet_buffer:
                        continue
                    tweet_buffer.append(text)
                    tweet_date = datetime.strptime(line[date_column_index], "%Y-%m-%d %H:%M:%S")
                    time_delta = (tweet_date - self.start_date)
                    time_delta = time_delta.total_seconds() / 60 # El tiempo transcurrido entre el tweet actual y el primero del Dataset en minutos
                    time_slice = int(time_delta / self.time_slice_length) # Un numero entre 0 y 
                    self.tweet_count[time_slice] += 1
                    # tokenize the tweet and update word frequency
                    tweet_text = line[text_column_index]
                    words = self.tokenize(tweet_text)
                    mention = '@' in tweet_text
                    for word in set(words):
                        word_id = self.vocabulary.get(word)
                        if word_id is not None:
                            self.global_freq[word_id, time_slice] += 1 
                            if mention:
                                self.mention_freq[word_id, time_slice] += 1 
                    with open('./data/corpus/' + str(time_slice), 'a') as time_slice_file:
                        time_slice_file.write(tweet_text+'\n')
        self.global_freq = self.global_freq.tocsr()
        self.mention_freq = self.mention_freq.tocsr()

    # Pasa el time_slice (0, 13, 27...) a la correspondiente fecha que era en un principio
    def to_date(self, time_slice):
        a_date = self.start_date + timedelta(minutes=time_slice*self.time_slice_length)
        return a_date

    # Metodo que devuelve las P (parametro) palabras que mas veces aparezcan con la palabra principal del evento
    def cooccurring_words(self, event, p):
        main_word = event[2]
        word_frequency = {}
        for i in range(event[1][0], event[1][1] + 1):
            with open('./data/corpus/' + str(i), 'r') as input_file:
                tweet_buffer = [] # Buffer para añadir los tweets que vamos analizando para evitar spam
                for tweet_text in input_file.readlines():
                    # Quitamos las menciones y los enlaces al tweet, y vemos si el resto del texto es igual
                    text = self.clear_mentions_links(tweet_text)
                    if text in tweet_buffer:
                        continue
                    tweet_buffer.append(text)
                    words = self.tokenize(tweet_text)
                    if event[2] in words:
                        for word in words:
                            if word != main_word:
                                if len(word) > 1 and self.vocabulary.get(word) is not None:
                                    frequency = word_frequency.get(word)
                                    if frequency is None:
                                        frequency = 0
                                    word_frequency[word] = frequency + 1
        # sort words w.r.t frequency
        vocabulary = list(word_frequency.items())
        vocabulary.sort(key=lambda x: x[1], reverse=True)
        top_cooccurring_words = []
        for word, frequency in vocabulary:
            top_cooccurring_words.append(word)
            if len(top_cooccurring_words) == p:
                # return the p words that co-occur the most with the main word
                return top_cooccurring_words