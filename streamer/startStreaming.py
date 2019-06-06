import sys
sys.dont_write_bytecode = True

# tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API

# saving
import datetime
import os
import json
import csv

# Twitter credentials
from credentials import consumer_key, consumer_secret, access_token, access_token_secret

class FileListener(StreamListener):
    # Constructor
    def __init__(self, output_directory):
        self.output_directory = output_directory # Path donde se guardaran los tweets
        self.filename = None # Nombre del fichero en el que se estan guardando los tweets en este momento
        self.received_tweets = []

    # Metodo que se ejecuta cada vez que recibimos un tweet
    def on_data(self, data):
        # Extraemos los campos que nos interesan 
        saving_tweet = {}
        data_json = json.loads(data) # Pasamos data a JSON
        saving_tweet['tweetId'] = data_json['id']
        saving_tweet['authorId'] = data_json['user']['id']
        if 'coordinates' in data_json:
            try:
                if 'coordinates' in data_json['coordinates']:
                    saving_tweet['coordinates'] = data_json['coordinates']['coordinates']
            except:
                saving_tweet['coordinates'] = 'null'
                pass
        else:
            saving_tweet['coordinates'] = 'null'
        date_object = datetime.datetime.strptime(data_json['created_at'], '%a %b %d %H:%M:%S +%f %Y') # Pasamos la fecha de String a Date
        date_object += datetime.timedelta(hours=2) # La hora que devuelve Twitter esta atrasada 1 hora o 2 (depende)
        saving_tweet['date'] = date_object.strftime('%Y-%m-%d %H:%M:%S') # Le damos el formato que queramos a la fecha
        t = str.maketrans("\n\t\r", "   ")
        if 'extended_tweet' in data_json:
            saving_tweet['text'] = data_json['extended_tweet']['full_text'].translate(t)
        else:
            saving_tweet['text'] = data_json['text'].translate(t)

        # Comprobamos si se ha cambiado de franja de media hora
        if date_object.minute >= 0 and date_object.minute < 30:
            filename = date_object.replace(minute=0).strftime('%Y-%m-%d %H:%M:00')
        else:
            filename = date_object.replace(minute=30).strftime('%Y-%m-%d %H:%M:00')
        if self.filename == None:
            self.filename = filename

        # Si se ha cambiado de franja guardamos los tweets
        if filename != self.filename:
            self.start_file(filename)

        self.received_tweets.append(saving_tweet)         
   
    # Metodo para crear el directorio donde se guardaran los tweets y decidir el nombre del fichero
    def start_file(self, filename):
        # Creamos el directorio en el que se guardan los tweets si no existe ya
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        # Guardamos los tweets en un fichero CSV
        with open(os.path.join(self.output_directory, '%s.csv' % self.filename), 'a') as f:
            fieldnames = ['tweetId', 'authorId', 'coordinates', 'date', 'text']
            writer = csv.DictWriter(f, fieldnames=fieldnames,  delimiter='\t')
            writer.writeheader()

            for tweet in self.received_tweets:
                writer.writerow(tweet)

        self.filename = filename
        self.received_tweets = []

    # Metodo que se ejecuta cuando se produce un error para desconectar el Stream y no ser sancionados
    def on_error(self, status_code):
        if status_code == 420:
            exit()
            return False

if __name__ == '__main__':
    output_directory = '../orchestrator/data/streaming'

    locations = [-3.9787006307, 40.2683111652, -3.3693867643, 40.5708246083] # Madrid y alrededores http://boundingbox.klokantech.com/
    languages = ['es'] # Español

    #Creo el Listener con el directorio donde se guardaran los tweets
    listener = FileListener(output_directory)
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = API(auth)

    stream = Stream(auth=auth, listener=listener)
    # Si ponemos async=True hace el stream en ota hebra para no bloquear la actual
    stream.filter(locations=locations, languages=languages)

