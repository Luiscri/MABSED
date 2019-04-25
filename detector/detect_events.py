# coding: utf-8

import sys
sys.dont_write_bytecode = True
sys.path.insert(0, './mabsed/')

# std
import timeit
import argparse

# mabsed
from corpus import Corpus
from mabsed import MABSED

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Perform mention-anomaly-based streaming event detection (MABSED)')
    p.add_argument('i', metavar='input', type=str, help='Input directory containing CSV files')
    p.add_argument('k', metavar='top_k_events', type=int, help='Number of top events to detect')
    p.add_argument('--sw', metavar='stopwords', type=str, help='Stop-word list', default='./data/stopwords/stopwords-es.txt')
    p.add_argument('--sep', metavar='separator', type=str, help='CSV separator', default='\t')
    p.add_argument('--maf', metavar='min_absolute_frequency', type=int, help='Minimum absolute word frequency, default to 10', default=10)
    # Valor maximo relativo de la frecuencia que puede tener una palabra respecto del total de TWEETS (no de palabras)
    p.add_argument('--mrf', metavar='max_relative_frequency', type=float, help='Maximum relative word frequency, default to 0.4', default=0.4)
    p.add_argument('--tsl', metavar='time_slice_length', type=int, help='Time-slice length, default to 30 (minutes)', default=30) # Dividimos el corpus en ventanas de 30 minutos
    p.add_argument('--p', metavar='p', type=int, help='Number of candidate words per event, default to 10', default=10) # Igual cambiar esto para que salgan menos
    p.add_argument('--t', metavar='theta', type=float, help='Theta, default to 0.6', default=0.6)
    p.add_argument('--s', metavar='sigma', type=float, help='Sigma, default to 0.6', default=0.6)
    args = p.parse_args()
    print('Parameters:')
    print('   Corpus: %s\n   k: %d\n   Stop-words: %s\n   Min. abs. word frequency: %d\n   Max. rel. word frequency: %f' %
          (args.i, args.k, args.sw, args.maf, args.mrf))
    print('   p: %d\n   theta: %f\n   sigma: %f' % (args.p, args.t, args.s))

    print('Loading corpus...')
    start_time = timeit.default_timer()
    my_corpus = Corpus(source_directory_path=args.i, stopwords_file_path=args.sw, min_absolute_freq=args.maf, max_relative_freq=args.mrf, separator=args.sep)
    elapsed = timeit.default_timer() - start_time
    print('Corpus loaded in %f seconds.' % elapsed)

    time_slice_length = args.tsl
    print('Partitioning tweets into %d-minute time-slices...' % time_slice_length)
    start_time = timeit.default_timer()
    my_corpus.discretize(time_slice_length)
    elapsed = timeit.default_timer() - start_time
    print('Partitioning done in %f seconds.' % elapsed)

    print('Running MABSED...')
    k = args.k # Numero de eventos a detectar
    p = args.p # Numero maximo de palabras que describen cada evento (10 por defecto)
    theta = args.t # Umbral de peso por encima del cual una palabra se considera relevante (0.6 por defecto)
    sigma = args.s # Sensibilidad a los eventos duplicados (si es alta aumenta numero de eventos duplicados y la precision)
    start_time = timeit.default_timer()
    mabsed = MABSED(my_corpus, args.sep)
    mabsed.run(k=k, p=p, theta=theta, sigma=sigma)
    mabsed.print_events()
    elapsed = timeit.default_timer() - start_time
    print('Event detection performed in %f seconds.' % elapsed)

    # Guardamos los resultados
    eventsOutput = './detected_events.txt'
    tweetsOutput = './detected_tweets.txt'
    mabsed.save_events(eventsOutput)
    mabsed.save_tweets(tweetsOutput)
    print('Events data saved in:')
    print('   '+eventsOutput)
    print('   '+tweetsOutput)
