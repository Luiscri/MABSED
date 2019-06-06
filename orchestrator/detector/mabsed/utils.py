# coding: utf-8

def load_stopwords(file_path):
    stopwords = set()
    with open(file_path, 'r') as input_file:
        for line in input_file.readlines():
            stopwords.add(line.strip('\n'))
    return stopwords