# coding: utf-8
import sys
sys.dont_write_bytecode = True

# std
import timeit
import datetime

# mabsed
from mabsed.corpus import Corpus
from mabsed.mabsed import MABSED

def main(input_files, output_files, stopwords, corpus_directory, k=3, separator='\t', min_absolute_freq=10,
         max_relative_freq=0.4, time_slice_length=30, p=10, theta=0.6, sigma=0.6):
    script_timer = timeit.default_timer()
    corpus = generate_corpus(input_files, stopwords, corpus_directory, min_absolute_freq,
             max_relative_freq, separator, time_slice_length)
    detect_events(script_timer, corpus, corpus_directory, k, p, theta, sigma, output_files)

def generate_corpus(input_files, stopwords, corpus_directory, min_absolute_freq, max_relative_freq,
                    separator, time_slice_length):
    print('Corpus Parameters:')
    print(('   Number of input files: %d\n   Stop-words: %s\n   Min. abs. word frequency: %d\n' +
           '   Max. rel. word frequency: %f\n   Time slice length: %d minutes') %
          (len(input_files), stopwords, min_absolute_freq, max_relative_freq, time_slice_length))

    print('Loading corpus...') 
    start_time = timeit.default_timer()
    corpus = Corpus(input_files=input_files, stopwords=stopwords,
                    corpus_directory=corpus_directory, min_absolute_freq=min_absolute_freq,
                    max_relative_freq=max_relative_freq, separator=separator)
    elapsed = timeit.default_timer() - start_time
    print('Corpus loaded in %f seconds.' % elapsed)

    print('Creating impact matrices...')
    start_time = timeit.default_timer()
    corpus.compute_matrices(time_slice_length)
    elapsed = timeit.default_timer() - start_time
    print('Matrices created in %f seconds.' % elapsed)
    return corpus

# k = Numero de eventos a detectar
# p = Numero maximo de palabras que describen cada evento (10 por defecto)
# theta = Umbral de peso por encima del cual una palabra se considera relevante (0.6 por defecto)
# sigma = Sensibilidad a los eventos duplicados (si es alta disminuye el numero de eventos duplicados y la precision)
def detect_events(script_timer, corpus, corpus_directory, k, p, theta, sigma, output_files):
    print('Detection Parameters:')
    print('   Number of events: %d\n   Number of related words: %d\n   Theta: %f\n   Sigma: %f' % 
          (k, p, theta, sigma))

    print('Running MABSED...')
    start_time = timeit.default_timer()
    mabsed = MABSED(corpus, corpus_directory)
    mabsed.run(k=k, p=p, theta=theta, sigma=sigma)
    mabsed.print_events()
    elapsed = timeit.default_timer() - start_time
    print('Event detection performed in %f seconds.' % elapsed)

    # Guardamos los resultados
    mabsed.save_events(output_files[0])
    mabsed.save_tweets(output_files[1])
    print('Detection results saved in:')
    print('   '+output_files[0])
    print('   '+output_files[1])

    elapsed = timeit.default_timer() - script_timer
    print('Total script time: %f seconds.' % elapsed)
    # mabsed.print_graphs()