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

# lemmatizer
from cube.api import Cube
from cube.io_utils.conll import ConllEntry

# similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# mabed
import utils as utils
import json

class Corpus:
    def __init__(self, source_directory_path, stopwords_file_path, min_absolute_freq, max_relative_freq, max_relative_sim, separator, time_slice_length, save_voc=True):
        if source_directory_path[-1] != '/':
            source_directory_path = source_directory_path + '/'
        self.source_directory_path = source_directory_path
        self.size = 0 # Numero de tweets en el Corpus
        self.start_date = '3000-01-01 00:00:00' # Fecha del tweet mas antiguo
        self.end_date = '1000-01-01 00:00:00' # Fecha del tweet mas reciente
        self.separator = separator # Separador usado en los ficheros CSV

        # load stop-words
        self.stopwords = utils.load_stopwords(stopwords_file_path)

        '''
        self.lemmatizer = Cube(verbose=True)
        self.lemmatizer.load("es", tokenization=False, parsing=False)
        '''

        # Entrenamos el vectorizador y ademas cargamos la fecha de inicio y fin del Corpus
        vectorize = self.train_vectorizer()
        self.vectorizer = vectorize[0]
        print('   Vectorizer trained. Total of words used: %d' % len(self.vectorizer.vocabulary_))

        self.start_date = vectorize[1]
        self.end_date = vectorize[2]

        # clean the data directory
        if os.path.exists('./data/corpus'):
            shutil.rmtree('./data/corpus')
        os.makedirs('./data/corpus')

        # compute the total number of time-slices
        self.time_slice_length = time_slice_length
        time_delta = (self.end_date - self.start_date)
        time_delta = time_delta.total_seconds()/60
        self.time_slice_count = int(math.ceil(time_delta / self.time_slice_length)) # Redondeamos para arriba siempre (5.0 lo redondea a 5.0)
        self.tweet_count = np.zeros(self.time_slice_count)

        # create empty files
        for time_slice in range(self.time_slice_count):
            dummy_file = open('./data/corpus/' + str(time_slice), 'w')
            dummy_file.write('')

        print('   Removing spam from Corpus...')

        # Lista con el path de todos los ficheros CSV del directorio indicado
        files_path = [os.path.join(self.source_directory_path, f) for f in os.listdir(self.source_directory_path) if os.path.isfile(os.path.join(self.source_directory_path, f))]
        word_frequency = {} # Creamos un diccionario que tenga cuantas veces se ha repetido cada palabra en todos los tweets
        for file in files_path:
            non_sense_word = 'nonsensewordusedtoinitializebuffer'
            non_sense_vector = self.vectorizer.transform([non_sense_word])
            tweet_buffer = non_sense_vector # Buffer para añadir los vectores de los tweets que vamos analizando para evitar spam
            with open(file, 'r') as input_file:
                csv_reader = csv.reader(input_file, delimiter=self.separator)
                header = next(csv_reader)
                tweetId_column_index = header.index('tweetId')
                authorId_column_index = header.index('authorId')
                coordinates_column_index = header.index('coordinates')
                date_column_index = header.index('date')
                text_column_index = header.index('text')
                for idx, line in enumerate(csv_reader):
                    # Quitamos las menciones y los enlaces al tweet, y vemos si el resto del texto es igual
                    text = self.clear_mentions_links(line[text_column_index])
                    text_vector = self.vectorizer.transform([text])
                    similarity = cosine_similarity(text_vector.reshape(1,-1), tweet_buffer).max()
                    if similarity >= max_relative_sim:
                        with open('./detected_spam.txt' , 'a') as spam_file:
                            spam_file.write(line[text_column_index]+' -->'+str(similarity)+'\n')
                        continue
                    tweet_buffer = vstack([text_vector, tweet_buffer])
                    self.size += 1
                    tweet_date = datetime.strptime(line[date_column_index], "%Y-%m-%d %H:%M:%S")
                    time_delta = (tweet_date - self.start_date)
                    time_delta = time_delta.total_seconds() / 60 # El tiempo transcurrido entre el tweet actual y el primero del Dataset en minutos
                    time_slice = int(time_delta / self.time_slice_length) # Un numero entre 0 y time_slice_count-1
                    self.tweet_count[time_slice] += 1
                    words = self.tokenize(line[text_column_index]) # Ver metodo mas abajo
                    # update word frequency
                    for word in words:
                        if len(word) > 1:
                            frequency = word_frequency.get(word)
                            if frequency is None:
                                frequency = 0
                            word_frequency[word] = frequency + 1
                    with open('./data/corpus/' + str(time_slice), 'a') as time_slice_file:
                        line_json = {
                            'tweetId': line[tweetId_column_index],
                            'authorId': line[authorId_column_index],
                            'coordinates': line[coordinates_column_index],
                            'date': line[date_column_index],
                            'text': line[text_column_index]
                        }
                        saving_line = json.dumps(line_json, ensure_ascii=False)
                        time_slice_file.write(saving_line+'\n')

        print('   Extracting Corpus vocabulary...')

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

        print('   Corpus: %i tweets, spanning from %s to %s' % (self.size,
                                                                self.start_date,
                                                                self.end_date))
        print('   Vocabulary: %d distinct words' % vocabulary_size)
        self.global_freq = None # Matriz en formato CSR con la frecuencia de cada palabra en cada time_slice (para comprobar si aumenta mucho respecto a los demas)
        self.mention_freq = None # Matriz en formato CSR con la cantidad de menciones que tiene cada palabra en cada time_slice (suma de todos los tweets)
        self.user_freq = None # Matriz en formato CSR con la cantidad de usuarios distintos que han usado cada palabra en cada time_slice (suma de todos los tweets)

    # Elimina las menciones y los enlaces de un string devolviendo otro string con el resto del texto
    def clear_mentions_links(self, text):
        words = text.split()
        cleaned_words = [word for word in words if ('@' not in word and 'http' not in word)]
        return ' '.join(cleaned_words)

    def train_vectorizer(self):
        reader = self.read_files()
        # max_features=10000
        vectorizer = TfidfVectorizer()
        vectorizer.fit(reader[0])
        return [vectorizer, reader[1], reader[2]]

    # Pasamos todos los tweets a una lista y declaramos la fecha de inicio y fin del Corpus
    def read_files(self):
        tweets = []
        date_from = self.start_date
        date_to = self.end_date
        files_path = [os.path.join(self.source_directory_path, f) for f in os.listdir(self.source_directory_path) if os.path.isfile(os.path.join(self.source_directory_path, f))]
        for file in files_path:
            with open(file, 'r') as input_file:
                csv_reader = csv.reader(input_file, delimiter=self.separator)
                header = next(csv_reader)
                text_column_index = header.index('text')
                date_column_index = header.index('date')
                for line in csv_reader:
                    tweet_date = line[date_column_index]
                    if tweet_date > date_to:
                        date_to = tweet_date
                    elif tweet_date < date_from:
                        date_from = tweet_date
                    tweet = self.clear_mentions_links(line[text_column_index])
                    tweets.append(tweet)
        date_from = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S") # Lo pasamos a formato Date (estaba en String) 
        date_to = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S") # Lo pasamos a formato Date (estaba en String)
        return [tweets, date_from, date_to]

    # Devuelve una lista de lemas eliminando los signos de puntuacion y los links
    def tokenize(self, text):
        # split the documents into tokens based on whitespaces
        words = text.split()
        # Nos quitamos los enalces
        words_without_links = [word for word in words if 'http' not in word]
        # Sustituimos los signos de puntuacion por espacios por si van pegadas las palabras
        t = str.maketrans("'!¡?¿.,\"()", "          ") # Translate solo se le puede aplicar a un string
        raw_tokens = ' '.join(words_without_links).translate(t).split()
        # Strip solo quita los signos de puntuacion al principio y al final de la palabra
        # string.punctuation tiene estos caracteres: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
        punctuation = string.punctuation.replace('@', '').replace('#', '')
        return [token.strip(punctuation).lower() for token in raw_tokens if len(token) > 1]


    def lemmatize(self, words):
        lemmas = []
        tokens = []
        for idx, word in enumerate(words):
            if '@' in word or '#' in word:
                lemmas.append(word)
            else:
                if word != '':
                    entry = ConllEntry(idx+1, word, "_", "_", "_", "_", 0, "_", "_", "_")
                    tokens.append(entry)

        # lemmas
        if len(tokens) == 0:
            return []
        sentences = self.lemmatizer([tokens])
        for entry in sentences[0]:
            lemmas.append(entry.lemma)
        return lemmas

    # Creamos las matrices que usaremos para el proceso de deteccion
    def compute_matrices(self):
        # compute word frequency
        # dok_matrix es de SciPy
        self.global_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.int32) 
        self.mention_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.int32)
        self.user_freq = dok_matrix((len(self.vocabulary), self.time_slice_count), dtype=np.int32)

        for i in range(0, self.time_slice_count):
            with open('./data/corpus/' + str(i), 'r') as input_file:
                user_buffer = {} # Diccionario en el que la clave sera una palabra y el valor un set con los usuarios que la han tweeteado en este time_slice
                for line in input_file.readlines():
                    line_json = json.loads(line)
                    tweet_text = line_json['text']
                    tweet_user = line_json['authorId']
                    time_slice = i
                    # tokenize the tweet and update matrices
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
            with open('./data/corpus/' + str(i), 'r') as input_file:
                for line in input_file.readlines():
                    line_json = json.loads(line)
                    tweet_text = line_json['text']
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