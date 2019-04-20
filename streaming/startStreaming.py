from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API
import logging, datetime, time, os, json, csv
from credentials import consumer_key, consumer_secret, access_token, access_token_secret

class FileListener(StreamListener):
    # Constructor
    def __init__(self, path, restart_time):
        self.path = path # Path donde se guardaran los tweets
        self.filename = None # Nombre del fichero en el que se estan guardando los tweets en este momento
        self.restart_time = restart_time
        self.file_start_time = datetime.datetime.now()

    # Metodo que se ejecuta cada vez que recibimos un tweet
    def on_data(self, data):    
        just_created = False # Variable para saber si acabamos de crear el fichero CSV 
        '''
        Creo un fichero nuevo si:
            - No existe fichero anterior (inicializar)
            - Si se ha superado el tiempo para restart
        '''
        if self.filename == None or datetime.datetime.now() - datetime.timedelta(seconds=self.restart_time) > self.file_start_time:
            self.startFile()
            just_created = True
        
        # Extraemos los campos que nos interesan 
        savingTweet = {}
        dataJson = json.loads(data) # Pasamos data a JSON
        savingTweet['tweetId'] = dataJson['id']
        savingTweet['authorId'] = dataJson['user']['id']
        if 'coordinates' in dataJson:
            try:
                if 'coordinates' in dataJson['coordinates']:
                    savingTweet['coordinates'] = dataJson['coordinates']['coordinates']
            except:
                savingTweet['coordinates'] = 'null'
                pass
        else:
            savingTweet['coordinates'] = 'null'
        stringToDate = datetime.datetime.strptime(dataJson['created_at'], '%a %b %d %H:%M:%S +%f %Y') # Pasamos la fecha de String a Date
        savingTweet['date'] = stringToDate.strftime('%Y-%m-%d %H:%M:%S') # Le damos el formato que queramos a la fecha
        t = str.maketrans("\n\t\r", "   ")
        if 'extended_tweet' in dataJson:
            savingTweet['text'] = dataJson['extended_tweet']['full_text'].translate(t)
        else:
            savingTweet['text'] = dataJson['text'].translate(t)

        # Escribimos los datos en el fichero CSV
        with open(self.filename, 'a') as f:
            fieldnames = ['tweetId', 'authorId', 'coordinates', 'date', 'text']
            writer = csv.DictWriter(f, fieldnames=fieldnames,  delimiter='\t')

            if just_created:
                writer.writeheader()

            writer.writerow({
                'tweetId': savingTweet['tweetId'],
                'authorId': savingTweet['authorId'],
                'coordinates': savingTweet['coordinates'],
                'date': savingTweet['date'],
                'text': savingTweet['text']
            })

        ''' Guardar en formato JSON
        with open(self.filename, 'a') as f:
            json.dump(savingTweet, f, sort_keys=True, indent=4)
            f.write('\n')
        '''            

    # Metodo que se ejecuta cuando se produce un error para desconectar el Stream y no ser sancionados
    def on_error(self, status_code):
        logger.error(status_code)
        if status_code == 420:
            exit()
            return False
   
    # Metodo para crear el directorio donde se guardaran los tweets y decidir el nombre del fichero
    def startFile(self):
        # Creo el directorio en el que se guardan los tweets si no existe
        try:
            os.makedirs(self.path)
            logger.info('Created %s' % self.path)
        except:
            pass

        # Decidimos el nombre del fichero donde se guardaran los tweets
        date_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.filename = os.path.join(self.path, '%s.csv' % date_time) # Cambiar a .json si lo queremos en ese formato
        self.file_start_time = datetime.datetime.now()
        logger.info('Starting new file: %s' % self.filename)

if __name__ == '__main__':
    output_directory = './data/tweets/streaming'
    if not os.path.isdir('log'):
        os.makedirs('log')
    log_filename = 'log/logEs'

    logger = logging.getLogger('tweepy_streaming')
    handler = logging.FileHandler(log_filename, mode='a')
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    locations = [-3.9787006307, 40.2683111652, -3.3693867643, 40.5708246083] # Madrid y alrededores http://boundingbox.klokantech.com/
    languages = ['es'] # Español
    if not os.path.isdir('pid'):
        os.makedirs('pid')
    pid_file = 'pid/pidSpanish'
    file = open(pid_file, 'w')
    file.write(str(os.getpid()))
    file.close()

    #Creo el Listener:
    # - Con el directorio donde colocar los tweets
    # - Y con el tiempo de crear un fichero nuevo
    listener = FileListener(output_directory, 900) # Creamos un fichero cada 900 segundos (15 minutos)
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    logger.warning("Connecting Process Spanish")
    api = API(auth)
    logger.warning(api.me().name)

    stream = Stream(auth=auth, listener=listener)
    # Si ponemos async=True hace el stream en ota hebra para no bloquear la actual
    stream.filter(locations=locations, languages=languages)

