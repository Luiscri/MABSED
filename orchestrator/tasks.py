import sys
sys.dont_write_bytecode = True

# orchestration
import luigi
from luigi.contrib.esindex import CopyToIndex
import datetime

# filter
import os
import csv
import json
from filter.filter import filter_spam

# lemmatizer
from lemmatizer.lemmatizer import lemmatize
from cube.api import Cube

# detection
sys.path.insert(0, './detector/')
from detect_events import main as detect_events

lemmatizer = Cube(verbose=True)
lemmatizer.load("es", tokenization=False, parsing=False)

class Streamer(luigi.ExternalTask):
    time_slice = luigi.parameter.DateMinuteParameter(interval=30)

    def output(self):
        fname = '../data/streaming/{}.csv'.format(self.time_slice)
        # print('Requires: {}'.format(fname))
        return luigi.LocalTarget(fname)


class Preprocess(luigi.Task):
    time_slice = luigi.parameter.DateMinuteParameter(interval=30, default=datetime.datetime.today())

    def requires(self):
        return Streamer(time_slice=self.time_slice)

    def run(self):
        with self.input().open('r') as infile:
            reader = csv.DictReader(infile, delimiter='\t')
            tweets = list(reader)
        filtered_tweets, spam = filter_spam(tweets, 0.5)

        spam_directory = '../data/detected_spam/'
        if not os.path.exists(spam_directory):
            os.makedirs(spam_directory)

        with open(spam_directory+'{}.csv'.format(self.time_slice), 'a') as spam_file:
            csv_columns = ['detected', 'from']
            writer = csv.DictWriter(spam_file, fieldnames=csv_columns, delimiter='\t')
            writer.writeheader()
            for tweet in spam:
                writer.writerow(tweet)

        lemmatized_tweets = lemmatize(filtered_tweets, lemmatizer)
        
        with self.output().open('w') as outfile:
            csv_columns = ['tweetId', 'authorId', 'coordinates', 'date', 'text', 'lemmatizedText']
            writer = csv.DictWriter(outfile, fieldnames=csv_columns, delimiter='\t')
            writer.writeheader()
            for tweet in lemmatized_tweets:
                writer.writerow(tweet)        

    def output(self):
        return luigi.LocalTarget('../data/preprocessed/{}.csv'.format(self.time_slice))        

class DetectEvents(luigi.Task):
    final = luigi.parameter.DateMinuteParameter(interval=30, default=datetime.datetime.today())

    def requires(self):
        comienzo = self.final - datetime.timedelta(days=1)
        while comienzo < self.final:
            comienzo += datetime.timedelta(minutes=30) 
            yield Preprocess(time_slice=comienzo)

    def run(self):
        input_files = [f.path for f in self.input()]
        output_files = [f.path for f in self.output()]
        detect_events(input_files=input_files, output_files=output_files,
                      stopwords='./detector/data/stopwords/stopwords-es.txt',
                      corpus_directory='./detector/data/corpus/')

    def output(self):
        events_filename = '../data/results/detected_events{}.txt'.format(self.final.strftime("%Y-%m-%d %H:%M:%S"))
        tweets_filename = '../data/results/detected_tweets{}.txt'.format(self.final.strftime("%Y-%m-%d %H:%M:%S"))
        return [luigi.LocalTarget(events_filename), luigi.LocalTarget(tweets_filename)]

class Mediator(luigi.Task):
    final = luigi.parameter.DateMinuteParameter(interval=30, default=datetime.datetime.today())
    idx = luigi.parameter.IntParameter()

    def requires(self):
        return DetectEvents(final=self.final)

    def output(self):
        return self.input()[self.idx]

class SearchAndStore(CopyToIndex):
    final = luigi.parameter.DateMinuteParameter(interval=30, default=datetime.datetime.today())

    index = luigi.parameter.Parameter()
    doc_type = luigi.parameter.Parameter()
    idx = luigi.parameter.Parameter()

    host = 'elasticsearch'
    #port = '9200'
    purge_existing_index = True

    def requires(self):
        return Mediator(final=self.final, idx=self.idx)

class Main(luigi.Task):
    final = luigi.parameter.DateMinuteParameter(interval=30, default=datetime.datetime.today())

    def requires(self):
        indices = ['mabsed-events', 'mabsed-tweets']
        doc_types = ['event', 'tweet']
        for idx in range(0,2):
            yield SearchAndStore(final=self.final, index=indices[idx], doc_type=doc_types[idx], idx=idx)