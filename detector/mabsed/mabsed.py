# coding: utf-8

# std
from multiprocessing import Pool

# math
import networkx as nx
import numpy as np
import stats as st

#saving
import sys # Borrar esto despues de las pruebas
import os
import json
import csv
import re
import datetime

class MABSED:

    def __init__(self, corpus, separator):
        self.corpus = corpus
        self.separator = separator
        self.event_graph = None
        self.redundancy_graph = None
        self.events = None
        self.p = None
        self.k = None
        self.theta = None
        self.sigma = None

    def run(self, k=10, p=10, theta=0.6, sigma=0.5):
        self.p = p
        self.k = k
        self.theta = theta
        self.sigma = sigma
        basic_events = self.phase1()
        return self.phase2(basic_events)

    '''
        Devuelve una lista que contendra una tupla para cada palabra del vocabulario.
        Esta tupla describe el impacto que ha tenido dicha palabra en cuanto a numero de menciones
        ha provocado y numero de usuarios han hablado de ella.
    '''
    def phase1(self):
        print('Phase 1...')
        basic_events = [] # Esto va a ser una lista de tuplas
        for vocabulary_entry in self.corpus.vocabulary.items():
            mention_event = self.get_mention_subsequence(vocabulary_entry)
            # frequency_event = self.get_frequency_subsequence(vocabulary_entry)
            user_event = self.get_user_subsequence(vocabulary_entry)
            basic_events.append(self.merge_basic_event(mention_event, user_event))           
        print('   Detected events: %d' % len(basic_events))
        return basic_events

    def merge_basic_event(self, mention_event, user_event):
        total_magnitude = mention_event[0] + user_event[0]
        magnitudes = (total_magnitude, mention_event[0], user_event[0])
        a = min(mention_event[1][0], user_event[1][0])
        b = max(mention_event[1][1], user_event[1][1])
        interval = (a, b)
        total_anomaly = []
        for i in range(0, self.corpus.time_slice_count):
            sumatory = mention_event[3][i] + user_event[3][i]
            total_anomaly.append(sumatory)
        anomalies = (total_anomaly, mention_event[3], user_event[3])
        return (magnitudes, interval, mention_event[2], anomalies)

    '''
        Metodo que se usara en todas las palabras del vocabulario, y para cada una calcula la
        magnitud del impacto que esta ha generado calculada respecto al numero de menciones
        que ha provocado.
        Devuelve una tupla con: (impacto, intervalo, palabra, lista de anomalias)
    '''
    def get_mention_subsequence(self, vocabulary_entry):
        # vocabulary_entry[1] es el puesto en menciones de cada palabra del diccionario, es decir, 0, 1, 2...
        mention_freq = self.corpus.mention_freq[vocabulary_entry[1], :].toarray() # Aqui tenemos un array con otro array dentro
        mention_freq = mention_freq[0, :] # Ahora tenemos un unico array, que es la columna de la matriz que corresponde a esa palabra del vocabulario, y cada fila sera un time_slice
        total_mention_freq = np.sum(mention_freq) # Sumamos para saber cuantos tweets con mencion tiene esa palabra en total en todo el corpus

        # compute the time-series that describes the evolution of mention-anomaly
        anomaly = [] # Aqui tendremos un array cuyo indice seran los time-slices y cuyos valores seran un float que indica lo que sobresale o decaen las menciones asociadas a dicha palabra respecto de lo esperado en ese time_slice
        # i es el time_slice de cada vuelta
        for i in range(0, self.corpus.time_slice_count):
            # mention_freq[i] es cuantas menciones tiene la palabra en ese time_slice, y es la anomalia observada de esa palabra
            anomaly.append(self.mention_anomaly(i, mention_freq[i], total_mention_freq))
        max_ending_here = max_so_far = 0
        a = b = a_ending_here = 0
        # Cuando acabe este bucle for, a y b representaran el intervalo en el que la suma de las anomalias ha destacado mas de la media
        for idx, ano in enumerate(anomaly):
            max_ending_here = max(0, max_ending_here + ano)
            if max_ending_here == 0:
                # a new bigger sum may start from here
                a_ending_here = idx
            if max_ending_here > max_so_far:
                # the new sum from a_ending_here to idx is bigger
                a = a_ending_here+1
                max_so_far = max_ending_here
                b = idx

        # return the event description
        max_interval = (a, b) # Intervalo en el que la suma de las anomalias ha destacado mas de la media
        mag = np.sum(anomaly[a:b+1]) # Magnitud de la anomalia
        basic_event = (mag, max_interval, vocabulary_entry[0], anomaly) # Esto es una tupla, es como una lista pero no podemos editar sus elementos
        return basic_event

    # Devuelve en formato float un numero que indica como sobresalen o decaen las menciones asociadas a esa palabra en el time_slice dado respecto a la media de esa palabra en el corpus
    def mention_anomaly(self, time_slice, observation, total_mention_freq):
        # compute the expected frequency of the given word at this time-slice
        expectation = float(self.corpus.tweet_count[time_slice]) * (float(total_mention_freq)/(float(self.corpus.size)))

        # return the difference between the observed frequency and the expected frequency
        return observation - expectation

    def get_frequency_subsequence(self, vocabulary_entry):
        # vocabulary_entry[1] es el puesto en menciones de cada palabra del diccionario, es decir, 0, 1, 2...
        frequency = self.corpus.global_freq[vocabulary_entry[1], :].toarray() # Aqui tenemos un array con otro array dentro
        frequency = frequency[0, :] # Ahora tenemos un unico array, que es la columna de la matriz que corresponde a esa palabra del vocabulario, y cada fila sera un time_slice
        total_freq = np.sum(frequency) # Sumamos para saber la frecuencia de esa palabra en total en todo el corpus

        # compute the time-series that describes the evolution of mention-anomaly
        anomaly = [] # Aqui tendremos un array cuyo indice seran los time-slices y cuyos valores seran un float que indica lo que sobresale o decae la frecuencia asociada a dicha palabra respecto de lo esperado en ese time_slice
        # i es el time_slice de cada vuelta
        for i in range(0, self.corpus.time_slice_count):
            anomaly.append(self.frequency_anomaly(i, frequency[i], total_freq))
        max_ending_here = max_so_far = 0
        a = b = a_ending_here = 0
        # Cuando acabe este bucle for, a y b representaran el intervalo en el que la suma de las anomalias ha destacado mas de la media
        for idx, ano in enumerate(anomaly):
            max_ending_here = max(0, max_ending_here + ano)
            if max_ending_here == 0:
                # a new bigger sum may start from here
                a_ending_here = idx
            if max_ending_here > max_so_far:
                # the new sum from a_ending_here to idx is bigger
                a = a_ending_here+1
                max_so_far = max_ending_here
                b = idx

        # return the event description
        max_interval = (a, b) # Tupla: intervalo en el que la suma de las anomalias ha destacado mas de la media
        mag = np.sum(anomaly[a:b+1]) # Magnitud de la anomalia
        basic_event = (mag, max_interval, vocabulary_entry[0], anomaly) # Esto es una tupla, es como una lista pero no podemos editar sus elementos
        return basic_event

    # Devuelve en formato float un numero que indica como sobresalen o decaen la frecuencia de esa palabra en el time_slice dado respecto a la media de esa palabra en el corpus
    def frequency_anomaly(self, time_slice, observation, total_freq):
        # compute the expected frequency of the given word at this time-slice
        expectation = float(self.corpus.tweet_count[time_slice]) * (float(total_freq)/(float(self.corpus.size)))

        # return the difference between the observed frequency and the expected frequency
        return observation - expectation

    def get_user_subsequence(self, vocabulary_entry):
        # vocabulary_entry[1] es el puesto en menciones de cada palabra del diccionario, es decir, 0, 1, 2...
        user_freq = self.corpus.user_freq[vocabulary_entry[1], :].toarray() # Aqui tenemos un array con otro array dentro
        user_freq = user_freq[0, :] # Ahora tenemos un unico array, que es la columna de la matriz que corresponde a esa palabra del vocabulario, y cada fila sera un time_slice
        total_user_freq = np.sum(user_freq) # Sumamos para saber cuantos usuarios estaban hablando de esa palabra en total en todo el corpus

        # compute the time-series that describes the evolution of mention-anomaly
        anomaly = [] # Aqui tendremos un array cuyo indice seran los time-slices y cuyos valores seran un float que indica lo que sobresale o decaen las menciones asociadas a dicha palabra respecto de lo esperado en ese time_slice
        # i es el time_slice de cada vuelta
        for i in range(0, self.corpus.time_slice_count):
            # mention_freq[i] es cuantas menciones tiene la palabra en ese time_slice, y es la anomalia observada de esa palabra
            anomaly.append(self.user_anomaly(i, user_freq[i], total_user_freq))
        max_ending_here = max_so_far = 0
        a = b = a_ending_here = 0
        # Cuando acabe este bucle for, a y b representaran el intervalo en el que la suma de las anomalias ha destacado mas de la media
        for idx, ano in enumerate(anomaly):
            max_ending_here = max(0, max_ending_here + ano)
            if max_ending_here == 0:
                # a new bigger sum may start from here
                a_ending_here = idx
            if max_ending_here > max_so_far:
                # the new sum from a_ending_here to idx is bigger
                a = a_ending_here+1
                max_so_far = max_ending_here
                b = idx

        # return the event description
        max_interval = (a, b) # Intervalo en el que la suma de las anomalias ha destacado mas de la media
        mag = np.sum(anomaly[a:b+1]) # Magnitud de la anomalia
        basic_event = (mag, max_interval, vocabulary_entry[0], anomaly) # Esto es una tupla, es como una lista pero no podemos editar sus elementos
        return basic_event

    # Devuelve en formato float un numero que indica como sobresalen o decaen los usuarios que hablan sobre esa palabra en el time_slice dado respecto a la media de esa palabra en el corpus
    def user_anomaly(self, time_slice, observation, total_user_freq):
        # compute the expected frequency of the given word at this time-slice
        expectation = float(self.corpus.tweet_count[time_slice]) * (float(total_user_freq)/(float(self.corpus.size)))

        # return the difference between the observed frequency and the expected frequency
        return observation - expectation

    def phase2(self, basic_events):
        print('Phase 2...')

        # sort the events detected during phase 1 according to their magnitude of impact
        basic_events.sort(key=lambda tup: tup[0][0], reverse=True)

        # create the event graph (directed) and the redundancy graph (undirected)
        self.event_graph = nx.DiGraph(name='Event graph')
        self.redundancy_graph = nx.Graph(name='Redundancy graph')
        i = 0
        unique_events = 0
        refined_events = []

        # phase 2 goes on until the top k (distinct) events have been identified
        while unique_events < self.k and i < len(basic_events):
            basic_event = basic_events[i]
            main_word = basic_event[2]
            candidate_words = self.corpus.cooccurring_words(basic_event, self.p) # Devuelve una lista con p (10) palabras como maximo
            main_word_freq = self.corpus.global_freq[self.corpus.vocabulary[main_word], :].toarray()
            main_word_freq = main_word_freq[0, :]
            related_words = []

            # identify candidate words based on co-occurrence
            if candidate_words is not None:
                for candidate_word in candidate_words:
                    candidate_word_freq = self.corpus.global_freq[self.corpus.vocabulary[candidate_word], :].toarray()
                    candidate_word_freq = candidate_word_freq[0, :]

                    # compute correlation and filter according to theta
                    weight = (st.erdem_correlation(main_word_freq, candidate_word_freq) + 1) / 2
                    if weight >= self.theta:
                        related_words.append((candidate_word, weight))

                if len(related_words) > 1:
                    refined_event = (basic_event[0], basic_event[1], main_word, related_words, basic_event[3])
                    # check if this event is distinct from those already stored in the event graph
                    if self.update_graphs(refined_event):
                        refined_events.append(refined_event)
                        unique_events += 1
            i += 1
        # merge redundant events and save the result
        self.events = self.merge_redundant_events(refined_events)

    def update_graphs(self, event):
        redundant = False
        main_word = event[2]
        # check whether 'event' is redundant with another event already stored in the event graph or not
        if self.event_graph.has_node(main_word):
            for related_word, weight in event[3]:
                if self.event_graph.has_edge(main_word, related_word):
                    interval_0 = self.event_graph.node[related_word]['interval']
                    interval_1 = event[1]
                    if st.overlap_coefficient(interval_0, interval_1) > self.sigma:
                        self.redundancy_graph.add_node(main_word, description=event)
                        self.redundancy_graph.add_node(related_word, description=self.get_event(related_word))
                        self.redundancy_graph.add_edge(main_word, related_word)
                        redundant = True
                        break
        if not redundant:
            self.event_graph.add_node(event[2], interval=event[1], mag=event[0][0], main_term=True)
            for related_word, weight in event[3]:
                self.event_graph.add_edge(related_word, event[2], weight=weight)
        return not redundant

    def get_event(self, main_term):
        if self.event_graph.has_node(main_term):
            event_node = self.event_graph.node[main_term]
            if event_node['main_term']:
                related_words = []
                for node in self.event_graph.predecessors(main_term):
                    related_words.append((node, self.event_graph.get_edge_data(node, main_term)['weight']))
                return event_node['mag'], event_node['interval'], main_term, related_words

    def merge_redundant_events(self, events):
        # compute the connected components in the redundancy graph
        components = []
        for c in nx.connected_components(self.redundancy_graph):
            components.append(c)
        final_events = []

        # merge redundant events
        for event in events:
            main_word = event[2]
            main_term = main_word
            descriptions = []
            for component in components:
                if main_word in component:
                    main_term = ', '.join(component)
                    for node in component:
                        descriptions.append(self.redundancy_graph.node[node]['description'])
                    break
            if len(descriptions) == 0:
                related_words = event[3]
            else:
                related_words = self.merge_related_words(main_term, descriptions)
            related_words.sort(key=lambda tup: tup[1], reverse=True)
            final_event = (event[0], event[1], main_term, related_words, event[4])
            final_events.append(final_event)
        return final_events

    def merge_related_words(self, main_term, descriptions):
        all_related_words = []
        for desc in descriptions:
            all_related_words.extend(desc[3])
        all_related_words.sort(key=lambda tup: tup[1], reverse=True)
        merged_related_words = []
        for word, weight in all_related_words:
            if word not in main_term and dict(merged_related_words).get(word) is None:
                if len(merged_related_words) == self.p:
                    break
                merged_related_words.append((word, weight))
        return merged_related_words

    def print_event(self, event):
        related_words = []
        for related_word, weight in event[3]:
            related_words.append(related_word+'('+str("{0:.2f}".format(weight))+')')
        print('   %s - %s: %s (%s)' % (str(self.corpus.to_date(event[1][0])),
                                       str(self.corpus.to_date(event[1][1])),
                                       event[2],
                                       ', '.join(related_words)))

    def print_events(self):
        print('   Top %d events:' % len(self.events))
        for event in self.events:
            self.print_event(event)

    def save_event(self, event, event_id, output_file):
        saving_data = {}
        saving_data['id'] = event_id
        impact_json = {
            'total': float("{0:.2f}".format(event[0][0])),
            'mention': float("{0:.2f}".format(event[0][1])),
            'user': float("{0:.2f}".format(event[0][2]))
        } # Formateamos los impactos a un float de dos decimales
        saving_data['impact'] = impact_json
        saving_data['main_words'] = event[2].split(', ')
        saving_data['related_words'] = []
        for word, weight in event[3]:
            word_json = {
                'word': word,
                'weight': float("{0:.2f}".format(weight))
            } 
            saving_data['related_words'].append(word_json)
        duration_json = {
            'from': str(self.corpus.to_date(event[1][0])),
            'to': str(self.corpus.to_date(event[1][1]))
        }
        saving_data['duration'] = duration_json
        anomaly_json = {
            'total': event[4][0],
            'mention': event[4][1],
            'user': event[4][2]
        }
        saving_data['anomaly'] = anomaly_json
        
        saving_json = json.dumps(saving_data, ensure_ascii=False)
        with open(output_file, 'a') as f:
            f.write(saving_json)
            f.write('\n')

    def save_events(self, output_file):
        if os.path.exists(output_file):
            os.remove(output_file)

        for idx, event in enumerate(self.events):
            self.save_event(event, idx+1, output_file)

    def save_tweet(self, tweet, tweet_id, coordinate, event, event_id, output_file):
        saving_tweet = {}
        main_words = event[2].split(', ')
        words = self.corpus.tokenize(tweet)

        for main_word in main_words:
            if main_word in words:
                for related_word, weight in event[3]:
                    if related_word in words:
                        saving_tweet['eventId'] = event_id
                        saving_tweet['tweetId'] = tweet_id
                        saving_tweet['text'] = tweet
                        if(coordinate != 'null'):
                            points = coordinate.replace('[','').replace(']','').split(",")
                            saving_tweet['lat'] = float(points[1])
                            saving_tweet['lon'] = float(points[0])
                        saving_json = json.dumps(saving_tweet, ensure_ascii=False)
                        with open(output_file, 'a') as f:
                            f.write(saving_json)
                            f.write('\n')
                        break
                break

    def save_tweets(self, output_file):
        if os.path.exists(output_file):
            os.remove(output_file)

        saving_tweets = {}
        for idx, event in enumerate(self.events):
            files_path = self.get_files_interval(event)
            for file in files_path:
                with open(file, 'r') as input_file:
                    csv_reader = csv.reader(input_file, delimiter=self.separator)
                    header = next(csv_reader)
                    text_column_index = header.index('text')
                    coordinates_column_index = header.index('coordinates')
                    tweet_id_column_index = header.index('tweetId')
                    for line in csv_reader:
                        tweet = line[text_column_index]
                        tweet_id = line[tweet_id_column_index]
                        coordinate = line[coordinates_column_index]
                        self.save_tweet(tweet, tweet_id, coordinate, event, idx+1, output_file)

    def get_files_interval(self, event):
        files_name = [f.split('.csv')[0] for f in os.listdir(self.corpus.source_directory_path) if os.path.isfile(os.path.join(self.corpus.source_directory_path, f))]
        files_name = sorted(files_name, key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d-%H-%M-%S")) # Sigue siendo lista de strings
        date_from = self.corpus.to_date(event[1][0]) # Objeto datetime
        date_to = self.corpus.to_date(event[1][1])
        if date_from == date_to:
            date_to += datetime.timedelta(minutes=30)

        result = [] # Lista de fechas en formato string
        for file in files_name:
            file_datetime = datetime.datetime.strptime(file,"%Y-%m-%d-%H-%M-%S")
            if file_datetime > date_from and file_datetime < date_to:
                result.append(file)

        first_idx = files_name.index(result[0])
        last_idx = files_name.index(result[-1])
        if first_idx != 0:
            result.append(files_name[first_idx-1])
        if last_idx != len(files_name)-1:
            result.append(files_name[last_idx+1])
        result = sorted(result, key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d-%H-%M-%S"))

        return [os.path.join(self.corpus.source_directory_path, f,)+'.csv' for f in result]